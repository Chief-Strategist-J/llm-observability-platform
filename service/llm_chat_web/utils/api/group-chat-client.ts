export interface Comment {
    _id?: string
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

export const groupChatApi = {
    /**
     * Fetch all discussions
     */
    async getDiscussions(): Promise<DiscussionsResponse> {
        const response = await fetch('/api/group-chat')
        return response.json()
    },

    /**
     * Create a new discussion
     */
    async createDiscussion(data: {
        author: string
        avatar?: string
        time?: string
        content: string
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
                upvotes: 0,
                downvotes: 0,
                userVote: null,
                replies: []
            })
        })
        return response.json()
    },

    /**
     * Add a reply to a discussion
     */
    async addReply(discussionId: string, data: {
        author: string
        avatar?: string
        time?: string
        content: string
    }): Promise<{ success: boolean; count: number; error?: string }> {
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

    /**
     * Vote on a discussion
     */
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

    /**
     * Delete a discussion
     */
    async deleteDiscussion(discussionId: string): Promise<{ success: boolean; count: number; error?: string }> {
        const response = await fetch(`/api/group-chat/${discussionId}`, {
            method: 'DELETE'
        })
        return response.json()
    }
}
