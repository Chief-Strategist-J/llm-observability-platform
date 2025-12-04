"use client"

import { useState, useEffect } from "react"
import { GraphVisualization } from "./graph-visualization"
import { groupChatApi, type Comment } from "@/utils/api/group-chat-client"

export default function VisualizationPage() {
    const [discussions, setDiscussions] = useState<Comment[]>([])
    const [loading, setLoading] = useState(true)

    const loadDiscussions = async () => {
        try {
            const data = await groupChatApi.getDiscussions()
            if (data.success) {
                const mappedDiscussions = data.discussions.map((disc) => ({
                    id: disc.id || Date.now(),
                    _id: disc._id,
                    author: disc.author,
                    avatar: disc.avatar,
                    time: disc.time,
                    content: disc.content,
                    title: disc.title,
                    upvotes: disc.upvotes,
                    downvotes: disc.downvotes,
                    userVote: disc.userVote,
                    replies: disc.replies || []
                }))
                setDiscussions(mappedDiscussions)
            }
        } catch (error) {
            console.error('Error fetching discussions:', error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        loadDiscussions()
    }, [])

    return (
        <div className="h-screen w-full">
            <GraphVisualization
                discussions={discussions}
                onRefresh={loadDiscussions}
            />
        </div>
    )
}
