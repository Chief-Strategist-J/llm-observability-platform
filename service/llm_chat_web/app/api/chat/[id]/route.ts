import { NextRequest, NextResponse } from 'next/server'
import { updateMessage, deleteMessage } from '@/database/services/chat-service'

export async function PUT(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const body = await request.json()
        const { id } = await params

        const count = await updateMessage(id, body)

        if (count === 0) {
            return NextResponse.json(
                { error: 'Message not found', success: false },
                { status: 404 }
            )
        }

        return NextResponse.json({ success: true, count }, { status: 200 })
    } catch (error) {
        console.error('PUT /api/chat/[id] error:', error)
        return NextResponse.json(
            { error: 'Failed to update message', success: false },
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
        const count = await deleteMessage(id)

        if (count === 0) {
            return NextResponse.json(
                { error: 'Message not found', success: false },
                { status: 404 }
            )
        }

        return NextResponse.json({ success: true, count }, { status: 200 })
    } catch (error) {
        console.error('DELETE /api/chat/[id] error:', error)
        return NextResponse.json(
            { error: 'Failed to delete message', success: false },
            { status: 500 }
        )
    }
}
