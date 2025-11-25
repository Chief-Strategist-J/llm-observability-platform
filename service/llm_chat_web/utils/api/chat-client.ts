export interface Message {
    _id?: string
    id: number
    text: string
    sender: "me" | "other"
    time: string
    author: string
    avatar: string
}

export interface ChatResponse {
    messages: Message[]
    success: boolean
    error?: string
}

export interface MessageResponse {
    message: Message
    success: boolean
    error?: string
}

export const chatApi = {
    /**
     * Fetch all messages for a conversation
     */
    async getMessages(conversationId: string = 'default'): Promise<ChatResponse> {
        const response = await fetch(`/api/chat?conversationId=${conversationId}`)
        return response.json()
    },

    /**
     * Send a new message
     */
    async sendMessage(data: {
        conversationId?: string
        text: string
        sender: 'me' | 'other'
        author: string
        avatar?: string
        time?: string
    }): Promise<MessageResponse> {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                conversationId: data.conversationId || 'default',
                text: data.text,
                sender: data.sender,
                author: data.author,
                avatar: data.avatar || '/avatars/01.png',
                time: data.time || new Date().toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit'
                })
            })
        })
        return response.json()
    },

    /**
     * Update an existing message
     */
    async updateMessage(id: string, updates: Partial<Message>): Promise<{ success: boolean; count: number; error?: string }> {
        const response = await fetch(`/api/chat/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updates)
        })
        return response.json()
    },

    /**
     * Delete a message
     */
    async deleteMessage(id: string): Promise<{ success: boolean; count: number; error?: string }> {
        const response = await fetch(`/api/chat/${id}`, {
            method: 'DELETE'
        })
        return response.json()
    }
}
