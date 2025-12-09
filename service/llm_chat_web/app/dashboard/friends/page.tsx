"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
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
    Send,
    Loader2
} from "lucide-react"
import {
    searchUsersAction,
    getFriendsAction,
    getPendingRequestsAction,
    getSentRequestsAction,
    sendFriendRequestAction,
    acceptFriendRequestAction,
    rejectFriendRequestAction
} from "./actions"
import { PublicUser, FriendRequestUI } from "@/database/types/user-types"
import { toast } from "sonner"

export default function FriendsPage() {
    const router = useRouter()
    const [searchQuery, setSearchQuery] = useState("")
    const [activeTab, setActiveTab] = useState("friends")
    const [friends, setFriends] = useState<PublicUser[]>([])
    const [searchResults, setSearchResults] = useState<PublicUser[]>([])
    const [pendingRequests, setPendingRequests] = useState<FriendRequestUI[]>([])
    const [sentRequests, setSentRequests] = useState<FriendRequestUI[]>([])
    const [loading, setLoading] = useState(true)
    const [searching, setSearching] = useState(false)

    const fetchInitialData = async () => {
        setLoading(true)
        try {
            const [friendsData, pendingData, sentData, initialDiscover] = await Promise.all([
                getFriendsAction(),
                getPendingRequestsAction(),
                getSentRequestsAction(),
                searchUsersAction("")
            ])
            setFriends(friendsData)
            setPendingRequests(pendingData)
            setSentRequests(sentData)
            setSearchResults(initialDiscover)
        } catch (error) {
            console.error("Failed to fetch friends data", error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchInitialData()
    }, [])

    useEffect(() => {
        const search = async () => {
            if (searchQuery.trim().length > 1) {
                setSearching(true)
                try {
                    const results = await searchUsersAction(searchQuery)
                    setSearchResults(results)
                } catch (error) {
                    console.error(error)
                } finally {
                    setSearching(false)
                }
            } else if (searchQuery.trim().length === 0) {
                // Reset to initial state or fetch default if needed, currently we handled initial load
                const results = await searchUsersAction("")
                setSearchResults(results)
            } else {
                setSearchResults([])
            }
        }

        const timeout = setTimeout(search, 500)
        return () => clearTimeout(timeout)
    }, [searchQuery])

    const handleMessageFriend = (friendId: string) => {
        router.push(`/dashboard/chat?friendId=${friendId}`)
    }

    const handleSendRequest = async (userId: string) => {
        const result = await sendFriendRequestAction(userId)
        if (result.success) {
            toast.success("Friend Request Sent", { description: "Waiting for them to accept." })
            const sData = await getSentRequestsAction()
            setSentRequests(sData)
            // Remove from search results to give immediate feedback or update button state
            setSearchResults(prev => prev.filter(u => u.id !== userId))
        } else {
            toast.error("Failed", { description: result.message || "Could not send request" })
        }
    }

    const handleAcceptRequest = async (requestId: string) => {
        const result = await acceptFriendRequestAction(requestId)
        if (result.success) {
            toast.success("Friend Added", { description: "You can now chat with them." })
            // Refresh friends and requests
            const [fData, pData] = await Promise.all([getFriendsAction(), getPendingRequestsAction()])
            setFriends(fData)
            setPendingRequests(pData)
        }
    }

    const handleRejectRequest = async (requestId: string) => {
        const result = await rejectFriendRequestAction(requestId)
        if (result.success) {
            setPendingRequests(prev => prev.filter(r => r._id?.toString() !== requestId)) // Optimistic update
        }
    }

    const getStatusColor = (status: string = "offline") => {
        // In a real app, this would come from presence service
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
                        <p className="text-xs text-slate-400">Manage connections</p>
                    </div>
                </div>
            </header>

            <div className="flex-1 flex overflow-hidden">
                <div className="flex-1 flex flex-col p-6">
                    <div className="mb-6">
                        <div className="relative max-w-md">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                            <Input
                                placeholder="Search new people..."
                                value={searchQuery}
                                onChange={(e) => { setSearchQuery(e.target.value); if (activeTab !== 'discover') setActiveTab('discover'); }}
                                className="pl-9 bg-slate-800 border-slate-700 text-white placeholder:text-slate-500 focus:ring-emerald-500"
                            />
                            {searching && <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-emerald-500" />}
                        </div>
                    </div>

                    <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
                        <TabsList className="bg-slate-800/50 border border-slate-700 w-fit mb-6">
                            <TabsTrigger value="friends" className="gap-2 data-[state=active]:bg-cyan-600 data-[state=active]:text-white text-slate-400">
                                <UserCheck className="h-3.5 w-3.5" />
                                My Friends
                                <Badge className="ml-1 bg-slate-700 text-white text-xs px-1.5">{friends.length}</Badge>
                            </TabsTrigger>
                            <TabsTrigger value="requests" className="gap-2 data-[state=active]:bg-amber-600 data-[state=active]:text-white text-slate-400">
                                <Clock className="h-3.5 w-3.5" />
                                Requests
                                {pendingRequests.length > 0 && (
                                    <Badge className="ml-1 bg-amber-500 text-white text-xs px-1.5">{pendingRequests.length}</Badge>
                                )}
                            </TabsTrigger>
                            <TabsTrigger value="discover" className="gap-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-emerald-500 data-[state=active]:to-green-600 data-[state=active]:text-white text-slate-400">
                                <Sparkles className="h-3.5 w-3.5" />
                                Discover
                            </TabsTrigger>
                        </TabsList>

                        <TabsContent value="discover" className="flex-1 m-0">
                            <ScrollArea className="h-[calc(100vh-280px)]">
                                {searchResults.length === 0 && !searching && searchQuery.trim().length > 0 ? (
                                    <div className="text-center py-12 text-slate-500">
                                        <p>No users found matching "{searchQuery}"</p>
                                    </div>
                                ) : (
                                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                                        {searchResults.map((user) => (
                                            <Card key={user.id} className="border-slate-800 bg-slate-900/50 hover:bg-slate-800/50 transition-all">
                                                <CardContent className="p-4">
                                                    <div className="flex items-center gap-4">
                                                        <Avatar className="h-12 w-12">
                                                            <AvatarImage src={user.avatar} />
                                                            <AvatarFallback className="bg-slate-700 text-white uppercase">{user.name[0]}</AvatarFallback>
                                                        </Avatar>
                                                        <div className="flex-1 min-w-0">
                                                            <p className="font-medium text-white truncate">{user.name}</p>
                                                            <p className="text-xs text-slate-400 truncate">{user.email}</p>
                                                        </div>
                                                    </div>
                                                    <div className="mt-4">
                                                        <Button
                                                            onClick={() => handleSendRequest(user.id)}
                                                            className="w-full bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white"
                                                        >
                                                            <UserPlus className="h-4 w-4 mr-2" />
                                                            Add Friend
                                                        </Button>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        ))}

                                        {searchResults.length === 0 && !searching && searchQuery.trim().length === 0 && (
                                            <div className="col-span-full text-center py-8 text-slate-500">
                                                <Sparkles className="h-10 w-10 mx-auto mb-2 opacity-20" />
                                                <p>No new people to discover right now.</p>
                                            </div>
                                        )}
                                    </div>
                                )}
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
                                                    <Card key={request._id!.toString()} className="border-slate-800 bg-slate-900/50">
                                                        <CardContent className="p-4">
                                                            <div className="flex items-center gap-4">
                                                                <Avatar className="h-12 w-12">
                                                                    <AvatarImage src={request.fromUser?.avatar} />
                                                                    <AvatarFallback className="bg-slate-700 text-white uppercase">{request.fromUser?.name[0]}</AvatarFallback>
                                                                </Avatar>
                                                                <div className="flex-1 min-w-0">
                                                                    <p className="font-medium text-white">{request.fromUser?.name}</p>
                                                                    <p className="text-xs text-slate-400">{request.fromUser?.email}</p>
                                                                    <p className="text-xs text-slate-500 mt-1">Sent: {new Date(request.createdAt).toLocaleDateString()}</p>
                                                                </div>
                                                                <div className="flex gap-2">
                                                                    <Button
                                                                        size="sm"
                                                                        onClick={() => handleAcceptRequest(request._id!.toString())}
                                                                        className="bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white"
                                                                    >
                                                                        <Check className="h-4 w-4" />
                                                                    </Button>
                                                                    <Button
                                                                        size="sm"
                                                                        variant="ghost"
                                                                        onClick={() => handleRejectRequest(request._id!.toString())}
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
                                                    <Card key={request._id!.toString()} className="border-slate-800 bg-slate-900/50">
                                                        <CardContent className="p-4">
                                                            <div className="flex items-center gap-4">
                                                                <Avatar className="h-12 w-12">
                                                                    <AvatarImage src={request.toUser?.avatar} />
                                                                    <AvatarFallback className="bg-slate-700 text-white uppercase">{request.toUser?.name[0]}</AvatarFallback>
                                                                </Avatar>
                                                                <div className="flex-1 min-w-0">
                                                                    <p className="font-medium text-white">{request.toUser?.name}</p>
                                                                    <p className="text-xs text-slate-400">{request.toUser?.email}</p>
                                                                    <p className="text-xs text-slate-500 mt-1">Sent: {new Date(request.createdAt).toLocaleDateString()}</p>
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
                                {loading ? (
                                    <div className="flex justify-center p-8">
                                        <Loader2 className="h-8 w-8 animate-spin text-slate-500" />
                                    </div>
                                ) : friends.length === 0 ? (
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
                                                                <AvatarFallback className="bg-slate-700 text-white uppercase">{friend.name[0]}</AvatarFallback>
                                                            </Avatar>
                                                            <span className={`absolute bottom-0 right-0 h-3 w-3 rounded-full ${getStatusColor()} ring-2 ring-slate-900`} />
                                                        </div>
                                                        <div className="flex-1 min-w-0">
                                                            <p className="font-medium text-white">{friend.name}</p>
                                                            <p className="text-xs text-slate-400">{friend.email}</p>
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
