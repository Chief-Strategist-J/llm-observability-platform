import { NextRequest, NextResponse } from 'next/server'
import { getMessages, createMessage } from '@/database/services/chat-service'

export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url)
        const conversationId = searchParams.get('conversationId') || 'default'

        const messages = await getMessages(conversationId)
        return NextResponse.json({ messages, success: true }, { status: 200 })
    } catch (error) {
        console.error('GET /api/chat error:', error)
        return NextResponse.json(
            { error: 'Failed to fetch messages', success: false },
            { status: 500 }
        )
    }
}

export async function POST(request: NextRequest) {
    try {
        const body = await request.json()
        const { text, sender, author, avatar, time, conversationId = 'default' } = body

        if (!text || !sender || !author) {
            return NextResponse.json(
                { error: 'Missing required fields', success: false },
                { status: 400 }
            )
        }

        const message = await createMessage({
            conversationId,
            text,
            sender,
            author,
            avatar: avatar || '/avatars/01.png',
            time: time || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        })

        return NextResponse.json({ message, success: true }, { status: 201 })
    } catch (error) {
        console.error('POST /api/chat error:', error)
        return NextResponse.json(
            { error: 'Failed to create message', success: false },
            { status: 500 }
        )
    }
}
