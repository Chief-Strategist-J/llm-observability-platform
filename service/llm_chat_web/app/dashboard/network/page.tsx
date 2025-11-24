"use client"

import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

const networkData = [
    { id: 1, name: "API Server", status: "active", connections: 45, latency: "12ms" },
    { id: 2, name: "Database", status: "active", connections: 32, latency: "5ms" },
    { id: 3, name: "Cache Server", status: "active", connections: 78, latency: "2ms" },
    { id: 4, name: "Web Server", status: "warning", connections: 120, latency: "45ms" },
    { id: 5, name: "Load Balancer", status: "active", connections: 156, latency: "8ms" },
    { id: 6, name: "Message Queue", status: "active", connections: 23, latency: "15ms" },
]

export default function NetworkPage() {
    return (
        <div className="flex flex-1 flex-col h-screen">
            <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
                <SidebarTrigger className="-ml-1" />
                <Separator orientation="vertical" className="mr-2 h-4" />
                <h1 className="text-lg font-semibold">Network</h1>
            </header>

            <div className="flex-1 p-8">
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {networkData.map((node) => (
                        <Card key={node.id}>
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <CardTitle className="text-sm font-medium">
                                        {node.name}
                                    </CardTitle>
                                    <Badge
                                        variant={node.status === "active" ? "default" : "destructive"}
                                    >
                                        {node.status}
                                    </Badge>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-2">
                                    <div className="flex justify-between">
                                        <span className="text-sm text-muted-foreground">Connections</span>
                                        <span className="text-sm font-medium">{node.connections}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-sm text-muted-foreground">Latency</span>
                                        <span className="text-sm font-medium">{node.latency}</span>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>

                <Card className="mt-6">
                    <CardHeader>
                        <CardTitle>Network Topology</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-center justify-center h-[400px] text-muted-foreground">
                            Network visualization placeholder
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
