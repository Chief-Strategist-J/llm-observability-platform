export interface Message {
    id: string
    text: string
    sender: "me" | "friend"
    time: string
    timestamp: number
    originalConversationId?: string
    type?: 'text' | 'merge'
    mergeSourceId?: string
    branchId?: string
}

export interface Conversation {
    id: string
    title: string
    messages: Message[]
    createdAt: string
    status: 'active' | 'merged'
    mergedInto?: string
}

export interface Friend {
    id: string
    name: string
    email: string
    avatar: string
    status: string
    lastMessage: string
    conversations: Conversation[]
    bio?: string
    joinedDate?: string
    phone?: string
    location?: string
}

export interface AIChat {
    id: string
    title: string
    messages: { role: 'user' | 'ai', content: string, time: string, timestamp: number }[]
    createdAt: string
}
