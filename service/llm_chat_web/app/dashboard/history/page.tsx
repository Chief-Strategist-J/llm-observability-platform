"use client"

import { Clock, CheckCircle2, XCircle, AlertCircle } from "lucide-react"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"

const historyItems = [
    {
        id: 1,
        title: "API deployment completed",
        description: "Successfully deployed version 2.4.0 to production",
        timestamp: "2 hours ago",
        status: "success",
    },
    {
        id: 2,
        title: "Database backup scheduled",
        description: "Automated backup started at 2:00 AM",
        timestamp: "5 hours ago",
        status: "success",
    },
    {
        id: 3,
        title: "Failed authentication attempt",
        description: "Blocked suspicious login from unknown IP",
        timestamp: "8 hours ago",
        status: "error",
    },
    {
        id: 4,
        title: "High memory usage detected",
        description: "Server memory usage exceeded 85%",
        timestamp: "12 hours ago",
        status: "warning",
    },
    {
        id: 5,
        title: "New user registration",
        description: "User john.doe@example.com registered",
        timestamp: "1 day ago",
        status: "info",
    },
    {
        id: 6,
        title: "System update available",
        description: "Security patch version 1.2.3 is ready",
        timestamp: "1 day ago",
        status: "info",
    },
    {
        id: 7,
        title: "SSL certificate renewed",
        description: "SSL certificate valid for 365 days",
        timestamp: "2 days ago",
        status: "success",
    },
    {
        id: 8,
        title: "Payment processing error",
        description: "Transaction #12345 failed",
        timestamp: "2 days ago",
        status: "error",
    },
]

const getStatusIcon = (status: string) => {
    switch (status) {
        case "success":
            return <CheckCircle2 className="h-5 w-5 text-green-500" />
        case "error":
            return <XCircle className="h-5 w-5 text-red-500" />
        case "warning":
            return <AlertCircle className="h-5 w-5 text-yellow-500" />
        default:
            return <Clock className="h-5 w-5 text-blue-500" />
    }
}

const getStatusColor = (status: string) => {
    switch (status) {
        case "success":
            return "default"
        case "error":
            return "destructive"
        case "warning":
            return "outline"
        default:
            return "secondary"
    }
}

export default function HistoryPage() {
    return (
        <div className="flex flex-1 flex-col h-screen">
            <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
                <SidebarTrigger className="-ml-1" />
                <Separator orientation="vertical" className="mr-2 h-4" />
                <h1 className="text-lg font-semibold">History</h1>
            </header>

            <div className="flex-1 p-8">
                <Card>
                    <CardHeader>
                        <CardTitle>Activity Timeline</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <ScrollArea className="h-[600px] pr-4">
                            <div className="space-y-4">
                                {historyItems.map((item, index) => (
                                    <div key={item.id} className="flex gap-4">
                                        <div className="flex flex-col items-center">
                                            {getStatusIcon(item.status)}
                                            {index < historyItems.length - 1 && (
                                                <div className="w-px h-full bg-border mt-2" />
                                            )}
                                        </div>
                                        <div className="flex-1 pb-8">
                                            <div className="flex items-start justify-between">
                                                <div>
                                                    <h3 className="font-semibold">{item.title}</h3>
                                                    <p className="text-sm text-muted-foreground mt-1">
                                                        {item.description}
                                                    </p>
                                                </div>
                                                <Badge variant={getStatusColor(item.status) as any}>
                                                    {item.status}
                                                </Badge>
                                            </div>
                                            <p className="text-xs text-muted-foreground mt-2">
                                                {item.timestamp}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </ScrollArea>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
