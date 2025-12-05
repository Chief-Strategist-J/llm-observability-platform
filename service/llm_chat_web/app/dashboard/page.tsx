"use client"

import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { MessageSquare, Activity, Network, History, Users, Sparkles } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function DashboardPage() {
    return (
        <div className="flex flex-1 flex-col min-h-screen bg-slate-950">
            <header className="sticky top-0 z-10 flex h-16 shrink-0 items-center gap-2 border-b border-slate-800 px-4 bg-slate-950/90 backdrop-blur-xl">
                <SidebarTrigger className="-ml-1 text-slate-400 hover:text-white" />
                <Separator orientation="vertical" className="mr-2 h-4 bg-slate-700" />
                <h1 className="text-lg font-semibold text-white">Dashboard</h1>
            </header>
            <div className="flex-1 p-8">
                <div className="mb-8">
                    <div className="inline-flex items-center gap-2 bg-slate-800/50 text-cyan-400 px-4 py-2 rounded-full text-sm font-medium mb-4 border border-slate-700">
                        <Sparkles className="h-4 w-4" />
                        Welcome to your workspace
                    </div>
                    <h2 className="text-3xl font-bold tracking-tight text-white">Welcome back!</h2>
                    <p className="text-slate-400 mt-2">
                        Here's an overview of your available features
                    </p>
                </div>

                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <Card className="group border-slate-800 bg-slate-900/50 hover:bg-slate-800/50 transition-all duration-300 hover:-translate-y-1">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium text-slate-300">
                                Direct Chat
                            </CardTitle>
                            <div className="p-2 bg-gradient-to-br from-cyan-500/20 to-blue-600/20 rounded-lg group-hover:scale-110 transition-transform">
                                <MessageSquare className="h-4 w-4 text-cyan-400" />
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-white">Chat</div>
                            <p className="text-xs text-slate-500 mt-1">
                                One-on-one messaging with friends
                            </p>
                            <Link href="/dashboard/chat">
                                <Button variant="link" className="p-0 h-auto mt-3 text-cyan-400 hover:text-cyan-300 font-medium">
                                    View →
                                </Button>
                            </Link>
                        </CardContent>
                    </Card>

                    <Card className="group border-slate-800 bg-slate-900/50 hover:bg-slate-800/50 transition-all duration-300 hover:-translate-y-1">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium text-slate-300">
                                Friends
                            </CardTitle>
                            <div className="p-2 bg-gradient-to-br from-emerald-500/20 to-green-600/20 rounded-lg group-hover:scale-110 transition-transform">
                                <Users className="h-4 w-4 text-emerald-400" />
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-white">Connect</div>
                            <p className="text-xs text-slate-500 mt-1">
                                Manage friend requests
                            </p>
                            <Link href="/dashboard/friends">
                                <Button variant="link" className="p-0 h-auto mt-3 text-emerald-400 hover:text-emerald-300 font-medium">
                                    View →
                                </Button>
                            </Link>
                        </CardContent>
                    </Card>

                    <Card className="group border-slate-800 bg-slate-900/50 hover:bg-slate-800/50 transition-all duration-300 hover:-translate-y-1">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium text-slate-300">
                                Group Discussions
                            </CardTitle>
                            <div className="p-2 bg-gradient-to-br from-violet-500/20 to-purple-600/20 rounded-lg group-hover:scale-110 transition-transform">
                                <MessageSquare className="h-4 w-4 text-violet-400" />
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-white">Community</div>
                            <p className="text-xs text-slate-500 mt-1">
                                Threaded conversations
                            </p>
                            <Link href="/dashboard/group-chat">
                                <Button variant="link" className="p-0 h-auto mt-3 text-violet-400 hover:text-violet-300 font-medium">
                                    View →
                                </Button>
                            </Link>
                        </CardContent>
                    </Card>

                    <Card className="group border-slate-800 bg-slate-900/50 hover:bg-slate-800/50 transition-all duration-300 hover:-translate-y-1">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium text-slate-300">
                                Activity Flow
                            </CardTitle>
                            <div className="p-2 bg-gradient-to-br from-amber-500/20 to-orange-600/20 rounded-lg group-hover:scale-110 transition-transform">
                                <Activity className="h-4 w-4 text-amber-400" />
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-white">Workflows</div>
                            <p className="text-xs text-slate-500 mt-1">
                                Build and connect
                            </p>
                            <Link href="/dashboard/activity">
                                <Button variant="link" className="p-0 h-auto mt-3 text-amber-400 hover:text-amber-300 font-medium">
                                    View →
                                </Button>
                            </Link>
                        </CardContent>
                    </Card>
                </div>

                <div className="mt-8">
                    <Card className="border-slate-800 bg-slate-900/50">
                        <CardHeader>
                            <CardTitle className="text-white">Recent Activity</CardTitle>
                            <CardDescription className="text-slate-400">Your latest interactions and updates</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <div className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-800/50 transition-colors">
                                    <div className="p-2 bg-slate-800 rounded-lg">
                                        <History className="h-4 w-4 text-cyan-400" />
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-sm font-medium text-white">Workflow Created</p>
                                        <p className="text-xs text-slate-500">Activity flow with 5 nodes</p>
                                    </div>
                                    <span className="text-xs text-slate-500">2h ago</span>
                                </div>
                                <div className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-800/50 transition-colors">
                                    <div className="p-2 bg-slate-800 rounded-lg">
                                        <MessageSquare className="h-4 w-4 text-emerald-400" />
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-sm font-medium text-white">New Message</p>
                                        <p className="text-xs text-slate-500">From Jackson Lee</p>
                                    </div>
                                    <span className="text-xs text-slate-500">4h ago</span>
                                </div>
                                <div className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-800/50 transition-colors">
                                    <div className="p-2 bg-slate-800 rounded-lg">
                                        <Network className="h-4 w-4 text-amber-400" />
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-sm font-medium text-white">Network Status</p>
                                        <p className="text-xs text-slate-500">All systems operational</p>
                                    </div>
                                    <span className="text-xs text-slate-500">6h ago</span>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    )
}

