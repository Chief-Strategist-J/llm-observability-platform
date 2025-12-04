"use client"

import { useState, useEffect, useMemo } from "react"
import { useRouter, useParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Loader2, ArrowLeft, AlertCircle, MessageSquare, ThumbsUp, ThumbsDown, Clock, Hash, Eye, Trash2, MoreVertical } from "lucide-react"
import { CommentItem } from "../comment-item"
import { groupChatApi, type Comment } from "@/utils/api/group-chat-client"
import { GraphVisualization } from "../visualization/graph-visualization"
import { LoadingState } from "../components/loading-state"
import { DiscussionHeader } from "../components/discussion-header"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog"

export default function DiscussionDetailPage() {
    const router = useRouter()
    const params = useParams()
    const discussionId = params.id as string

    const [discussion, setDiscussion] = useState<Comment | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [showDeleteDialog, setShowDeleteDialog] = useState(false)

    useEffect(() => {
        const fetchDiscussion = async () => {
            try {
                setLoading(true)
                setError(null)

                const data = await groupChatApi.getDiscussions()

                if (data.success) {
                    const found = data.discussions.find(
                        (d) => d._id === discussionId || String(d.id) === discussionId
                    )

                    if (found) {
                        setDiscussion({
                            id: found.id || Date.now(),
                            _id: found._id,
                            author: found.author,
                            avatar: found.avatar,
                            time: found.time,
                            content: found.content,
                            title: found.title,
                            upvotes: found.upvotes,
                            downvotes: found.downvotes,
                            userVote: found.userVote,
                            replies: found.replies || []
                        })
                    } else {
                        setError("Discussion not found")
                    }
                } else {
                    setError(data.error || "Failed to load discussion")
                }
            } catch (err) {
                console.error('Error fetching discussion:', err)
                setError("Failed to load discussion. Please try again.")
            } finally {
                setLoading(false)
            }
        }

        if (discussionId) {
            fetchDiscussion()
        }
    }, [discussionId])

    const findCommentById = (comment: Comment, id: number): Comment | null => {
        if (comment.id === id) return comment

        if (comment.replies) {
            for (const reply of comment.replies) {
                const found = findCommentById(reply, id)
                if (found) return found
            }
        }
        return null
    }

    const handleReply = async (parentId: number, content: string) => {
        if (!discussion) return

        try {
            const parent = findCommentById(discussion, parentId)
            if (!parent || !parent._id) return

            const data = await groupChatApi.addReply(parent._id, {
                author: 'You',
                avatar: '/avatars/shadcn.jpg',
                content
            })

            if (data.success) {
                const addReplyToComment = (comment: Comment): Comment => {
                    if (comment.id === parentId) {
                        const newReply: Comment = {
                            id: data.reply?.id ?? Date.now(),
                            _id: data.reply?._id,
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
                            replies: comment.replies.map(r => addReplyToComment(r))
                        }
                    }
                    return comment
                }

                setDiscussion(addReplyToComment(discussion))
            }
        } catch (error) {
            console.error('Error adding reply:', error)
        }
    }

    const handleDelete = async (commentId: number) => {
        if (!discussion) return

        try {
            const comment = findCommentById(discussion, commentId)
            if (!comment || !comment._id) return

            const data = await groupChatApi.deleteDiscussion(comment._id)

            if (data.success) {
                if (commentId === discussion.id) {
                    router.push('/dashboard/group-chat')
                } else {
                    const deleteComment = (comment: Comment): Comment | null => {
                        if (!comment.replies) return comment

                        const newReplies = comment.replies
                            .filter(r => r.id !== commentId)
                            .map(r => deleteComment(r))
                            .filter((r): r is Comment => r !== null)

                        return {
                            ...comment,
                            replies: newReplies
                        }
                    }

                    const updated = deleteComment(discussion)
                    if (updated) setDiscussion(updated)
                }
            }
        } catch (error) {
            console.error('Error deleting comment:', error)
        }
    }

    const handleVote = async (commentId: number, voteType: 'up' | 'down') => {
        if (!discussion) return

        try {
            const comment = findCommentById(discussion, commentId)
            if (!comment || !comment._id) return

            const data = await groupChatApi.voteDiscussion(
                comment._id,
                voteType,
                comment.userVote || null
            )

            if (data.success && data.discussion) {
                const updateVote = (comment: Comment): Comment => {
                    if (comment.id === commentId) {
                        return {
                            ...comment,
                            upvotes: data.discussion.upvotes,
                            downvotes: data.discussion.downvotes,
                            userVote: data.discussion.userVote
                        }
                    }
                    if (comment.replies) {
                        return {
                            ...comment,
                            replies: comment.replies.map(r => updateVote(r))
                        }
                    }
                    return comment
                }

                setDiscussion(updateVote(discussion))
            }
        } catch (error) {
            console.error('Error updating vote:', error)
        }
    }

    const handleDeleteDiscussion = async () => {
        if (!discussion?._id) return

        try {
            const data = await groupChatApi.deleteDiscussion(discussion._id)
            if (data.success) {
                router.push('/dashboard/group-chat')
            }
        } catch (err) {
            console.error('Error deleting discussion:', err)
        } finally {
            setShowDeleteDialog(false)
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

    const handleRefresh = async () => {
        const data = await groupChatApi.getDiscussions()
        if (data.success) {
            const found = data.discussions.find(
                (d) => d._id === discussionId || String(d.id) === discussionId
            )
            if (found) {
                setDiscussion({
                    id: found.id || Date.now(),
                    _id: found._id,
                    author: found.author,
                    avatar: found.avatar,
                    time: found.time,
                    content: found.content,
                    title: found.title,
                    upvotes: found.upvotes,
                    downvotes: found.downvotes,
                    userVote: found.userVote,
                    replies: found.replies || []
                })
            }
        }
    }

    if (loading) {
        return (
            <div className="flex flex-col h-screen bg-background">
                <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => router.push('/dashboard/group-chat')}
                    >
                        <ArrowLeft className="h-4 w-4 mr-2" />
                        Back
                    </Button>
                </header>
                <div className="flex-1 flex items-center justify-center">
                    <LoadingState message="Loading discussion..." />
                </div>
            </div>
        )
    }

    if (error || !discussion) {
        return (
            <div className="flex flex-col h-screen bg-background">
                <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => router.push('/dashboard/group-chat')}
                    >
                        <ArrowLeft className="h-4 w-4 mr-2" />
                        Back
                    </Button>
                </header>
                <div className="flex-1 flex items-center justify-center p-4">
                    <Card className="max-w-md w-full p-8 text-center">
                        <div className="flex justify-center mb-4">
                            <div className="h-16 w-16 rounded-full bg-destructive/10 flex items-center justify-center">
                                <AlertCircle className="h-8 w-8 text-destructive" />
                            </div>
                        </div>
                        <h2 className="text-xl font-semibold mb-2">
                            {error === "Discussion not found" ? "Discussion Not Found" : "Error Loading Discussion"}
                        </h2>
                        <p className="text-muted-foreground mb-6">
                            {error || "The discussion you're looking for doesn't exist or has been deleted."}
                        </p>
                        <Button onClick={() => router.push('/dashboard/group-chat')}>
                            Return to Discussions
                        </Button>
                    </Card>
                </div>
            </div>
        )
    }

    const replyCount = countReplies(discussion)

    return (
        <div className="flex flex-col h-screen bg-background">
            <header className="sticky top-0 z-10 flex h-16 shrink-0 items-center gap-2 border-b px-4 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => router.push('/dashboard/group-chat')}
                >
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back
                </Button>
                <Separator orientation="vertical" className="mx-2 h-4" />
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <span>Discussion</span>
                    {discussion.title && (
                        <>
                            <span>/</span>
                            <span className="font-medium text-foreground">{discussion.title}</span>
                        </>
                    )}
                </div>
            </header>

            <div className="flex-1 flex overflow-hidden">
                <main className="flex-1 flex flex-col min-h-0 w-1/2 border-r overflow-hidden">
                    <ScrollArea className="flex-1 h-full">
                        <div className="p-6 space-y-6 pb-20">
                            <Card className="p-6 shadow-sm border-muted/40 hover:shadow-md transition-shadow duration-200">
                                <DiscussionHeader
                                    discussion={discussion}
                                    replyCount={replyCount}
                                    showFullTitle={true}
                                />
                            </Card>

                            {replyCount > 0 && (
                                <div>
                                    <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
                                        <MessageSquare className="h-5 w-5" />
                                        Replies ({replyCount})
                                    </h2>
                                    <Card className="overflow-hidden">
                                        <div className="divide-y">
                                            {discussion.replies?.map((reply) => (
                                                <CommentItem
                                                    key={reply.id}
                                                    comment={reply}
                                                    onReply={handleReply}
                                                    onDelete={handleDelete}
                                                    onVote={handleVote}
                                                />
                                            ))}
                                        </div>
                                    </Card>
                                </div>
                            )}
                        </div>
                    </ScrollArea>
                </main>

                <aside className="w-1/2 flex flex-col bg-gradient-to-br from-background to-muted/20">
                    <div className="p-4 border-b bg-gradient-to-r from-muted/40 to-muted/20 backdrop-blur-sm">
                        <h2 className="font-semibold text-sm flex items-center gap-2">
                            <div className="h-6 w-6 rounded bg-primary/10 flex items-center justify-center">
                                <Eye className="h-3.5 w-3.5 text-primary" />
                            </div>
                            Discussion Map
                        </h2>
                        <p className="text-xs text-muted-foreground mt-1">3D visualization • Auto-rotating</p>
                    </div>
                    <div className="flex-1 relative">
                        <GraphVisualization
                            discussions={[discussion]}
                            onRefresh={handleRefresh}
                            static
                        />
                    </div>
                </aside>
            </div>
        </div>
    )
}
