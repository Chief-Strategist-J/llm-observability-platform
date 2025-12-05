"use client"

import { Search, Plus } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Friend } from "./types"

interface ChatSidebarProps {
    friends: Friend[]
    selectedFriendId?: string
    onSelectFriend: (friend: Friend) => void
    searchQuery: string
    onSearchChange: (query: string) => void
    onNewConversation: () => void
}

export function ChatSidebar({
    friends,
    selectedFriendId,
    onSelectFriend,
    searchQuery,
    onSearchChange,
    onNewConversation
}: ChatSidebarProps) {
    const filteredFriends = friends.filter(friend =>
        friend.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        friend.email.toLowerCase().includes(searchQuery.toLowerCase())
    )

    return (
        <aside className="w-72 border-r border-slate-800 flex flex-col bg-slate-900">
            <div className="p-4 border-b border-slate-800">
                <div className="relative">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-slate-500" />
                    <Input
                        placeholder="Search friends..."
                        className="pl-8 bg-slate-800 border-slate-700 text-white placeholder:text-slate-500"
                        value={searchQuery}
                        onChange={(e) => onSearchChange(e.target.value)}
                    />
                </div>
            </div>
            <ScrollArea className="flex-1">
                <div className="p-2 space-y-1">
                    {filteredFriends.map((friend) => (
                        <button
                            key={friend.id}
                            onClick={() => onSelectFriend(friend)}
                            className={`w-full flex items-center gap-3 p-3 rounded-lg transition-colors ${selectedFriendId === friend.id
                                ? "bg-slate-800"
                                : "hover:bg-slate-800/50"
                                }`}
                        >
                            <div className="relative">
                                <Avatar>
                                    <AvatarImage src={friend.avatar} />
                                    <AvatarFallback>{friend.name[0]}</AvatarFallback>
                                </Avatar>
                                <span className={`absolute bottom-0 right-0 w-3 h-3 rounded-full border-2 border-slate-900 ${friend.status === 'online' ? 'bg-emerald-500' :
                                    friend.status === 'away' ? 'bg-amber-500' : 'bg-slate-500'
                                    }`} />
                            </div>
                            <div className="flex-1 text-left overflow-hidden">
                                <div className="flex items-center justify-between">
                                    <span className="font-medium text-white truncate">{friend.name}</span>
                                    <span className="text-xs text-slate-500">12:30 PM</span>
                                </div>
                                <p className="text-xs text-slate-400 truncate">{friend.lastMessage}</p>
                            </div>
                        </button>
                    ))}
                </div>
            </ScrollArea>
        </aside>
    )
}
