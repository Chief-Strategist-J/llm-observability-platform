export interface Comment {
    id: number
    author: string
    avatar: string
    time: string
    content: string
    upvotes: number
    downvotes: number
    userVote?: 'up' | 'down' | null
    replies?: Comment[]
}

export const initialDiscussions: Comment[] = [
    {
        id: 1,
        author: "HuckleberryUst250",
        avatar: "/avatars/01.png",
        time: "3h ago",
        content: "State management is not about performance. Why are you concerned?",
        upvotes: 52,
        downvotes: 3,
        userVote: null,
        replies: [
            {
                id: 2,
                author: "ilawicki",
                avatar: "/avatars/02.png",
                time: "3h ago",
                content: "You got downvoted, lol.",
                upvotes: 3,
                downvotes: 1,
                userVote: null,
            },
        ],
    },
]
