"use client"

import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { MessageSquare, Activity, Network, History } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function DashboardPage() {
    return (
        <div className="flex flex-1 flex-col">
            <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
                <SidebarTrigger className="-ml-1" />
                <Separator orientation="vertical" className="mr-2 h-4" />
                <h1 className="text-lg font-semibold">Dashboard</h1>
            </header>
            <div className="flex-1 p-8">
                <div className="mb-8">
                    <h2 className="text-3xl font-bold tracking-tight">Welcome back!</h2>
                    <p className="text-muted-foreground">
                        Here's an overview of your available features
                    </p>
                </div>

                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">
                                Direct Chat
                            </CardTitle>
                            <MessageSquare className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">Chat</div>
                            <p className="text-xs text-muted-foreground">
                                One-on-one messaging
                            </p>
                            <Link href="/dashboard/chat">
                                <Button variant="link" className="p-0 h-auto mt-2">View</Button>
                            </Link>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">
                                Group Discussions
                            </CardTitle>
                            <MessageSquare className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">Community</div>
                            <p className="text-xs text-muted-foreground">
                                Threaded conversations
                            </p>
                            <Link href="/dashboard/group-chat">
                                <Button variant="link" className="p-0 h-auto mt-2">View</Button>
                            </Link>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">
                                Activity Flow
                            </CardTitle>
                            <Activity className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">Workflows</div>
                            <p className="text-xs text-muted-foreground">
                                Build and connect
                            </p>
                            <Link href="/dashboard/activity">
                                <Button variant="link" className="p-0 h-auto mt-2">View</Button>
                            </Link>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">
                                Network Monitor
                            </CardTitle>
                            <Network className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">Network</div>
                            <p className="text-xs text-muted-foreground">
                                System overview
                            </p>
                            <Link href="/dashboard/network">
                                <Button variant="link" className="p-0 h-auto mt-2">View</Button>
                            </Link>
                        </CardContent>
                    </Card>
                </div>

                <div className="mt-8">
                    <Card>
                        <CardHeader>
                            <CardTitle>Recent Activity</CardTitle>
                            <CardDescription>Your latest interactions and updates</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <div className="flex items-center gap-3">
                                    <History className="h-4 w-4 text-muted-foreground" />
                                    <div className="flex-1">
                                        <p className="text-sm font-medium">Workflow Created</p>
                                        <p className="text-xs text-muted-foreground">Activity flow with 5 nodes</p>
                                    </div>
                                    <span className="text-xs text-muted-foreground">2h ago</span>
                                </div>
                                <div className="flex items-center gap-3">
                                    <MessageSquare className="h-4 w-4 text-muted-foreground" />
                                    <div className="flex-1">
                                        <p className="text-sm font-medium">New Message</p>
                                        <p className="text-xs text-muted-foreground">From Jackson Lee</p>
                                    </div>
                                    <span className="text-xs text-muted-foreground">4h ago</span>
                                </div>
                                <div className="flex items-center gap-3">
                                    <Network className="h-4 w-4 text-muted-foreground" />
                                    <div className="flex-1">
                                        <p className="text-sm font-medium">Network Status</p>
                                        <p className="text-xs text-muted-foreground">All systems operational</p>
                                    </div>
                                    <span className="text-xs text-muted-foreground">6h ago</span>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    )
}
