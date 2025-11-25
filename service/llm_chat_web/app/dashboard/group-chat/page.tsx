"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { Textarea } from "@/components/ui/textarea"
import { Loader2 } from "lucide-react"
import { CommentItem } from "./comment-item"
import { groupChatApi, type Comment } from "@/utils/api/group-chat-client"

export default function GroupChatPage() {
    const [discussions, setDiscussions] = useState<Comment[]>([])
    const [newPost, setNewPost] = useState("")
    const [loading, setLoading] = useState(true)
    const [posting, setPosting] = useState(false)

    // Fetch discussions on mount
    useEffect(() => {
        const fetchDiscussions = async () => {
            try {
                setLoading(true)
                const data = await groupChatApi.getDiscussions()

                if (data.success) {
                    const mappedDiscussions = data.discussions.map((disc) => ({
                        id: parseInt(disc._id || '') || Date.now(),
                        _id: disc._id,
                        author: disc.author,
                        avatar: disc.avatar,
                        time: disc.time,
                        content: disc.content,
                        upvotes: disc.upvotes,
                        downvotes: disc.downvotes,
                        userVote: disc.userVote,
                        replies: disc.replies || []
                    }))
                    setDiscussions(mappedDiscussions)
                } else {
                    console.error('Failed to load discussions')
                }
            } catch (error) {
                console.error('Error fetching discussions:', error)
            } finally {
                setLoading(false)
            }
        }

        fetchDiscussions()
    }, [])

    const handlePost = async () => {
        if (newPost.trim() && !posting) {
            setPosting(true)
            try {
                const data = await groupChatApi.createDiscussion({
                    author: 'You',
                    avatar: '/avatars/shadcn.jpg',
                    content: newPost
                })

                if (data.success) {
                    const newDiscussion: Comment = {
                        id: Date.now(),
                        _id: data.discussion._id,
                        author: "You",
                        avatar: "/avatars/shadcn.jpg",
                        time: "Just now",
                        content: newPost,
                        upvotes: 0,
                        downvotes: 0,
                        userVote: null,
                        replies: []
                    }
                    setDiscussions([newDiscussion, ...discussions])
                    setNewPost("")
                } else {
                    console.error('Failed to create discussion')
                }
            } catch (error) {
                console.error('Error creating discussion:', error)
            } finally {
                setPosting(false)
            }
        }
    }

    const handleReply = async (parentId: number, content: string) => {
        try {
            const parent = discussions.find(d => d.id === parentId)
            if (!parent || !parent._id) return

            const data = await groupChatApi.addReply(parent._id, {
                author: 'You',
                avatar: '/avatars/shadcn.jpg',
                content
            })

            if (data.success) {
                const addReplyToComment = (comments: Comment[]): Comment[] => {
                    return comments.map(comment => {
                        if (comment.id === parentId) {
                            const newReply: Comment = {
                                id: Date.now(),
                                author: "You",
                                avatar: "/avatars/shadcn.jpg",
                                time: "Just now",
                                content: content,
                                upvotes: 0,
                                downvotes: 0,
                                userVote: null,
                            }
                            return {
                                ...comment,
                                replies: [...(comment.replies || []), newReply]
                            }
                        }
                        if (comment.replies) {
                            return {
                                ...comment,
                                replies: addReplyToComment(comment.replies)
                            }
                        }
                        return comment
                    })
                }

                setDiscussions(addReplyToComment(discussions))
            } else {
                console.error('Failed to add reply')
            }
        } catch (error) {
            console.error('Error adding reply:', error)
        }
    }

    const handleDelete = async (commentId: number) => {
        try {
            const comment = discussions.find(d => d.id === commentId)
            if (!comment || !comment._id) return

            const data = await groupChatApi.deleteDiscussion(comment._id)

            if (data.success) {
                const deleteComment = (comments: Comment[]): Comment[] => {
                    return comments.filter(comment => {
                        if (comment.id === commentId) {
                            return false
                        }
                        if (comment.replies) {
                            comment.replies = deleteComment(comment.replies)
                        }
                        return true
                    })
                }

                setDiscussions(deleteComment(discussions))
            } else {
                console.error('Failed to delete comment')
            }
        } catch (error) {
            console.error('Error deleting comment:', error)
        }
    }

    const handleVote = async (commentId: number, voteType: 'up' | 'down') => {
        try {
            const comment = discussions.find(d => d.id === commentId)
            if (!comment || !comment._id) return

            const data = await groupChatApi.voteDiscussion(
                comment._id,
                voteType,
                comment.userVote || null
            )

            if (data.success && data.discussion) {
                const updateVote = (comments: Comment[]): Comment[] => {
                    return comments.map(c => {
                        if (c.id === commentId) {
                            return {
                                ...c,
                                upvotes: data.discussion.upvotes,
                                downvotes: data.discussion.downvotes,
                                userVote: data.discussion.userVote
                            }
                        }
                        if (c.replies) {
                            return {
                                ...c,
                                replies: updateVote(c.replies)
                            }
                        }
                        return c
                    })
                }

                setDiscussions(updateVote(discussions))
            } else {
                console.error('Failed to update vote')
            }
        } catch (error) {
            console.error('Error updating vote:', error)
        }
    }

    return (
        <div className="flex flex-1 flex-col h-screen">
            <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
                <SidebarTrigger className="-ml-1" />
                <Separator orientation="vertical" className="mr-2 h-4" />
                <h1 className="text-lg font-semibold">Community Discussions</h1>
            </header>

            <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4 p-4 overflow-hidden">
                <div className="lg:col-span-2 flex flex-col min-h-0">
                    <Card className="mb-4 p-4 flex-shrink-0">
                        <Textarea
                            placeholder="Start a discussion..."
                            value={newPost}
                            onChange={(e) => setNewPost(e.target.value)}
                            className="min-h-[100px] resize-y"
                            style={{ maxHeight: '300px' }}
                            disabled={posting}
                        />
                        <div className="flex justify-end mt-2">
                            <Button onClick={handlePost} disabled={posting}>
                                {posting ? <><Loader2 className="h-4 w-4 animate-spin mr-2" /> Posting...</> : 'Post'}
                            </Button>
                        </div>
                    </Card>

                    <ScrollArea className="flex-1">
                        {loading ? (
                            <div className="flex items-center justify-center h-full">
                                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                            </div>
                        ) : (
                            <Card className="divide-y">
                                {discussions.map((discussion) => (
                                    <div key={discussion.id} className="break-inside-avoid">
                                        <CommentItem
                                            comment={discussion}
                                            onReply={handleReply}
                                            onDelete={handleDelete}
                                            onVote={handleVote}
                                        />
                                    </div>
                                ))}
                            </Card>
                        )}
                    </ScrollArea>
                </div>

                <div className="hidden lg:block space-y-4">
                    <Card className="p-4">
                        <h3 className="font-semibold mb-3">Trending Topics</h3>
                        <div className="space-y-2">
                            <div className="p-2 rounded-lg hover:bg-accent cursor-pointer transition-colors">
                                <p className="font-medium text-sm">#ReactBestPractices</p>
                                <p className="text-xs text-muted-foreground">1.2k posts</p>
                            </div>
                            <div className="p-2 rounded-lg hover:bg-accent cursor-pointer transition-colors">
                                <p className="font-medium text-sm">#WebDevelopment</p>
                                <p className="text-xs text-muted-foreground">856 posts</p>
                            </div>
                            <div className="p-2 rounded-lg hover:bg-accent cursor-pointer transition-colors">
                                <p className="font-medium text-sm">#NextJS</p>
                                <p className="text-xs text-muted-foreground">643 posts</p>
                            </div>
                        </div>
                    </Card>

                    <Card className="p-4">
                        <h3 className="font-semibold mb-3">Community Rules</h3>
                        <ul className="space-y-2 text-sm text-muted-foreground">
                            <li>1. Be respectful</li>
                            <li>2. No spam or self-promotion</li>
                            <li>3. Stay on topic</li>
                            <li>4. Help others learn</li>
                        </ul>
                    </Card>
                </div>
            </div>
        </div>
    )
}
