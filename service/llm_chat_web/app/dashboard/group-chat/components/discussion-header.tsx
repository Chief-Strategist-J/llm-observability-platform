import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { MessageSquare, ThumbsUp, ThumbsDown } from "lucide-react"
import { Comment } from "@/utils/api/group-chat-client"

interface DiscussionHeaderProps {
    discussion: Comment
    replyCount: number
    showFullTitle?: boolean
}

export function DiscussionHeader({
    discussion,
    replyCount,
    showFullTitle = false
}: DiscussionHeaderProps) {
    return (
        <div className="flex gap-4">
            <Avatar className="h-12 w-12 flex-shrink-0 ring-2 ring-background shadow-sm">
                <AvatarImage src={discussion.avatar} />
                <AvatarFallback>{discussion.author[0]}</AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2">
                    <span className="font-semibold text-foreground">{discussion.author}</span>
                    <span className="text-sm text-muted-foreground">•</span>
                    <span className="text-sm text-muted-foreground">{discussion.time}</span>
                </div>
                {discussion.title && showFullTitle && (
                    <h1 className="text-3xl font-bold mb-4 bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text">
                        {discussion.title}
                    </h1>
                )}
                <p className="text-base leading-relaxed whitespace-pre-wrap mb-4 text-foreground/90">
                    {discussion.content}
                </p>

                <div className="flex items-center gap-4 text-sm pt-3 border-t mt-4">
                    <div className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 transition-colors cursor-pointer">
                        <ThumbsUp className="h-4 w-4" />
                        <span className="font-medium">{discussion.upvotes}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-rose-600 dark:text-rose-400 hover:text-rose-700 dark:hover:text-rose-300 transition-colors cursor-pointer">
                        <ThumbsDown className="h-4 w-4" />
                        <span className="font-medium">{discussion.downvotes}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-sky-600 dark:text-sky-400">
                        <MessageSquare className="h-4 w-4" />
                        <span className="font-medium">{replyCount} {replyCount === 1 ? 'Reply' : 'Replies'}</span>
                    </div>
                </div>
            </div>
        </div>
    )
}
