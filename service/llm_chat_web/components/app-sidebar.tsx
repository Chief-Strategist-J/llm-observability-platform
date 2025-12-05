"use client"

import * as React from "react"
import {
    Bot,
    Building2,
    GalleryVerticalEnd,
    MessageSquare,
    SquareTerminal,
    Users,
} from "lucide-react"

import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarHeader,
    SidebarRail,
} from "@/components/ui/sidebar"
import { NavMain } from "@/components/nav-main"
import { NavUser } from "@/components/nav-user"
import { TeamSwitcher } from "@/components/team-switcher"
import { useAuth } from "@/hooks/use-auth"

const navItems = [
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
        title: "Friends",
        url: "/dashboard/friends",
        icon: Users,
        items: [
            {
                title: "Discover",
                url: "/dashboard/friends",
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
        title: "Team",
        url: "/dashboard/team",
        icon: Building2,
        items: [
            {
                title: "Manage Teams",
                url: "/dashboard/team",
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
        ],
    },
]

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
    const { user, company } = useAuth()

    const userData = {
        name: user?.name || "User",
        email: user?.email || "",
        avatar: user?.avatar || "",
    }

    const teams = company
        ? [
            {
                name: company.name,
                logo: GalleryVerticalEnd,
                plan: company.plan.charAt(0).toUpperCase() + company.plan.slice(1),
            },
        ]
        : [
            {
                name: "Personal",
                logo: GalleryVerticalEnd,
                plan: "Free",
            },
        ]

    return (
        <Sidebar collapsible="icon" {...props}>
            <SidebarHeader>
                <TeamSwitcher teams={teams} />
            </SidebarHeader>
            <SidebarContent>
                <NavMain items={navItems} />
            </SidebarContent>
            <SidebarFooter>
                <NavUser user={userData} />
            </SidebarFooter>
            <SidebarRail />
        </Sidebar>
    )
}
