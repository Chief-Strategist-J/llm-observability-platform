export interface Comment {
    _id?: string
    id: number
    author: string
    avatar: string
    time: string
    content: string
    title?: string
    upvotes: number
    downvotes: number
    userVote?: 'up' | 'down' | null
    replies?: Comment[]
}

export interface DiscussionsResponse {
    discussions: Comment[]
    success: boolean
    error?: string
}

export interface DiscussionResponse {
    discussion: Comment
    success: boolean
    error?: string
}

export interface ReplyResponse {
    success: boolean
    count: number
    reply?: Comment
    error?: string
}

export const groupChatApi = {
    async getDiscussions(): Promise<DiscussionsResponse> {
        const response = await fetch('/api/group-chat')
        return response.json()
    },

    async createDiscussion(data: {
        author: string
        avatar?: string
        time?: string
        content: string
        title?: string
    }): Promise<DiscussionResponse> {
        const response = await fetch('/api/group-chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                author: data.author,
                avatar: data.avatar || '/avatars/shadcn.jpg',
                time: data.time || 'Just now',
                content: data.content,
                title: data.title,
                upvotes: 0,
                downvotes: 0,
                userVote: null,
                replies: []
            })
        })
        return response.json()
    },

    async addReply(discussionId: string, data: {
        author: string
        avatar?: string
        time?: string
        content: string
    }): Promise<ReplyResponse> {
        const response = await fetch(`/api/group-chat/${discussionId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                author: data.author,
                avatar: data.avatar || '/avatars/shadcn.jpg',
                time: data.time || 'Just now',
                content: data.content
            })
        })
        return response.json()
    },

    async voteDiscussion(
        discussionId: string,
        voteType: 'up' | 'down',
        currentUserVote: 'up' | 'down' | null
    ): Promise<DiscussionResponse> {
        const response = await fetch(`/api/group-chat/${discussionId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                voteType,
                currentUserVote
            })
        })
        return response.json()
    },

    async deleteDiscussion(discussionId: string): Promise<{ success: boolean; count: number; error?: string }> {
        const response = await fetch(`/api/group-chat/${discussionId}`, {
            method: 'DELETE'
        })
        return response.json()
    }
}
