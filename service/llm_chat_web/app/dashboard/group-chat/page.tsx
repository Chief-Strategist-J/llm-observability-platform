"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { Textarea } from "@/components/ui/textarea"
import { CommentItem } from "./comment-item"
import { type Comment, initialDiscussions } from "./comment-data"

export default function GroupChatPage() {
    const [discussions, setDiscussions] = useState<Comment[]>(initialDiscussions)
    const [newPost, setNewPost] = useState("")

    const handlePost = () => {
        if (newPost.trim()) {
            const newDiscussion: Comment = {
                id: Date.now(),
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
        }
    }

    const handleReply = (parentId: number, content: string) => {
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
    }

    const handleDelete = (commentId: number) => {
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
    }

    const handleVote = (commentId: number, voteType: 'up' | 'down') => {
        const updateVote = (comments: Comment[]): Comment[] => {
            return comments.map(comment => {
                if (comment.id === commentId) {
                    let newComment = { ...comment }

                    if (comment.userVote === voteType) {
                        if (voteType === 'up') {
                            newComment.upvotes -= 1
                        } else {
                            newComment.downvotes -= 1
                        }
                        newComment.userVote = null
                    } else {
                        if (comment.userVote === 'up') {
                            newComment.upvotes -= 1
                        } else if (comment.userVote === 'down') {
                            newComment.downvotes -= 1
                        }

                        if (voteType === 'up') {
                            newComment.upvotes += 1
                        } else {
                            newComment.downvotes += 1
                        }
                        newComment.userVote = voteType
                    }

                    return newComment
                }
                if (comment.replies) {
                    return {
                        ...comment,
                        replies: updateVote(comment.replies)
                    }
                }
                return comment
            })
        }

        setDiscussions(updateVote(discussions))
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
                        />
                        <div className="flex justify-end mt-2">
                            <Button onClick={handlePost}>Post</Button>
                        </div>
                    </Card>

                    <ScrollArea className="flex-1">
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
