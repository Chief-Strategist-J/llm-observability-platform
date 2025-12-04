import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { Heart, MessageCircle, Flame } from "lucide-react"
import { Comment } from "@/utils/api/group-chat-client"

interface DiscussionCardProps {
    discussion: Comment
    onClick: () => void
    replyCount: number
    isTrending?: boolean
}

export function DiscussionCard({
    discussion,
    onClick,
    replyCount,
    isTrending = false
}: DiscussionCardProps) {
    return (
        <Card
            className="overflow-hidden hover:shadow-lg transition-all duration-300 cursor-pointer group bg-gradient-to-br from-background to-muted/30 border hover:border-primary/30"
            onClick={onClick}
        >
            <div className="p-5">
                <div className="flex gap-4">
                    <Avatar className="h-11 w-11 flex-shrink-0 ring-2 ring-muted group-hover:ring-primary/40 group-hover:scale-105 transition-all duration-300">
                        <AvatarImage src={discussion.avatar} />
                        <AvatarFallback className="bg-gradient-to-br from-slate-600 to-slate-700 dark:from-slate-400 dark:to-slate-500 text-white">{discussion.author[0]}</AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                            <span className="font-semibold text-sm text-foreground group-hover:text-primary transition-colors">
                                {discussion.author}
                            </span>
                            <span className="text-xs text-muted-foreground">
                                {discussion.time}
                            </span>
                            {isTrending && (
                                <Badge variant="secondary" className="ml-auto gap-1 bg-amber-500/10 text-amber-700 dark:text-amber-500 border-amber-500/20">
                                    <Flame className="h-3 w-3" />
                                    Trending
                                </Badge>
                            )}
                        </div>

                        {discussion.title && (
                            <h3 className="font-bold text-lg mb-2 text-foreground group-hover:text-primary transition-colors line-clamp-2">
                                {discussion.title}
                            </h3>
                        )}

                        <p className="text-sm text-muted-foreground leading-relaxed line-clamp-2 mb-4">
                            {discussion.content}
                        </p>

                        <div className="flex items-center gap-6 text-sm">
                            <div className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 transition-colors">
                                <Heart className="h-4 w-4" />
                                <span className="font-medium">{discussion.upvotes}</span>
                            </div>
                            <div className="flex items-center gap-1.5 text-sky-600 dark:text-sky-400 hover:text-sky-700 dark:hover:text-sky-300 transition-colors">
                                <MessageCircle className="h-4 w-4" />
                                <span className="font-medium">{replyCount}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </Card>
    )
}
