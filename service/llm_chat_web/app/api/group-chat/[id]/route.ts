import { NextRequest, NextResponse } from 'next/server'
import { updateDiscussion, deleteDiscussion, addReply, voteDiscussion } from '@/database/services/group-chat-service'

export async function POST(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const body = await request.json()
        const { id } = await params
        const { author, avatar, content, time } = body

        if (!author || !content) {
            return NextResponse.json(
                { error: 'Missing required fields', success: false },
                { status: 400 }
            )
        }

        const result = await addReply(id, {
            author,
            avatar: avatar || '/avatars/shadcn.jpg',
            time: time || 'Just now',
            content,
            upvotes: 0,
            downvotes: 0,
            userVote: null,
            replies: []
        })

        return NextResponse.json({ success: true, ...result }, { status: 201 })
    } catch (error) {
        console.error('POST /api/group-chat/[id] error:', error)
        return NextResponse.json(
            { error: 'Failed to add reply', success: false },
            { status: 500 }
        )
    }
}

export async function PUT(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const body = await request.json()
        const { id } = await params
        const { voteType, currentUserVote, ...updates } = body

        // If it's a vote request
        if (voteType) {
            const discussion = await voteDiscussion(id, voteType, currentUserVote)
            return NextResponse.json({ discussion, success: true }, { status: 200 })
        }

        // Otherwise it's a regular update
        const count = await updateDiscussion(id, updates)

        if (count === 0) {
            return NextResponse.json(
                { error: 'Discussion not found', success: false },
                { status: 404 }
            )
        }

        return NextResponse.json({ success: true, count }, { status: 200 })
    } catch (error) {
        console.error('PUT /api/group-chat/[id] error:', error)
        return NextResponse.json(
            { error: 'Failed to update discussion', success: false },
            { status: 500 }
        )
    }
}

export async function DELETE(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params
        const count = await deleteDiscussion(id)

        if (count === 0) {
            return NextResponse.json(
                { error: 'Discussion not found', success: false },
                { status: 404 }
            )
        }

        return NextResponse.json({ success: true, count }, { status: 200 })
    } catch (error) {
        console.error('DELETE /api/group-chat/[id] error:', error)
        return NextResponse.json(
            { error: 'Failed to delete discussion', success: false },
            { status: 500 }
        )
    }
}
