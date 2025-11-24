"use client"

import { useState, useRef, useEffect } from "react"
import { Send } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { ScrollArea } from "@/components/ui/scroll-area"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"

interface Message {
    id: number
    text: string
    sender: "me" | "other"
    time: string
    author: string
    avatar: string
}

const initialMessages: Message[] = [
    {
        id: 1,
        text: "Hey, how are you?",
        sender: "other",
        time: "10:30 AM",
        author: "Jackson Lee",
        avatar: "/avatars/02.png"
    },
    {
        id: 2,
        text: "I'm good! Working on the new project.",
        sender: "me",
        time: "10:31 AM",
        author: "You",
        avatar: "/avatars/01.png"
    },
    {
        id: 3,
        text: "That sounds exciting! What are you building?",
        sender: "other",
        time: "10:32 AM",
        author: "Jackson Lee",
        avatar: "/avatars/02.png"
    },
    {
        id: 4,
        text: "A chat application with React and Next.js",
        sender: "me",
        time: "10:33 AM",
        author: "You",
        avatar: "/avatars/01.png"
    },
]

export default function ChatPage() {
    const [messages, setMessages] = useState<Message[]>(initialMessages)
    const [newMessage, setNewMessage] = useState("")
    const scrollAreaRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        if (scrollAreaRef.current) {
            const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]')
            if (scrollContainer) {
                scrollContainer.scrollTop = scrollContainer.scrollHeight
            }
        }
    }, [messages])

    const handleSend = () => {
        if (newMessage.trim()) {
            const newMsg: Message = {
                id: messages.length + 1,
                text: newMessage,
                sender: "me",
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                author: "You",
                avatar: "/avatars/01.png"
            }
            setMessages([...messages, newMsg])
            setNewMessage("")

            setTimeout(() => {
                const reply: Message = {
                    id: messages.length + 2,
                    text: "Thanks for the message! I'll get back to you soon.",
                    sender: "other",
                    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                    author: "Jackson Lee",
                    avatar: "/avatars/02.png"
                }
                setMessages(prev => [...prev, reply])
            }, 1000)
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
                    />
                    <Button size="icon" onClick={handleSend}>
                        <Send className="h-4 w-4" />
                    </Button>
                </div>
            </div>
        </div>
    )
}
