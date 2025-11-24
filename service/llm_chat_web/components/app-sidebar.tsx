"use client"

import * as React from "react"
import {
    AudioWaveform,
    BookOpen,
    Bot,
    Command,
    Frame,
    GalleryVerticalEnd,
    Map,
    MessageSquare,
    PieChart,
    SquareTerminal,
} from "lucide-react"

import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarHeader,
    SidebarRail,
} from "@/components/ui/sidebar"
import { NavMain } from "@/components/nav-main"
import { NavProjects } from "@/components/nav-projects"
import { NavUser } from "@/components/nav-user"
import { TeamSwitcher } from "@/components/team-switcher"

const data = {
    user: {
        name: "shadcn",
        email: "m@example.com",
        avatar: "/avatars/shadcn.jpg",
    },
    teams: [
        {
            name: "Acme Inc",
            logo: GalleryVerticalEnd,
            plan: "Enterprise",
        },
        {
            name: "Acme Corp.",
            logo: AudioWaveform,
            plan: "Startup",
        },
        {
            name: "Evil Corp.",
            logo: Command,
            plan: "Free",
        },
    ],
    navMain: [
        {
            title: "Dashboard",
            url: "/dashboard",
            icon: SquareTerminal,
            isActive: true,
            items: [
                {
                    title: "Overview",
                    url: "/dashboard",
                },
            ],
        },
        {
            title: "Chat",
            url: "/dashboard/chat",
            icon: MessageSquare,
            items: [
                {
                    title: "Direct Messages",
                    url: "/dashboard/chat",
                },
                {
                    title: "Group Discussions",
                    url: "/dashboard/group-chat",
                },
            ],
        },
        {
            title: "Activity",
            url: "/dashboard/activity",
            icon: Bot,
            items: [
                {
                    title: "Workflow",
                    url: "/dashboard/activity",
                },
                {
                    title: "History",
                    url: "/dashboard/history",
                },
            ],
        },
        {
            title: "Network",
            url: "/dashboard/network",
            icon: BookOpen,
            items: [
                {
                    title: "Overview",
                    url: "/dashboard/network",
                },
            ],
        },
    ],
    projects: [
        {
            name: "Chat Application",
            url: "/dashboard/chat",
            icon: Frame,
        },
        {
            name: "Analytics",
            url: "/dashboard",
            icon: PieChart,
        },
        {
            name: "Network Monitor",
            url: "/dashboard/network",
            icon: Map,
        },
    ],
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
    return (
        <Sidebar collapsible="icon" {...props}>
            <SidebarHeader>
                <TeamSwitcher teams={data.teams} />
            </SidebarHeader>
            <SidebarContent>
                <NavMain items={data.navMain} />
                <NavProjects projects={data.projects} />
            </SidebarContent>
            <SidebarFooter>
                <NavUser user={data.user} />
            </SidebarFooter>
            <SidebarRail />
        </Sidebar>
    )
}
