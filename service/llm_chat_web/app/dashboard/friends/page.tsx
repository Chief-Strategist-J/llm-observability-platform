"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
    Users,
    Search,
    UserPlus,
    Check,
    X,
    Clock,
    MessageSquare,
    Sparkles,
    UserCheck,
    Send
} from "lucide-react"

const seedUsers = [
    { id: "u1", name: "Emma Watson", email: "emma@example.com", avatar: "/avatars/02.png", mutualFriends: 12 },
    { id: "u2", name: "John Smith", email: "john@example.com", avatar: "/avatars/03.png", mutualFriends: 8 },
    { id: "u3", name: "Sarah Connor", email: "sarah@example.com", avatar: "/avatars/04.png", mutualFriends: 5 },
    { id: "u4", name: "Michael Chen", email: "michael@example.com", avatar: "/avatars/05.png", mutualFriends: 3 },
    { id: "u5", name: "Lisa Park", email: "lisa@example.com", avatar: "/avatars/06.png", mutualFriends: 15 },
]

const seedFriends = [
    { id: "f1", name: "Jackson Lee", email: "jackson@example.com", avatar: "/avatars/02.png", status: "online", friendSince: "2024-06-15" },
    { id: "f2", name: "Sofia Davis", email: "sofia@example.com", avatar: "/avatars/03.png", status: "offline", friendSince: "2024-08-22" },
    { id: "f3", name: "Isabella Nguyen", email: "isabella@example.com", avatar: "/avatars/04.png", status: "away", friendSince: "2024-10-10" },
]

const seedPendingRequests = [
    { id: "r1", name: "Alex Johnson", email: "alex@example.com", avatar: "/avatars/05.png", sentAt: "2 hours ago", type: "received" },
    { id: "r2", name: "Maria Garcia", email: "maria@example.com", avatar: "/avatars/06.png", sentAt: "1 day ago", type: "received" },
]

const seedSentRequests = [
    { id: "s1", name: "David Kim", email: "david@example.com", avatar: "/avatars/07.png", sentAt: "3 hours ago" },
]

export default function FriendsPage() {
    const router = useRouter()
    const [searchQuery, setSearchQuery] = useState("")
    const [activeTab, setActiveTab] = useState("discover")
    const [users, setUsers] = useState(seedUsers)
    const [friends, setFriends] = useState(seedFriends)
    const [pendingRequests, setPendingRequests] = useState(seedPendingRequests)
    const [sentRequests, setSentRequests] = useState(seedSentRequests)
    const [sentToUsers, setSentToUsers] = useState<string[]>([])

    const filteredUsers = users.filter(u =>
        u.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        u.email.toLowerCase().includes(searchQuery.toLowerCase())
    )

    const handleMessageFriend = (friendId: string) => {
        router.push(`/dashboard/chat?friend=${friendId}`)
    }

    const handleSendRequest = (userId: string) => {
        setSentToUsers([...sentToUsers, userId])
    }

    const handleAcceptRequest = (requestId: string) => {
        const request = pendingRequests.find(r => r.id === requestId)
        if (request) {
            setFriends([...friends, {
                id: request.id,
                name: request.name,
                email: request.email,
                avatar: request.avatar,
                status: "online",
                friendSince: new Date().toISOString().split('T')[0]
            }])
            setPendingRequests(pendingRequests.filter(r => r.id !== requestId))
        }
    }

    const handleRejectRequest = (requestId: string) => {
        setPendingRequests(pendingRequests.filter(r => r.id !== requestId))
    }

    const getStatusColor = (status: string) => {
        switch (status) {
            case "online": return "bg-emerald-500"
            case "away": return "bg-amber-500"
            default: return "bg-slate-500"
        }
    }

    return (
        <div className="flex flex-1 flex-col h-screen bg-slate-950">
            <header className="sticky top-0 z-10 flex h-16 shrink-0 items-center gap-2 border-b border-slate-800 px-4 bg-slate-950/90 backdrop-blur-xl">
                <SidebarTrigger className="-ml-1 text-slate-400 hover:text-white" />
                <Separator orientation="vertical" className="mr-2 h-4 bg-slate-700" />
                <div className="flex items-center gap-3">
                    <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-emerald-500/20 to-green-600/20 flex items-center justify-center ring-1 ring-emerald-500/20">
                        <Users className="h-4 w-4 text-emerald-400" />
                    </div>
                    <div>
                        <h1 className="text-lg font-semibold text-white">Friends</h1>
                        <p className="text-xs text-slate-400">{friends.length} friends • {pendingRequests.length} pending</p>
                    </div>
                </div>
            </header>

            <div className="flex-1 flex overflow-hidden">
                <div className="flex-1 flex flex-col p-6">
                    <div className="mb-6">
                        <div className="relative max-w-md">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                            <Input
                                placeholder="Search users..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-9 bg-slate-800 border-slate-700 text-white placeholder:text-slate-500 focus:ring-emerald-500"
                            />
                        </div>
                    </div>

                    <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
                        <TabsList className="bg-slate-800/50 border border-slate-700 w-fit mb-6">
                            <TabsTrigger value="discover" className="gap-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-emerald-500 data-[state=active]:to-green-600 data-[state=active]:text-white text-slate-400">
                                <Sparkles className="h-3.5 w-3.5" />
                                Discover
                            </TabsTrigger>
                            <TabsTrigger value="requests" className="gap-2 data-[state=active]:bg-amber-600 data-[state=active]:text-white text-slate-400">
                                <Clock className="h-3.5 w-3.5" />
                                Requests
                                {pendingRequests.length > 0 && (
                                    <Badge className="ml-1 bg-amber-500 text-white text-xs px-1.5">{pendingRequests.length}</Badge>
                                )}
                            </TabsTrigger>
                            <TabsTrigger value="friends" className="gap-2 data-[state=active]:bg-cyan-600 data-[state=active]:text-white text-slate-400">
                                <UserCheck className="h-3.5 w-3.5" />
                                My Friends
                            </TabsTrigger>
                        </TabsList>

                        <TabsContent value="discover" className="flex-1 m-0">
                            <ScrollArea className="h-[calc(100vh-280px)]">
                                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                                    {filteredUsers.map((user) => (
                                        <Card key={user.id} className="border-slate-800 bg-slate-900/50 hover:bg-slate-800/50 transition-all">
                                            <CardContent className="p-4">
                                                <div className="flex items-center gap-4">
                                                    <Avatar className="h-12 w-12">
                                                        <AvatarImage src={user.avatar} />
                                                        <AvatarFallback className="bg-slate-700 text-white">{user.name[0]}</AvatarFallback>
                                                    </Avatar>
                                                    <div className="flex-1 min-w-0">
                                                        <p className="font-medium text-white truncate">{user.name}</p>
                                                        <p className="text-xs text-slate-400 truncate">{user.email}</p>
                                                        <p className="text-xs text-slate-500 mt-1">{user.mutualFriends} mutual friends</p>
                                                    </div>
                                                </div>
                                                <div className="mt-4">
                                                    {sentToUsers.includes(user.id) ? (
                                                        <Button disabled className="w-full bg-slate-700 text-slate-400">
                                                            <Clock className="h-4 w-4 mr-2" />
                                                            Request Sent
                                                        </Button>
                                                    ) : (
                                                        <Button
                                                            onClick={() => handleSendRequest(user.id)}
                                                            className="w-full bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white"
                                                        >
                                                            <UserPlus className="h-4 w-4 mr-2" />
                                                            Add Friend
                                                        </Button>
                                                    )}
                                                </div>
                                            </CardContent>
                                        </Card>
                                    ))}
                                </div>
                            </ScrollArea>
                        </TabsContent>

                        <TabsContent value="requests" className="flex-1 m-0">
                            <ScrollArea className="h-[calc(100vh-280px)]">
                                <div className="space-y-6">
                                    {pendingRequests.length > 0 && (
                                        <div>
                                            <h3 className="text-sm font-medium text-white mb-4 flex items-center gap-2">
                                                <Clock className="h-4 w-4 text-amber-400" />
                                                Pending Requests ({pendingRequests.length})
                                            </h3>
                                            <div className="space-y-3">
                                                {pendingRequests.map((request) => (
                                                    <Card key={request.id} className="border-slate-800 bg-slate-900/50">
                                                        <CardContent className="p-4">
                                                            <div className="flex items-center gap-4">
                                                                <Avatar className="h-12 w-12">
                                                                    <AvatarImage src={request.avatar} />
                                                                    <AvatarFallback className="bg-slate-700 text-white">{request.name[0]}</AvatarFallback>
                                                                </Avatar>
                                                                <div className="flex-1 min-w-0">
                                                                    <p className="font-medium text-white">{request.name}</p>
                                                                    <p className="text-xs text-slate-400">{request.email}</p>
                                                                    <p className="text-xs text-slate-500 mt-1">Sent {request.sentAt}</p>
                                                                </div>
                                                                <div className="flex gap-2">
                                                                    <Button
                                                                        size="sm"
                                                                        onClick={() => handleAcceptRequest(request.id)}
                                                                        className="bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white"
                                                                    >
                                                                        <Check className="h-4 w-4" />
                                                                    </Button>
                                                                    <Button
                                                                        size="sm"
                                                                        variant="ghost"
                                                                        onClick={() => handleRejectRequest(request.id)}
                                                                        className="text-slate-400 hover:text-white hover:bg-slate-700"
                                                                    >
                                                                        <X className="h-4 w-4" />
                                                                    </Button>
                                                                </div>
                                                            </div>
                                                        </CardContent>
                                                    </Card>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {sentRequests.length > 0 && (
                                        <div>
                                            <h3 className="text-sm font-medium text-white mb-4 flex items-center gap-2">
                                                <Send className="h-4 w-4 text-cyan-400" />
                                                Sent Requests ({sentRequests.length})
                                            </h3>
                                            <div className="space-y-3">
                                                {sentRequests.map((request) => (
                                                    <Card key={request.id} className="border-slate-800 bg-slate-900/50">
                                                        <CardContent className="p-4">
                                                            <div className="flex items-center gap-4">
                                                                <Avatar className="h-12 w-12">
                                                                    <AvatarImage src={request.avatar} />
                                                                    <AvatarFallback className="bg-slate-700 text-white">{request.name[0]}</AvatarFallback>
                                                                </Avatar>
                                                                <div className="flex-1 min-w-0">
                                                                    <p className="font-medium text-white">{request.name}</p>
                                                                    <p className="text-xs text-slate-400">{request.email}</p>
                                                                    <p className="text-xs text-slate-500 mt-1">Sent {request.sentAt}</p>
                                                                </div>
                                                                <Badge variant="outline" className="text-slate-400 border-slate-600">
                                                                    <Clock className="h-3 w-3 mr-1" />
                                                                    Pending
                                                                </Badge>
                                                            </div>
                                                        </CardContent>
                                                    </Card>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {pendingRequests.length === 0 && sentRequests.length === 0 && (
                                        <div className="text-center py-12">
                                            <div className="p-4 bg-slate-800 rounded-full w-fit mx-auto mb-4">
                                                <Clock className="h-12 w-12 text-slate-500" />
                                            </div>
                                            <h3 className="text-lg font-semibold text-white mb-2">No pending requests</h3>
                                            <p className="text-sm text-slate-400">Friend requests will appear here</p>
                                        </div>
                                    )}
                                </div>
                            </ScrollArea>
                        </TabsContent>

                        <TabsContent value="friends" className="flex-1 m-0">
                            <ScrollArea className="h-[calc(100vh-280px)]">
                                {friends.length === 0 ? (
                                    <div className="text-center py-12">
                                        <div className="p-4 bg-slate-800 rounded-full w-fit mx-auto mb-4">
                                            <Users className="h-12 w-12 text-slate-500" />
                                        </div>
                                        <h3 className="text-lg font-semibold text-white mb-2">No friends yet</h3>
                                        <p className="text-sm text-slate-400 mb-4">Start by discovering new people to connect with</p>
                                        <Button
                                            onClick={() => setActiveTab("discover")}
                                            className="bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white"
                                        >
                                            <Sparkles className="h-4 w-4 mr-2" />
                                            Discover People
                                        </Button>
                                    </div>
                                ) : (
                                    <div className="space-y-3">
                                        {friends.map((friend) => (
                                            <Card key={friend.id} className="border-slate-800 bg-slate-900/50 hover:bg-slate-800/50 transition-all">
                                                <CardContent className="p-4">
                                                    <div className="flex items-center gap-4">
                                                        <div className="relative">
                                                            <Avatar className="h-12 w-12">
                                                                <AvatarImage src={friend.avatar} />
                                                                <AvatarFallback className="bg-slate-700 text-white">{friend.name[0]}</AvatarFallback>
                                                            </Avatar>
                                                            <span className={`absolute bottom-0 right-0 h-3 w-3 rounded-full ${getStatusColor(friend.status)} ring-2 ring-slate-900`} />
                                                        </div>
                                                        <div className="flex-1 min-w-0">
                                                            <p className="font-medium text-white">{friend.name}</p>
                                                            <p className="text-xs text-slate-400">{friend.email}</p>
                                                            <p className="text-xs text-slate-500 mt-1 capitalize">{friend.status} • Friends since {friend.friendSince}</p>
                                                        </div>
                                                        <Button
                                                            size="sm"
                                                            onClick={() => handleMessageFriend(friend.id)}
                                                            className="bg-cyan-600 hover:bg-cyan-700 text-white font-medium shadow-lg shadow-cyan-500/20"
                                                        >
                                                            <MessageSquare className="h-4 w-4 mr-2" />
                                                            Message
                                                        </Button>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        ))}
                                    </div>
                                )}
                            </ScrollArea>
                        </TabsContent>
                    </Tabs>
                </div>
            </div>
        </div>
    )
}
