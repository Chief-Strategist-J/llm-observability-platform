"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { ChevronsUpDown, Plus, type LucideIcon } from "lucide-react"

import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuShortcut,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
    useSidebar,
} from "@/components/ui/sidebar"

interface Team {
    name: string
    logo: LucideIcon
    plan: string
}

export function TeamSwitcher({ teams }: { teams: Team[] }) {
    const router = useRouter()
    const { isMobile } = useSidebar()
    const [activeTeam, setActiveTeam] = React.useState<Team | null>(teams[0] || null)

    React.useEffect(() => {
        if (teams.length > 0 && (!activeTeam || teams[0].name !== activeTeam.name)) {
            setActiveTeam(teams[0])
        }
    }, [teams, activeTeam])

    if (!activeTeam) {
        return null
    }

    const Logo = activeTeam.logo

    return (
        <SidebarMenu>
            <SidebarMenuItem>
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <SidebarMenuButton
                            size="lg"
                            className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
                            suppressHydrationWarning
                        >
                            <div className="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg">
                                <Logo className="size-4" />
                            </div>
                            <div className="grid flex-1 text-left text-sm leading-tight">
                                <span className="truncate font-semibold">
                                    {activeTeam.name}
                                </span>
                                <span className="truncate text-xs">{activeTeam.plan}</span>
                            </div>
                            <ChevronsUpDown className="ml-auto" />
                        </SidebarMenuButton>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent
                        className="min-w-56 rounded-lg bg-slate-900 border-slate-700"
                        align="start"
                        side={isMobile ? "bottom" : "right"}
                        sideOffset={4}
                    >
                        <DropdownMenuLabel className="text-slate-400 text-xs">
                            Teams
                        </DropdownMenuLabel>
                        {teams.map((team, index) => {
                            const TeamLogo = team.logo
                            return (
                                <DropdownMenuItem
                                    key={team.name}
                                    onClick={() => setActiveTeam(team)}
                                    className="gap-2 p-2 cursor-pointer text-slate-300 focus:bg-slate-800 focus:text-white"
                                >
                                    <div className="flex size-6 items-center justify-center rounded-sm border border-slate-700 bg-slate-800">
                                        <TeamLogo className="size-4 shrink-0" />
                                    </div>
                                    {team.name}
                                    <DropdownMenuShortcut>⌘{index + 1}</DropdownMenuShortcut>
                                </DropdownMenuItem>
                            )
                        })}
                        <DropdownMenuSeparator className="bg-slate-700" />
                        <DropdownMenuItem
                            onClick={() => router.push('/dashboard/team')}
                            className="gap-2 p-2 cursor-pointer text-slate-300 focus:bg-slate-800 focus:text-white"
                        >
                            <div className="flex size-6 items-center justify-center rounded-md border border-slate-700 bg-slate-800">
                                <Plus className="size-4" />
                            </div>
                            <div className="font-medium">Add team</div>
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </SidebarMenuItem>
        </SidebarMenu>
    )
}

