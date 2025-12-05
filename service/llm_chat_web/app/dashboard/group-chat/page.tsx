"use client"

import { useState, useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import { Plus, MessageSquare, TrendingUp, Flame, Clock, Star, Filter, Loader2, Heart, MessageCircle, Share2 } from "lucide-react"
import { groupChatApi, type Comment } from "@/utils/api/group-chat-client"
import GroupChat3DTree from "./visualizer-3d"
import { EmptyState } from "./components/empty-state"
import { LoadingState } from "./components/loading-state"
import { DiscussionCard } from "./components/discussion-card"

export default function GroupChatPage() {
    const router = useRouter()
    const [discussions, setDiscussions] = useState<Comment[]>([])
    const [newDiscussionTitle, setNewDiscussionTitle] = useState("")
    const [newDiscussionContent, setNewDiscussionContent] = useState("")
    const [loading, setLoading] = useState(true)
    const [posting, setPosting] = useState(false)
    const [isNewDiscussionOpen, setIsNewDiscussionOpen] = useState(false)
    const [activeTab, setActiveTab] = useState("all")

    useEffect(() => {
        const fetchDiscussions = async () => {
            try {
                setLoading(true)
                const data = await groupChatApi.getDiscussions()

                if (data.success) {
                    const mappedDiscussions = data.discussions.map((disc) => ({
                        id: disc.id || Date.now(),
                        _id: disc._id,
                        author: disc.author,
                        avatar: disc.avatar,
                        time: disc.time,
                        content: disc.content,
                        title: disc.title,
                        upvotes: disc.upvotes,
                        downvotes: disc.downvotes,
                        userVote: disc.userVote,
                        replies: disc.replies || []
                    }))
                    setDiscussions(mappedDiscussions)
                }
            } catch (error) {
                console.error('Error fetching discussions:', error)
            } finally {
                setLoading(false)
            }
        }

        fetchDiscussions()
    }, [])

    const handleCreateNewDiscussion = async () => {
        if (newDiscussionContent.trim() && !posting) {
            setPosting(true)
            try {
                const data = await groupChatApi.createDiscussion({
                    author: 'You',
                    avatar: '/avatars/shadcn.jpg',
                    content: newDiscussionContent,
                    title: newDiscussionTitle.trim() || undefined
                })

                if (data.success) {
                    const newDiscussion: Comment = {
                        id: data.discussion.id || Date.now(),
                        _id: data.discussion._id,
                        author: "You",
                        avatar: "/avatars/shadcn.jpg",
                        time: "Just now",
                        content: newDiscussionContent,
                        title: data.discussion.title,
                        upvotes: 0,
                        downvotes: 0,
                        userVote: null,
                        replies: []
                    }
                    setDiscussions([newDiscussion, ...discussions])
                    setNewDiscussionTitle("")
                    setNewDiscussionContent("")
                    setIsNewDiscussionOpen(false)
                }
            } catch (error) {
                console.error('Error creating discussion:', error)
            } finally {
                setPosting(false)
            }
        }
    }

    const countReplies = (comment: Comment): number => {
        let count = 0
        if (comment.replies && comment.replies.length > 0) {
            for (const reply of comment.replies) {
                count += 1 + countReplies(reply)
            }
        }
        return count
    }

    const navigateToDiscussion = (discussionId: string | number) => {
        router.push(`/dashboard/group-chat/${discussionId}`)
    }

    const trendingDiscussions = useMemo(() => {
        return [...discussions]
            .map(d => ({
                ...d,
                engagement: d.upvotes + d.downvotes + countReplies(d)
            }))
            .sort((a, b) => b.engagement - a.engagement)
            .slice(0, 5)
    }, [discussions])

    const recentDiscussions = useMemo(() => {
        return [...discussions].slice(0, 5)
    }, [discussions])

    const totalReplies = useMemo(() => {
        return discussions.reduce((acc, d) => acc + countReplies(d), 0)
    }, [discussions])

    const filteredDiscussions = useMemo(() => {
        if (activeTab === "trending") {
            return trendingDiscussions
        } else if (activeTab === "recent") {
            return recentDiscussions
        }
        return discussions
    }, [activeTab, discussions, trendingDiscussions, recentDiscussions])

    return (
        <div className="flex flex-1 flex-col h-screen bg-slate-950">
            <header className="sticky top-0 z-10 flex h-16 shrink-0 items-center gap-2 border-b border-slate-800 px-4 bg-slate-950/90 backdrop-blur-xl">
                <SidebarTrigger className="-ml-1 text-slate-400 hover:text-white" />
                <Separator orientation="vertical" className="mr-2 h-4 bg-slate-700" />
                <div className="flex items-center gap-3">
                    <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-violet-500/20 to-purple-600/20 flex items-center justify-center ring-1 ring-violet-500/20">
                        <MessageSquare className="h-4 w-4 text-violet-400" />
                    </div>
                    <div>
                        <h1 className="text-lg font-semibold text-white">
                            Community Discussions
                        </h1>
                        <p className="text-xs text-slate-400">
                            {discussions.length} discussions • {totalReplies} replies
                        </p>
                    </div>
                </div>
                <div className="ml-auto flex items-center gap-2">
                    <Dialog open={isNewDiscussionOpen} onOpenChange={setIsNewDiscussionOpen}>
                        <DialogTrigger asChild>
                            <Button className="bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white border-0">
                                <Plus className="h-4 w-4 mr-2" />
                                New Discussion
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="sm:max-w-[500px] bg-slate-900 border-slate-800">
                            <DialogHeader>
                                <DialogTitle className="text-white">Start a New Discussion</DialogTitle>
                                <DialogDescription className="text-slate-400">
                                    Share your thoughts with the community
                                </DialogDescription>
                            </DialogHeader>
                            <div className="grid gap-4 py-4">
                                <div className="grid gap-2">
                                    <label htmlFor="title" className="text-sm font-medium text-slate-300">
                                        Title (optional)
                                    </label>
                                    <Input
                                        id="title"
                                        placeholder="Give your discussion a title..."
                                        value={newDiscussionTitle}
                                        onChange={(e) => setNewDiscussionTitle(e.target.value)}
                                        className="bg-slate-800 border-slate-700 text-white placeholder:text-slate-500"
                                    />
                                </div>
                                <div className="grid gap-2">
                                    <label htmlFor="content" className="text-sm font-medium text-slate-300">
                                        Content
                                    </label>
                                    <Textarea
                                        id="content"
                                        placeholder="What's on your mind?"
                                        value={newDiscussionContent}
                                        onChange={(e) => setNewDiscussionContent(e.target.value)}
                                        className="min-h-[120px] bg-slate-800 border-slate-700 text-white placeholder:text-slate-500"
                                    />
                                </div>
                            </div>
                            <DialogFooter>
                                <Button variant="outline" onClick={() => setIsNewDiscussionOpen(false)} className="border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white">
                                    Cancel
                                </Button>
                                <Button
                                    onClick={handleCreateNewDiscussion}
                                    disabled={!newDiscussionContent.trim() || posting}
                                    className="bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white"
                                >
                                    {posting ? (
                                        <>
                                            <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                            Creating...
                                        </>
                                    ) : (
                                        'Create Discussion'
                                    )}
                                </Button>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>
                    <GroupChat3DTree discussions={discussions} />
                </div>
            </header>

            <div className="flex-1 flex overflow-hidden">
                <main className="flex-1 flex flex-col min-h-0">
                    <div className="border-b border-slate-800 bg-slate-900/30 px-4 py-3">
                        <Tabs value={activeTab} onValueChange={setActiveTab}>
                            <TabsList className="bg-slate-800/50 border border-slate-700">
                                <TabsTrigger value="all" className="gap-2 data-[state=active]:bg-slate-700 data-[state=active]:text-white text-slate-400">
                                    <Filter className="h-3.5 w-3.5" />
                                    All
                                </TabsTrigger>
                                <TabsTrigger value="trending" className="gap-2 data-[state=active]:bg-amber-600 data-[state=active]:text-white text-slate-400">
                                    <Flame className="h-3.5 w-3.5" />
                                    Trending
                                </TabsTrigger>
                                <TabsTrigger value="recent" className="gap-2 data-[state=active]:bg-emerald-600 data-[state=active]:text-white text-slate-400">
                                    <Clock className="h-3.5 w-3.5" />
                                    Recent
                                </TabsTrigger>
                            </TabsList>
                        </Tabs>
                    </div>

                    <ScrollArea className="flex-1">
                        <div className="max-w-4xl mx-auto p-4">
                            {loading ? (
                                <LoadingState message="Loading discussions..." />
                            ) : filteredDiscussions.length === 0 ? (
                                <EmptyState
                                    icon={MessageSquare}
                                    title="No discussions yet"
                                    description="Be the first to start a conversation! Share your ideas with the community."
                                    actionLabel="Start First Discussion"
                                    onAction={() => setIsNewDiscussionOpen(true)}
                                />
                            ) : (
                                <div className="space-y-3">
                                    {filteredDiscussions.map((discussion) => {
                                        const replyCount = countReplies(discussion)
                                        const totalEngagement = discussion.upvotes + discussion.downvotes + replyCount
                                        const isTrending = totalEngagement > 5

                                        return (
                                            <DiscussionCard
                                                key={discussion.id}
                                                discussion={discussion}
                                                replyCount={replyCount}
                                                isTrending={isTrending}
                                                onClick={() => navigateToDiscussion(discussion._id || discussion.id)}
                                            />
                                        )
                                    })}
                                </div>
                            )}
                        </div>
                    </ScrollArea>
                </main>

                <aside className="hidden xl:flex w-80 flex-col border-l border-slate-800 bg-slate-900/50">
                    <div className="p-4 border-b border-slate-800">
                        <h2 className="font-semibold text-sm flex items-center gap-2 text-white">
                            <Star className="h-4 w-4 text-violet-400" />
                            Community Stats
                        </h2>
                    </div>
                    <ScrollArea className="flex-1">
                        <div className="p-4 space-y-4">
                            <Card className="border-slate-800 bg-slate-800/50">
                                <CardHeader className="pb-3">
                                    <CardTitle className="text-sm font-medium text-white">Overview</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-slate-400">Discussions</span>
                                        <span className="font-semibold text-white">{discussions.length}</span>
                                    </div>
                                    <div className="flex justify-between text-sm">
                                        <span className="text-slate-400">Total Replies</span>
                                        <span className="font-semibold text-white">{totalReplies}</span>
                                    </div>
                                    <div className="flex justify-between text-sm">
                                        <span className="text-slate-400">Active Users</span>
                                        <span className="font-semibold text-white">{new Set(discussions.map(d => d.author)).size}</span>
                                    </div>
                                </CardContent>
                            </Card>

                            {trendingDiscussions.length > 0 && (
                                <Card className="border-slate-800 bg-slate-800/50">
                                    <CardHeader className="pb-3">
                                        <CardTitle className="text-sm font-medium flex items-center gap-2 text-white">
                                            <TrendingUp className="h-4 w-4 text-amber-400" />
                                            Top Discussions
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent className="space-y-3">
                                        {trendingDiscussions.slice(0, 3).map((disc, idx) => (
                                            <div
                                                key={disc.id}
                                                className="flex gap-2 cursor-pointer hover:bg-slate-700/50 p-2 rounded-lg transition-colors"
                                                onClick={() => navigateToDiscussion(disc._id || disc.id)}
                                            >
                                                <span className="text-lg font-bold text-slate-600">#{idx + 1}</span>
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-xs font-medium line-clamp-2 text-slate-300">
                                                        {disc.title || disc.content}
                                                    </p>
                                                    <p className="text-xs text-slate-500 mt-1">
                                                        {(disc as any).engagement} interactions
                                                    </p>
                                                </div>
                                            </div>
                                        ))}
                                    </CardContent>
                                </Card>
                            )}
                        </div>
                    </ScrollArea>
                </aside>
            </div>
        </div>
    )
}

