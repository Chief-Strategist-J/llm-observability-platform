import { useState } from "react"
import { ThumbsUp, ThumbsDown, MessageCircle, Share2, MoreHorizontal, Trash2, Check } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Textarea } from "@/components/ui/textarea"
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
import { type Comment } from "./comment-data"

interface CommentItemProps {
    comment: Comment
    depth?: number
    onReply: (parentId: number, content: string) => void
    onDelete: (commentId: number) => void
    onVote: (commentId: number, voteType: 'up' | 'down') => void
}

export function CommentItem({ comment, depth = 0, onReply, onDelete, onVote }: CommentItemProps) {
    const [showReply, setShowReply] = useState(false)
    const [replyText, setReplyText] = useState("")
    const [showDeleteDialog, setShowDeleteDialog] = useState(false)
    const [copied, setCopied] = useState(false)
    const isOwnComment = comment.author === "You"

    const handleReply = () => {
        if (replyText.trim()) {
            onReply(comment.id, replyText)
            setReplyText("")
            setShowReply(false)
        }
    }

    const handleDelete = () => {
        onDelete(comment.id)
        setShowDeleteDialog(false)
    }

    const handleVote = (voteType: 'up' | 'down') => {
        onVote(comment.id, voteType)
    }

    const handleShare = async () => {
        const shareUrl = `${window.location.origin}/dashboard/group-chat#comment-${comment.id}`
        try {
            await navigator.clipboard.writeText(shareUrl)
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
        } catch (err) {
            console.error('Failed to copy:', err)
        }
    }

    return (
        <div className={depth > 0 ? "ml-8 border-l-2 border-border pl-4" : ""} id={`comment-${comment.id}`}>
            <div className="flex gap-3 py-3">
                <Avatar className="h-8 w-8 flex-shrink-0">
                    <AvatarImage src={comment.avatar} />
                    <AvatarFallback>{comment.author[0]}</AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0 space-y-2">
                    <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-semibold text-sm">{comment.author}</span>
                        <span className="text-xs text-muted-foreground">{comment.time}</span>
                    </div>
                    <div className="break-words whitespace-pre-wrap max-w-full">
                        <p className="text-sm leading-relaxed">{comment.content}</p>
                    </div>
                    <div className="flex items-center gap-2 flex-wrap">
                        <Button
                            variant={comment.userVote === 'up' ? "default" : "ghost"}
                            size="sm"
                            className="h-7 gap-1"
                            onClick={() => handleVote('up')}
                        >
                            <ThumbsUp className="h-3 w-3" />
                            <span className="text-xs">{comment.upvotes}</span>
                        </Button>
                        <Button
                            variant={comment.userVote === 'down' ? "default" : "ghost"}
                            size="sm"
                            className="h-7 gap-1"
                            onClick={() => handleVote('down')}
                        >
                            <ThumbsDown className="h-3 w-3" />
                            {comment.downvotes > 0 && <span className="text-xs">{comment.downvotes}</span>}
                        </Button>
                        <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 gap-1"
                            onClick={() => setShowReply(!showReply)}
                        >
                            <MessageCircle className="h-3 w-3" />
                            <span className="text-xs">Reply</span>
                        </Button>
                        <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 gap-1"
                            onClick={handleShare}
                        >
                            {copied ? <Check className="h-3 w-3" /> : <Share2 className="h-3 w-3" />}
                            <span className="text-xs">{copied ? 'Copied' : 'Share'}</span>
                        </Button>
                        {isOwnComment && (
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <Button variant="ghost" size="sm" className="h-7 px-2">
                                        <MoreHorizontal className="h-3 w-3" />
                                    </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                    <DropdownMenuItem
                                        className="text-destructive focus:text-destructive"
                                        onClick={() => setShowDeleteDialog(true)}
                                    >
                                        <Trash2 className="h-4 w-4 mr-2" />
                                        Delete
                                    </DropdownMenuItem>
                                </DropdownMenuContent>
                            </DropdownMenu>
                        )}
                    </div>

                    {showReply && (
                        <div className="pt-2 max-w-full">
                            <Textarea
                                placeholder="Write a reply..."
                                className="min-h-[80px] text-sm resize-y w-full"
                                value={replyText}
                                onChange={(e) => setReplyText(e.target.value)}
                                style={{ maxHeight: '200px' }}
                            />
                            <div className="flex gap-2 mt-2">
                                <Button size="sm" onClick={handleReply}>Reply</Button>
                                <Button size="sm" variant="ghost" onClick={() => {
                                    setShowReply(false)
                                    setReplyText("")
                                }}>
                                    Cancel
                                </Button>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {comment.replies && comment.replies.length > 0 && (
                <div>
                    {comment.replies.map((reply) => (
                        <CommentItem
                            key={reply.id}
                            comment={reply}
                            depth={depth + 1}
                            onReply={onReply}
                            onDelete={onDelete}
                            onVote={onVote}
                        />
                    ))}
                </div>
            )}

            <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Delete Comment</AlertDialogTitle>
                        <AlertDialogDescription>
                            Are you sure you want to delete this comment? This action cannot be undone.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                            Delete
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    )
}
