"use client"

import { useState, useRef, useEffect } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import {
    Send, Loader2, Bot, Users, Sparkles, Plus, Trash2,
    Edit3, X, Check, MoreVertical, MessageSquare, User,
    GitBranch, GitGraph, Paperclip, Smile
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { ScrollArea } from "@/components/ui/scroll-area"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { ChatSidebar } from "@/components/chat/chat-sidebar"
import { GitGraphView, GraphBranch, GraphMessage } from "@/components/chat/git-graph-view"
import { ChatDialogs } from "@/components/chat/chat-dialogs"
import { Friend, Conversation, Message, AIChat } from "@/components/chat/types"

const initialFriends: Friend[] = [
    {
        id: "f1",
        name: "Jackson Lee",
        email: "jackson@email.com",
        avatar: "/avatars/02.png",
        status: "online",
        lastMessage: "Hey, how's it going?",
        bio: "Software Developer | Coffee enthusiast | Open source contributor",
        joinedDate: "March 2024",
        phone: "+1 234 567 8900",
        location: "San Francisco, CA",
        conversations: [
            {
                id: "c1",
                title: "Project Discussion",
                createdAt: "2024-03-10",
                status: 'active',
                messages: [
                    { id: "m1", text: "Hey, how's it going?", sender: "friend", time: "10:30 AM", timestamp: 1710000000000 },
                    { id: "m2", text: "I'm good, thanks! Working on a project.", sender: "me", time: "10:32 AM", timestamp: 1710000120000 },
                ]
            }
        ]
    },
    {
        id: "f2",
        name: "Isabella Nguyen",
        email: "isabella@email.com",
        avatar: "/avatars/03.png",
        status: "away",
        lastMessage: "Check this out!",
        bio: "UX Designer | Travel lover | Art aficionado",
        joinedDate: "January 2024",
        conversations: [
            {
                id: "c1",
                title: "Design Review",
                createdAt: "2024-01-15",
                status: 'active',
                messages: [
                    { id: "m1", text: "Check this out!", sender: "friend", time: "9:15 AM", timestamp: 1705300000000 },
                ]
            }
        ]
    },
    {
        id: "f3",
        name: "William Kim",
        email: "will@email.com",
        avatar: "/avatars/04.png",
        status: "offline",
        lastMessage: "See you tomorrow",
        bio: "Product Manager | Hiker | Foodie",
        joinedDate: "February 2024",
        conversations: [
            {
                id: "c1",
                title: "Weekly Sync",
                createdAt: "2024-02-20",
                status: 'active',
                messages: [
                    { id: "m1", text: "Are we meeting tomorrow?", sender: "me", time: "Yesterday", timestamp: 1708400000000 },
                    { id: "m2", text: "See you tomorrow", sender: "friend", time: "Yesterday", timestamp: 1708400060000 },
                ]
            }
        ]
    },
    {
        id: "f4",
        name: "Sofia Davis",
        email: "sofia@email.com",
        avatar: "/avatars/05.png",
        status: "online",
        lastMessage: "Thanks for the help!",
        bio: "Data Scientist | Bookworm | Yoga instructor",
        joinedDate: "April 2024",
        conversations: [
            {
                id: "c1",
                title: "Data Analysis",
                createdAt: "2024-04-05",
                status: 'active',
                messages: []
            }
        ]
    }
]

export default function ChatPage() {
    const searchParams = useSearchParams()
    const router = useRouter()
    const friendId = searchParams.get("friendId")

    const [friends, setFriends] = useState<Friend[]>(initialFriends)
    const [selectedFriend, setSelectedFriend] = useState<Friend | null>(null)
    const [searchQuery, setSearchQuery] = useState("")
    const [newMessage, setNewMessage] = useState("")
    const [sending, setSending] = useState(false)
    const [aiMessage, setAiMessage] = useState("")
    const [aiLoading, setAiLoading] = useState(false)
    const friendScrollRef = useRef<HTMLDivElement>(null)
    const aiScrollRef = useRef<HTMLDivElement>(null)

    // Dialog States
    const [profileOpen, setProfileOpen] = useState(false)
    const [editingMessage, setEditingMessage] = useState<{ id: string, content: string } | null>(null)
    const [emailDialogOpen, setEmailDialogOpen] = useState(false)
    const [emailForm, setEmailForm] = useState({ to: "", cc: "", bcc: "", subject: "", content: "" })
    const [isNewConversationDialogOpen, setIsNewConversationDialogOpen] = useState(false)
    const [newConversationTitle, setNewConversationTitle] = useState("")
    const [isMergeDialogOpen, setIsMergeDialogOpen] = useState(false)
    const [mergeTargetId, setMergeTargetId] = useState("")

    // Conversation State
    const [selectedConversationId, setSelectedConversationId] = useState<string>("")
    const [viewMode, setViewMode] = useState<"chat" | "graph">("chat")

    // AI Chat State
    const [aiChats, setAiChats] = useState<AIChat[]>([
        { id: 'ai-1', title: 'General Chat', messages: [], createdAt: new Date().toISOString() }
    ])
    const [selectedAiChat, setSelectedAiChat] = useState<AIChat>(aiChats[0])
    const [aiViewMode, setAiViewMode] = useState<"chat" | "graph">("chat")

    useEffect(() => {
        if (friendId) {
            const friend = friends.find(f => f.id === friendId)
            if (friend) {
                setSelectedFriend(friend)
                // Only change conversation if the currently selected one is not part of this friend's conversations
                // This prevents resetting to the first conversation when sending a message (which updates 'friends')
                const isCurrentConversationValid = friend.conversations.some(c => c.id === selectedConversationId)
                if (!isCurrentConversationValid && friend.conversations.length > 0) {
                    setSelectedConversationId(friend.conversations[0].id)
                }
            }
        }
    }, [friendId, friends, selectedConversationId])

    useEffect(() => {
        if (friendScrollRef.current) {
            friendScrollRef.current.scrollTop = friendScrollRef.current.scrollHeight
        }
    }, [selectedFriend, selectedConversationId, viewMode])

    useEffect(() => {
        if (aiScrollRef.current) {
            aiScrollRef.current.scrollTop = aiScrollRef.current.scrollHeight
        }
    }, [selectedAiChat, aiViewMode])

    const handleSendToFriend = async () => {
        if (newMessage.trim() && !sending && selectedFriend && selectedConversationId) {
            setSending(true)
            const newMsg: Message = {
                id: `m${Date.now()}`,
                text: newMessage,
                sender: "me",
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                timestamp: Date.now(),
                branchId: selectedConversationId // Add branchId for graph view compatibility
            }

            const updateFriendConversations = (friend: Friend) => {
                return friend.conversations.map((c) =>
                    c.id === selectedConversationId
                        ? { ...c, messages: [...c.messages, newMsg] }
                        : c
                )
            }

            setFriends(prevFriends =>
                prevFriends.map(f =>
                    f.id === selectedFriend.id
                        ? { ...f, conversations: updateFriendConversations(f), lastMessage: newMessage }
                        : f
                )
            )
            setSelectedFriend((prev) =>
                prev ? { ...prev, conversations: updateFriendConversations(prev), lastMessage: newMessage } : prev
            )
            setNewMessage("")
            setSending(false)
        }
    }

    const handleSendToAI = async () => {
        if (aiMessage.trim() && !aiLoading) {
            setAiLoading(true)
            const userMsg = { role: 'user' as const, content: aiMessage, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }), timestamp: Date.now() }

            const updatedChat = { ...selectedAiChat, messages: [...selectedAiChat.messages, userMsg] }
            setAiChats(prev => prev.map(c => c.id === selectedAiChat.id ? updatedChat : c))
            setSelectedAiChat(updatedChat)

            setAiMessage("")

            // Simulate AI response
            setTimeout(() => {
                const aiResponse = { role: 'ai' as const, content: "I'm a simulated AI response. How can I help you further?", time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }), timestamp: Date.now() }
                const chatWithAi = { ...updatedChat, messages: [...updatedChat.messages, aiResponse] }
                setAiChats(prev => prev.map(c => c.id === selectedAiChat.id ? chatWithAi : c))
                setSelectedAiChat(chatWithAi)
                setAiLoading(false)
            }, 1000)
        }
    }

    const handleDeleteMessage = (msgId: string) => {
        if (selectedFriend && selectedConversationId) {
            const updateConversations = (friend: any) => friend.conversations.map((c: any) =>
                c.id === selectedConversationId
                    ? { ...c, messages: c.messages.filter((m: any) => m.id !== msgId) }
                    : c
            )

            setFriends(prev => prev.map(f => f.id === selectedFriend.id ? { ...f, conversations: updateConversations(f) } : f))
            setSelectedFriend((prev: any) => prev ? { ...prev, conversations: updateConversations(prev) } : prev)
        }
    }

    const handleClearConversation = () => {
        if (selectedFriend && selectedConversationId) {
            const updateConversations = (friend: any) => friend.conversations.map((c: any) =>
                c.id === selectedConversationId ? { ...c, messages: [] } : c
            )
            setFriends(prev => prev.map(f => f.id === selectedFriend.id ? { ...f, conversations: updateConversations(f) } : f))
            setSelectedFriend((prev: any) => prev ? { ...prev, conversations: updateConversations(prev) } : prev)
        }
    }

    const handleEditMessage = (msg: Message) => {
        setEditingMessage({ id: msg.id, content: msg.text })
    }

    const handleSaveEditedMessage = () => {
        if (editingMessage && selectedFriend && selectedConversationId) {
            const updateConversations = (friend: any) => friend.conversations.map((c: any) =>
                c.id === selectedConversationId
                    ? { ...c, messages: c.messages.map((m: any) => m.id === editingMessage.id ? { ...m, text: editingMessage.content } : m) }
                    : c
            )
            setFriends(prev => prev.map(f => f.id === selectedFriend.id ? { ...f, conversations: updateConversations(f) } : f))
            setSelectedFriend((prev: any) => prev ? { ...prev, conversations: updateConversations(prev) } : prev)
            setEditingMessage(null)
        }
    }

    const handleSendEditedToFriend = () => {
        if (editingMessage && selectedFriend && selectedConversationId) {
            const newMsg: Message = {
                id: `m${Date.now()}`,
                text: editingMessage.content,
                sender: "me",
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                timestamp: Date.now(),
                branchId: selectedConversationId
            } as any

            const updateConversations = (friend: any) => friend.conversations.map((c: any) =>
                c.id === selectedConversationId
                    ? { ...c, messages: [...c.messages, newMsg] }
                    : c
            )

            setFriends(prev => prev.map(f => f.id === selectedFriend.id ? { ...f, conversations: updateConversations(f), lastMessage: editingMessage.content } : f))
            setSelectedFriend((prev: any) => prev ? { ...prev, conversations: updateConversations(prev), lastMessage: editingMessage.content } : prev)
            setEditingMessage(null)
        }
    }

    const handleForwardToSelectedFriend = (content: string) => {
        if (selectedFriend && selectedConversationId) {
            const newMsg: Message = {
                id: `m${Date.now()}`,
                text: content,
                sender: "me",
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                timestamp: Date.now(),
                branchId: selectedConversationId
            } as any

            const updateConversations = (friend: any) => friend.conversations.map((c: any) =>
                c.id === selectedConversationId
                    ? { ...c, messages: [...c.messages, newMsg] }
                    : c
            )

            setFriends(prev => prev.map(f => f.id === selectedFriend.id ? { ...f, conversations: updateConversations(f), lastMessage: content } : f))
            setSelectedFriend((prev: any) => prev ? { ...prev, conversations: updateConversations(prev), lastMessage: content } : prev)
        }
    }

    const handleEmailClick = (msg: Message) => {
        setEmailForm({ ...emailForm, content: msg.text })
        setEmailDialogOpen(true)
    }

    const handleSendEmail = () => {
        console.log("Sending email:", emailForm)
        setEmailDialogOpen(false)
        setEmailForm({ to: "", cc: "", bcc: "", subject: "", content: "" })
    }

    const handleCreateConversation = () => {
        if (newConversationTitle.trim() && selectedFriend) {
            const newConv: Conversation = {
                id: `c${Date.now()}`,
                title: newConversationTitle,
                messages: [],
                createdAt: new Date().toISOString().split('T')[0],
                status: 'active'
            }

            const updatedConversations = [...selectedFriend.conversations, newConv]

            setFriends(prev => prev.map(f => f.id === selectedFriend.id ? { ...f, conversations: updatedConversations } : f))
            setSelectedFriend((prev: any) => prev ? { ...prev, conversations: updatedConversations } : prev)
            setSelectedConversationId(newConv.id)
            setIsNewConversationDialogOpen(false)
            setNewConversationTitle("")
        }
    }

    const handleDeleteConversation = () => {
        if (selectedFriend && selectedConversationId) {
            const updatedConversations = selectedFriend.conversations.filter((c: any) => c.id !== selectedConversationId)

            if (updatedConversations.length === 0) {
                // Don't allow deleting the last conversation, or handle it gracefully
                // For now, let's just create a default one or prevent delete
                alert("Cannot delete the last conversation.")
                return
            }

            setFriends(prev => prev.map(f => f.id === selectedFriend.id ? { ...f, conversations: updatedConversations } : f))
            setSelectedFriend((prev: any) => prev ? { ...prev, conversations: updatedConversations } : prev)
            setSelectedConversationId(updatedConversations[0].id)
        }
    }

    const handleMergeConversation = () => {
        if (selectedFriend && selectedConversationId && mergeTargetId && selectedConversationId !== mergeTargetId) {
            const sourceConv = selectedFriend.conversations.find((c: any) => c.id === selectedConversationId)
            const targetConv = selectedFriend.conversations.find((c: any) => c.id === mergeTargetId)

            if (sourceConv && targetConv) {
                // 1. Mark source as merged
                // 2. Move messages to target with origin tag
                // 3. Add merge commit

                const movedMessages = sourceConv.messages.map((m: any) => ({
                    ...m,
                    originalConversationId: sourceConv.id
                }))

                const mergeCommit: Message = {
                    id: `m-merge-${Date.now()}`,
                    text: `Merged branch '${sourceConv.title}' into '${targetConv.title}'`,
                    sender: "me",
                    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                    timestamp: Date.now(),
                    type: 'merge',
                    originalConversationId: targetConv.id,
                    mergeSourceId: sourceConv.id
                } as any

                const newTargetMessages = [...targetConv.messages, ...movedMessages, mergeCommit].sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0))

                const updatedConversations = selectedFriend.conversations.map((c: any) => {
                    if (c.id === mergeTargetId) {
                        return { ...c, messages: newTargetMessages }
                    }
                    if (c.id === selectedConversationId) {
                        return { ...c, status: 'merged' as const, mergedInto: mergeTargetId, messages: [] }
                    }
                    return c
                })

                setFriends(prev => prev.map(f => f.id === selectedFriend.id ? { ...f, conversations: updatedConversations } : f))
                setSelectedFriend((prev: any) => prev ? { ...prev, conversations: updatedConversations } : prev)
                setSelectedConversationId(mergeTargetId)
                setIsMergeDialogOpen(false)
                setMergeTargetId("")
            }
        }
    }


    const aiModels = ["GPT-4", "Claude 3.5 Sonnet", "Gemini Pro"]
    const [selectedAiModel, setSelectedAiModel] = useState(aiModels[0])

    const handleCreateAiChat = () => {
        const newChat: AIChat = {
            id: `ai-${Date.now()}`,
            title: `New Chat ${aiChats.length + 1}`,
            messages: [],
            createdAt: new Date().toISOString()
        }
        setAiChats([...aiChats, newChat])
        setSelectedAiChat(newChat)
    }

    const currentConversation = selectedFriend?.conversations.find((c: any) => c.id === selectedConversationId)

    // Prepare data for Graph View
    const friendGraphBranches: GraphBranch[] = selectedFriend ? selectedFriend.conversations.map((c: any, i: number) => ({
        id: c.id,
        title: c.title,
        color: ['#10b981', '#3b82f6', '#f59e0b', '#ec4899', '#8b5cf6'][i % 5],
        status: c.status,
        mergedInto: c.mergedInto
    })) : []

    const friendGraphMessages: GraphMessage[] = selectedFriend ? selectedFriend.conversations.flatMap((c: any) =>
        c.messages.map((m: any) => ({
            ...m,
            branchId: m.originalConversationId || c.id, // Use original ID if available (for merged msgs), else current conv ID
            sender: m.sender // Ensure sender is compatible
        }))
    ) : []

    const aiGraphBranches: GraphBranch[] = aiChats.map((c, i) => ({
        id: c.id,
        title: c.title,
        color: ['#8b5cf6', '#ec4899', '#f59e0b', '#3b82f6', '#10b981'][i % 5],
        status: 'active'
    }))

    const aiGraphMessages: GraphMessage[] = aiChats.flatMap(c =>
        c.messages.map(m => ({
            ...m,
            id: `msg-${m.timestamp}`, // Ensure ID exists
            text: m.content,
            sender: 'ai', // Placeholder, handled by role
            branchId: c.id,
            role: m.role
        }))
    ) as any // Casting because 'role' is specific to AI messages in our generic GraphMessage

    return (
        <div className="flex flex-1 h-[100svh] max-h-[100svh] overflow-hidden bg-slate-950">
            <ChatSidebar
                friends={friends}
                selectedFriendId={selectedFriend?.id}
                onSelectFriend={(friend) => {
                    setSelectedFriend(friend)
                    if (friend.conversations.length > 0) {
                        setSelectedConversationId(friend.conversations[0].id)
                    }
                    // Update URL
                    const params = new URLSearchParams(searchParams)
                    params.set("friendId", friend.id)
                    router.replace(`?${params.toString()}`)
                }}
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
                onNewConversation={() => { }} // Not used in sidebar currently
            />

            <div className="flex-1 flex">
                {/* Friend Chat Area */}
                <div className="flex-1 flex flex-col border-r border-slate-800 h-full overflow-hidden">
                    {selectedFriend ? (
                        <>
                            <header className="flex h-14 shrink-0 items-center justify-between px-4 border-b border-slate-800 bg-slate-900">
                                <div className="flex items-center gap-3">
                                    <SidebarTrigger />
                                    <Separator orientation="vertical" className="mr-2 h-4" />
                                    <div className="flex items-center gap-3">
                                        <Avatar className="h-8 w-8 cursor-pointer hover:opacity-80 transition-opacity" onClick={() => setProfileOpen(true)}>
                                            <AvatarImage src={selectedFriend.avatar} />
                                            <AvatarFallback>{selectedFriend.name[0]}</AvatarFallback>
                                        </Avatar>
                                        <div>
                                            {/* removed username as per user request */}
                                            <div className="flex items-center gap-2">
                                                <span className={`w-2 h-2 rounded-full ${selectedFriend.status === 'online' ? 'bg-emerald-500' : selectedFriend.status === 'away' ? 'bg-amber-500' : 'bg-slate-500'}`} />
                                                <span className="text-xs text-slate-400 capitalize">{selectedFriend.status}</span>
                                            </div>
                                        </div>
                                    </div>

                                    <Separator orientation="vertical" className="mx-2 h-4" />

                                    <Select value={selectedConversationId} onValueChange={setSelectedConversationId}>
                                        <SelectTrigger className="w-[130px] h-8 bg-slate-800 border-slate-700 text-white text-xs">
                                            <SelectValue placeholder="Select discussion" />
                                        </SelectTrigger>
                                        <SelectContent className="bg-slate-900 border-slate-700">
                                            {selectedFriend.conversations.filter((c: any) => c.status !== 'merged').map((conv: any) => (
                                                <SelectItem key={conv.id} value={conv.id} className="text-white focus:bg-slate-800 text-xs">
                                                    <div className="flex items-center justify-between w-full gap-2">
                                                        <span>{conv.title}</span>
                                                        <span className="text-[10px] text-slate-500">{conv.createdAt}</span>
                                                    </div>
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>

                                    <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-400 hover:text-white" onClick={() => setIsNewConversationDialogOpen(true)}>
                                        <Plus className="h-4 w-4" />
                                    </Button>
                                </div>
                                <div className="flex items-center gap-2">
                                    <ToggleGroup type="single" value={viewMode} onValueChange={(v) => v && setViewMode(v as any)} className="bg-slate-800 rounded-lg p-0.5">
                                        <ToggleGroupItem value="chat" size="sm" className="data-[state=on]:bg-slate-700 data-[state=on]:text-white text-slate-400 h-7 px-2">
                                            <MessageSquare className="h-4 w-4" />
                                        </ToggleGroupItem>
                                        <ToggleGroupItem value="graph" size="sm" className="data-[state=on]:bg-slate-700 data-[state=on]:text-white text-slate-400 h-7 px-2">
                                            <GitGraph className="h-4 w-4" />
                                        </ToggleGroupItem>
                                    </ToggleGroup>
                                    <Separator orientation="vertical" className="mx-2 h-4" />
                                    <DropdownMenu>
                                        <DropdownMenuTrigger asChild>
                                            <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-400 hover:text-white">
                                                <MoreVertical className="h-4 w-4" />
                                            </Button>
                                        </DropdownMenuTrigger>
                                        <DropdownMenuContent align="end" className="bg-slate-900 border-slate-800 text-white">
                                            <DropdownMenuItem onClick={() => setProfileOpen(true)} className="focus:bg-slate-800">
                                                <User className="mr-2 h-4 w-4" /> View Profile
                                            </DropdownMenuItem>
                                            <DropdownMenuItem onClick={handleClearConversation} className="focus:bg-slate-800 text-amber-500">
                                                <Trash2 className="mr-2 h-4 w-4" /> Clear History
                                            </DropdownMenuItem>
                                            <DropdownMenuItem onClick={handleDeleteConversation} className="focus:bg-slate-800 text-red-500">
                                                <Trash2 className="mr-2 h-4 w-4" /> Delete Discussion
                                            </DropdownMenuItem>
                                            <DropdownMenuItem onClick={() => setIsMergeDialogOpen(true)} className="focus:bg-slate-800 text-blue-400">
                                                <GitBranch className="mr-2 h-4 w-4" /> Merge Discussion
                                            </DropdownMenuItem>
                                        </DropdownMenuContent>
                                    </DropdownMenu>
                                </div>
                            </header>

                            <div className="flex-1 min-h-0 overflow-hidden">
                                {viewMode === 'chat' ? (
                                    <ScrollArea ref={friendScrollRef} className="h-full p-4 bg-slate-950">
                                        <div className="space-y-4">
                                            {currentConversation?.messages.map((msg: Message) => (
                                                <div key={msg.id} className={`flex ${msg.sender === "me" ? "justify-end" : "justify-start"}`}>
                                                    <div className={`flex gap-3 max-w-[80%] ${msg.sender === "me" ? "flex-row-reverse" : ""}`}>
                                                        <Avatar className="h-8 w-8 mt-1">
                                                            <AvatarImage src={msg.sender === "me" ? undefined : selectedFriend.avatar} />
                                                            <AvatarFallback className={msg.sender === "me" ? "bg-slate-700 text-white" : "bg-slate-800 text-slate-400"}>
                                                                {msg.sender === "me" ? "Me" : selectedFriend.name[0]}
                                                            </AvatarFallback>
                                                        </Avatar>
                                                        <div className={`group relative rounded-2xl px-4 py-2 ${msg.sender === "me" ? "bg-emerald-600 text-white" : "bg-slate-800 text-slate-200"}`}>
                                                            <p className="text-sm">{msg.text}</p>
                                                            <span className={`text-[10px] mt-1 block ${msg.sender === "me" ? "text-emerald-200" : "text-slate-400"}`}>
                                                                {msg.time}
                                                            </span>
                                                            <div className={`absolute top-2 ${msg.sender === "me" ? "-left-12" : "-right-12"} opacity-0 group-hover:opacity-100 transition-opacity flex gap-1`}>
                                                                {msg.sender === "me" && (
                                                                    <Button variant="ghost" size="icon" className="h-6 w-6 text-slate-400 hover:text-white" onClick={() => handleEditMessage(msg)}>
                                                                        <Edit3 className="h-3 w-3" />
                                                                    </Button>
                                                                )}
                                                                <Button variant="ghost" size="icon" className="h-6 w-6 text-slate-400 hover:text-white" onClick={() => handleDeleteMessage(msg.id)}>
                                                                    <Trash2 className="h-3 w-3" />
                                                                </Button>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                            {currentConversation?.messages.length === 0 && (
                                                <div className="text-center text-slate-500 mt-10">
                                                    <p>No messages yet in this discussion.</p>
                                                    <p className="text-xs">Start the conversation!</p>
                                                </div>
                                            )}
                                        </div>
                                    </ScrollArea>
                                ) : (
                                    <div className="h-full flex flex-col bg-slate-950">
                                        <div className="flex items-center justify-between px-6 py-3 border-b border-slate-900 bg-slate-900/50">
                                            <div className="flex items-center gap-2">
                                                <GitBranch className="h-4 w-4 text-slate-400" />
                                                <span className="text-xs font-medium text-slate-400">Network Graph</span>
                                            </div>
                                            <div className="flex gap-4 text-xs text-slate-500">
                                                {selectedFriend.conversations.filter((c: any) => c.status === 'active').map((conv: any, i: number) => (
                                                    <div key={conv.id} className="flex items-center gap-1.5">
                                                        <span className={`w-2 h-2 rounded-full`} style={{ backgroundColor: ['#10b981', '#3b82f6', '#f59e0b', '#ec4899', '#8b5cf6'][i % 5] }} />
                                                        <span className={selectedConversationId === conv.id ? "text-white font-medium" : ""}>{conv.title}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                        <ScrollArea className="flex-1">
                                            <div className="p-8">
                                                <GitGraphView
                                                    branches={friendGraphBranches}
                                                    messages={friendGraphMessages}
                                                    selectedBranchId={selectedConversationId}
                                                    onSelectBranch={setSelectedConversationId}
                                                    friendAvatar={selectedFriend.avatar}
                                                    friendName={selectedFriend.name}
                                                />
                                            </div>
                                        </ScrollArea>
                                    </div>
                                )}
                            </div>

                            <div className="shrink-0 p-4 bg-transparent">
                                <div className="flex items-end gap-2 bg-slate-800/50 p-2 rounded-xl border border-slate-700/50 focus-within:border-slate-600 transition-colors">
                                    <div className="flex gap-1 pb-1.5 pl-1">
                                        <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg">
                                            <Paperclip className="h-4 w-4" />
                                        </Button>
                                    </div>
                                    <Input
                                        placeholder={`Message ${selectedFriend.name}...`}
                                        value={newMessage}
                                        onChange={(e) => setNewMessage(e.target.value)}
                                        onKeyDown={(e) => { if (e.key === "Enter") handleSendToFriend() }}
                                        className="min-h-[44px] border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 px-2 text-slate-200 placeholder:text-slate-500"
                                    />
                                    <div className="flex gap-1 pb-1.5 pr-1">
                                        <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg">
                                            <Smile className="h-4 w-4" />
                                        </Button>
                                        <Button
                                            onClick={handleSendToFriend}
                                            disabled={!newMessage.trim() || sending}
                                            className="h-8 w-8 p-0 bg-gradient-to-tr from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white shadow-lg shadow-emerald-900/20 rounded-lg shrink-0"
                                        >
                                            {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                                        </Button>
                                    </div>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="flex-1 flex items-center justify-center text-slate-500">
                            <div className="text-center">
                                <MessageSquare className="h-10 w-10 mx-auto mb-2 opacity-50" />
                                <p>Select a friend to start chatting</p>
                            </div>
                        </div>
                    )}
                </div>

                {/* AI Assistant Panel */}
                <div className="flex-1 flex flex-col bg-slate-950 border-l border-slate-800 h-full overflow-hidden">
                    <header className="flex h-14 shrink-0 items-center justify-between px-4 border-b border-slate-800 bg-slate-900">
                        <div className="flex items-center gap-2">
                            <Bot className="h-5 w-5 text-purple-400" />

                            <Select value={selectedAiChat.id} onValueChange={(v) => { const chat = aiChats.find(c => c.id === v); if (chat) setSelectedAiChat(chat) }}>
                                <SelectTrigger className="w-[140px] h-8 bg-slate-800 border-slate-700 text-white text-xs">
                                    <SelectValue placeholder="Select Chat" />
                                </SelectTrigger>
                                <SelectContent className="bg-slate-900 border-slate-700">
                                    {aiChats.map(chat => (
                                        <SelectItem key={chat.id} value={chat.id} className="text-white focus:bg-slate-800 text-xs">
                                            {chat.title}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>

                            <Select value={selectedAiModel} onValueChange={setSelectedAiModel}>
                                <SelectTrigger className="w-[130px] h-8 bg-slate-800 border-slate-700 text-white text-xs">
                                    <SelectValue placeholder="Model" />
                                </SelectTrigger>
                                <SelectContent className="bg-slate-900 border-slate-700">
                                    {aiModels.map(model => (
                                        <SelectItem key={model} value={model} className="text-white focus:bg-slate-800 text-xs">
                                            {model}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>

                            <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-400 hover:text-white" onClick={handleCreateAiChat}>
                                <Plus className="h-4 w-4" />
                            </Button>
                        </div>
                        <div className="flex items-center gap-2">
                            <ToggleGroup type="single" value={aiViewMode} onValueChange={(v) => v && setAiViewMode(v as any)} className="bg-slate-800 rounded-lg p-0.5">
                                <ToggleGroupItem value="chat" size="sm" className="data-[state=on]:bg-slate-700 data-[state=on]:text-white text-slate-400 h-7 px-2">
                                    <MessageSquare className="h-4 w-4" />
                                </ToggleGroupItem>
                                <ToggleGroupItem value="graph" size="sm" className="data-[state=on]:bg-slate-700 data-[state=on]:text-white text-slate-400 h-7 px-2">
                                    <GitGraph className="h-4 w-4" />
                                </ToggleGroupItem>
                            </ToggleGroup>
                        </div>
                    </header>

                    <div className="flex-1 min-h-0 overflow-hidden">
                        {aiViewMode === 'chat' ? (
                            <ScrollArea ref={aiScrollRef} className="h-full p-4">
                                <div className="space-y-4">
                                    {selectedAiChat.messages.map((msg, idx) => (
                                        <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                                            <div className={`flex gap-3 max-w-[85%] ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                                                <div className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 ${msg.role === "user" ? "bg-slate-700" : "bg-purple-900/50"}`}>
                                                    {msg.role === "user" ? <User className="h-4 w-4 text-white" /> : <Bot className="h-4 w-4 text-purple-400" />}
                                                </div>
                                                <div className={`rounded-2xl px-4 py-3 ${msg.role === "user" ? "bg-slate-800 text-white" : "bg-purple-900/20 text-slate-200 border border-purple-500/20"}`}>
                                                    <p className="text-sm leading-relaxed">{msg.content}</p>
                                                    <div className="flex items-center gap-2 mt-2">
                                                        <span className="text-[10px] text-slate-500">{msg.time}</span>
                                                        {msg.role === "ai" && (
                                                            <div className="flex gap-1">
                                                                <Button variant="ghost" size="icon" className="h-4 w-4 text-slate-500 hover:text-white" onClick={() => handleForwardToSelectedFriend(msg.content)}>
                                                                    <Send className="h-3 w-3" />
                                                                </Button>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                    {aiLoading && (
                                        <div className="flex justify-start">
                                            <div className="bg-slate-800 rounded-2xl px-4 py-3 border border-slate-700"><Loader2 className="h-4 w-4 animate-spin text-slate-400" /></div>
                                        </div>
                                    )}
                                </div>
                            </ScrollArea>
                        ) : (
                            <div className="h-full flex flex-col">
                                <div className="flex items-center justify-between px-2 py-3 border-b border-slate-900 bg-slate-900/50 mb-4">
                                    <div className="flex items-center gap-2">
                                        <GitBranch className="h-4 w-4 text-slate-400" />
                                        <span className="text-xs font-medium text-slate-400">AI Network Graph</span>
                                    </div>
                                    <div className="flex gap-4 text-xs text-slate-500">
                                        {aiChats.map((chat, i) => (
                                            <div key={chat.id} className="flex items-center gap-1.5">
                                                <span className={`w-2 h-2 rounded-full`} style={{ backgroundColor: ['#8b5cf6', '#ec4899', '#f59e0b', '#3b82f6', '#10b981'][i % 5] }} />
                                                <span className={selectedAiChat.id === chat.id ? "text-white font-medium" : ""}>{chat.title}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                                <ScrollArea className="flex-1">
                                    <GitGraphView
                                        branches={aiGraphBranches}
                                        messages={aiGraphMessages}
                                        selectedBranchId={selectedAiChat.id}
                                        onSelectBranch={(id) => {
                                            const chat = aiChats.find(c => c.id === id)
                                            if (chat) setSelectedAiChat(chat)
                                        }}
                                    />
                                </ScrollArea>
                            </div>
                        )}
                    </div>

                    <div className="shrink-0 p-4 bg-transparent">
                        <div className="flex items-end gap-2 bg-slate-800/50 p-2 rounded-xl border border-slate-700/50 focus-within:border-slate-600 transition-colors">
                            <div className="flex gap-1 pb-1.5 pl-1">
                                <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg">
                                    <Paperclip className="h-4 w-4" />
                                </Button>
                            </div>
                            <Textarea
                                placeholder="Ask AI..."
                                value={aiMessage}
                                onChange={(e) => setAiMessage(e.target.value)}
                                onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSendToAI() } }}
                                disabled={aiLoading}
                                className="min-h-[44px] max-h-[120px] border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 px-2 py-3 text-slate-200 placeholder:text-slate-500 resize-none"
                            />
                            <div className="flex gap-1 pb-1.5 pr-1">
                                <Button
                                    onClick={handleSendToAI}
                                    disabled={aiLoading || !aiMessage.trim()}
                                    className="h-8 w-8 p-0 bg-gradient-to-tr from-purple-600 to-indigo-500 hover:from-purple-500 hover:to-indigo-400 text-white shadow-lg shadow-purple-900/20 rounded-lg shrink-0"
                                >
                                    {aiLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <ChatDialogs
                profileOpen={profileOpen}
                setProfileOpen={setProfileOpen}
                selectedFriend={selectedFriend || undefined}
                editingMessage={editingMessage}
                setEditingMessage={setEditingMessage}
                onSaveEditedMessage={handleSaveEditedMessage}
                onSendEditedToFriend={handleSendEditedToFriend}
                emailDialogOpen={emailDialogOpen}
                setEmailDialogOpen={setEmailDialogOpen}
                emailForm={emailForm}
                setEmailForm={setEmailForm}
                onSendEmail={handleSendEmail}
                isNewConversationDialogOpen={isNewConversationDialogOpen}
                setIsNewConversationDialogOpen={setIsNewConversationDialogOpen}
                newConversationTitle={newConversationTitle}
                setNewConversationTitle={setNewConversationTitle}
                onCreateConversation={handleCreateConversation}
                isMergeDialogOpen={isMergeDialogOpen}
                setIsMergeDialogOpen={setIsMergeDialogOpen}
                mergeTargetId={mergeTargetId}
                setMergeTargetId={setMergeTargetId}
                onMergeConversation={handleMergeConversation}
                selectedConversationId={selectedConversationId}
            />
        </div>
    )
}
