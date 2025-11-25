"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { ScrollArea } from "@/components/ui/scroll-area"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { chatApi, type Message } from "@/utils/api/chat-client"

export default function ChatPage() {
    const [messages, setMessages] = useState<Message[]>([])
    const [newMessage, setNewMessage] = useState("")
    const [loading, setLoading] = useState(true)
    const [sending, setSending] = useState(false)
    const scrollAreaRef = useRef<HTMLDivElement>(null)

    // Fetch messages on mount
    useEffect(() => {
        const fetchMessages = async () => {
            try {
                setLoading(true)
                const data = await chatApi.getMessages('default')

                if (data.success) {
                    const mappedMessages = data.messages.map((msg, idx) => ({
                        id: idx + 1,
                        _id: msg._id,
                        text: msg.text,
                        sender: msg.sender,
                        time: msg.time,
                        author: msg.author,
                        avatar: msg.avatar
                    }))
                    setMessages(mappedMessages)
                } else {
                    console.error('Failed to load messages')
                }
            } catch (error) {
                console.error('Error fetching messages:', error)
            } finally {
                setLoading(false)
            }
        }

        fetchMessages()
    }, [])

    useEffect(() => {
        if (scrollAreaRef.current) {
            const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]')
            if (scrollContainer) {
                scrollContainer.scrollTop = scrollContainer.scrollHeight
            }
        }
    }, [messages])

    const handleSend = async () => {
        if (newMessage.trim() && !sending) {
            setSending(true)
            try {
                const data = await chatApi.sendMessage({
                    conversationId: 'default',
                    text: newMessage,
                    sender: 'me',
                    author: 'You',
                    avatar: '/avatars/01.png'
                })

                if (data.success) {
                    const newMsg: Message = {
                        id: messages.length + 1,
                        _id: data.message._id,
                        text: newMessage,
                        sender: "me",
                        time: data.message.time,
                        author: "You",
                        avatar: "/avatars/01.png"
                    }
                    setMessages([...messages, newMsg])
                    setNewMessage("")
                } else {
                    console.error('Failed to send message')
                }
            } catch (error) {
                console.error('Error sending message:', error)
            } finally {
                setSending(false)
            }
        }
    }

    return (
        <div className="flex flex-1 flex-col h-screen">
            <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
                <SidebarTrigger className="-ml-1" />
                <Separator orientation="vertical" className="mr-2 h-4" />
                <div className="flex items-center gap-2">
                    <Avatar className="h-8 w-8">
                        <AvatarImage src="/avatars/02.png" />
                        <AvatarFallback>JL</AvatarFallback>
                    </Avatar>
                    <div>
                        <h2 className="text-sm font-semibold">Jackson Lee</h2>
                        <p className="text-xs text-muted-foreground">Online</p>
                    </div>
                </div>
            </header>

            <ScrollArea ref={scrollAreaRef} className="flex-1 p-4">
                {loading ? (
                    <div className="flex items-center justify-center h-full">
                        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    </div>
                ) : (
                    <div className="space-y-4">
                        {messages.map((message) => (
                            <div
                                key={message.id}
                                className={`flex gap-3 ${message.sender === "me" ? "justify-end" : "justify-start"}`}
                            >
                                {message.sender === "other" && (
                                    <Avatar className="h-8 w-8">
                                        <AvatarImage src={message.avatar} />
                                        <AvatarFallback>{message.author[0]}</AvatarFallback>
                                    </Avatar>
                                )}
                                <div className={`max-w-[70%] ${message.sender === "me" ? "items-end" : "items-start"} flex flex-col`}>
                                    <div
                                        className={`rounded-lg px-4 py-2 ${message.sender === "me"
                                            ? "bg-primary text-primary-foreground"
                                            : "bg-muted"
                                            }`}
                                    >
                                        <p className="text-sm">{message.text}</p>
                                    </div>
                                    <p className="text-xs mt-1 text-muted-foreground">
                                        {message.time}
                                    </p>
                                </div>
                                {message.sender === "me" && (
                                    <Avatar className="h-8 w-8">
                                        <AvatarImage src={message.avatar} />
                                        <AvatarFallback>{message.author[0]}</AvatarFallback>
                                    </Avatar>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </ScrollArea>

            <div className="border-t p-4">
                <div className="flex gap-2">
                    <Input
                        placeholder="Type a message..."
                        value={newMessage}
                        onChange={(e) => setNewMessage(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter" && !e.shiftKey) {
                                e.preventDefault()
                                handleSend()
                            }
                        }}
                        disabled={sending}
                    />
                    <Button size="icon" onClick={handleSend} disabled={sending}>
                        {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                    </Button>
                </div>
            </div>
        </div>
    )
}
