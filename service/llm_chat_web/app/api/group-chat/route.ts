import { NextRequest, NextResponse } from 'next/server'
import { getDiscussions, createDiscussion } from '@/database/services/group-chat-service'

export async function GET() {
    try {
        const discussions = await getDiscussions()
        return NextResponse.json({ discussions, success: true }, { status: 200 })
    } catch (error) {
        console.error('GET /api/group-chat error:', error)
        return NextResponse.json(
            { error: 'Failed to fetch discussions', success: false },
            { status: 500 }
        )
    }
}

export async function POST(request: NextRequest) {
    try {
        const body = await request.json()
        const { author, avatar, time, content, title, upvotes = 0, downvotes = 0, userVote = null, replies = [] } = body

        if (!author || !content) {
            return NextResponse.json(
                { error: 'Missing required fields', success: false },
                { status: 400 }
            )
        }

        const discussion = await createDiscussion({
            author,
            avatar: avatar || '/avatars/shadcn.jpg',
            time: time || 'Just now',
            content,
            title,
            upvotes,
            downvotes,
            userVote,
            replies
        })

        return NextResponse.json({ discussion, success: true }, { status: 201 })
    } catch (error) {
        console.error('POST /api/group-chat error:', error)
        return NextResponse.json(
            { error: 'Failed to create discussion', success: false },
            { status: 500 }
        )
    }
}
