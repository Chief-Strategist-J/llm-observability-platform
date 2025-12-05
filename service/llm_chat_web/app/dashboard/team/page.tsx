"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import {
    Users,
    Plus,
    Search,
    MoreVertical,
    Settings,
    Trash2,
    UserPlus,
    Crown,
    Shield,
    User,
    Mail,
    Building2,
    Calendar,
    Edit3,
    Check,
    X
} from "lucide-react"

interface TeamMember {
    id: string
    name: string
    email: string
    avatar: string
    role: "owner" | "admin" | "member"
    joinedDate: string
    status: "active" | "pending"
}

interface Team {
    id: string
    name: string
    description: string
    createdAt: string
    plan: "free" | "pro" | "enterprise"
    members: TeamMember[]
}

const initialTeams: Team[] = [
    {
        id: "t1",
        name: "Engineering",
        description: "Core development team for product features",
        createdAt: "Jan 2024",
        plan: "pro",
        members: [
            { id: "m1", name: "You", email: "you@company.com", avatar: "/avatars/01.png", role: "owner", joinedDate: "Jan 2024", status: "active" },
            { id: "m2", name: "Jackson Lee", email: "jackson@company.com", avatar: "/avatars/02.png", role: "admin", joinedDate: "Feb 2024", status: "active" },
            { id: "m3", name: "Sofia Davis", email: "sofia@company.com", avatar: "/avatars/03.png", role: "member", joinedDate: "Mar 2024", status: "active" },
            { id: "m4", name: "Isabella Nguyen", email: "isabella@company.com", avatar: "/avatars/04.png", role: "member", joinedDate: "Apr 2024", status: "pending" },
        ]
    },
    {
        id: "t2",
        name: "Design",
        description: "UI/UX design and brand identity",
        createdAt: "Feb 2024",
        plan: "free",
        members: [
            { id: "m5", name: "You", email: "you@company.com", avatar: "/avatars/01.png", role: "owner", joinedDate: "Feb 2024", status: "active" },
            { id: "m6", name: "William Kim", email: "william@company.com", avatar: "/avatars/05.png", role: "member", joinedDate: "Mar 2024", status: "active" },
        ]
    },
]

export default function TeamPage() {
    const router = useRouter()
    const [teams, setTeams] = useState<Team[]>(initialTeams)
    const [selectedTeam, setSelectedTeam] = useState<Team | null>(teams[0])
    const [searchQuery, setSearchQuery] = useState("")
    const [createDialogOpen, setCreateDialogOpen] = useState(false)
    const [inviteDialogOpen, setInviteDialogOpen] = useState(false)
    const [newTeam, setNewTeam] = useState({ name: "", description: "" })
    const [inviteEmail, setInviteEmail] = useState("")
    const [inviteRole, setInviteRole] = useState<"admin" | "member">("member")

    const getRoleIcon = (role: string) => {
        switch (role) {
            case "owner": return <Crown className="h-3 w-3 text-amber-400" />
            case "admin": return <Shield className="h-3 w-3 text-blue-400" />
            default: return <User className="h-3 w-3 text-slate-400" />
        }
    }

    const getRoleBadge = (role: string) => {
        switch (role) {
            case "owner": return "bg-amber-600/20 text-amber-400 border-amber-600/30"
            case "admin": return "bg-blue-600/20 text-blue-400 border-blue-600/30"
            default: return "bg-slate-600/20 text-slate-400 border-slate-600/30"
        }
    }

    const getPlanBadge = (plan: string) => {
        switch (plan) {
            case "enterprise": return "bg-purple-600/20 text-purple-400"
            case "pro": return "bg-emerald-600/20 text-emerald-400"
            default: return "bg-slate-600/20 text-slate-400"
        }
    }

    const handleCreateTeam = () => {
        if (newTeam.name.trim()) {
            const team: Team = {
                id: `t${Date.now()}`,
                name: newTeam.name,
                description: newTeam.description,
                createdAt: new Date().toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
                plan: "free",
                members: [{ id: "m1", name: "You", email: "you@company.com", avatar: "/avatars/01.png", role: "owner", joinedDate: new Date().toLocaleDateString('en-US', { month: 'short', year: 'numeric' }), status: "active" }]
            }
            setTeams([...teams, team])
            setSelectedTeam(team)
            setNewTeam({ name: "", description: "" })
            setCreateDialogOpen(false)
        }
    }

    const handleInviteMember = () => {
        if (inviteEmail.trim() && selectedTeam) {
            const newMember: TeamMember = {
                id: `m${Date.now()}`,
                name: inviteEmail.split('@')[0],
                email: inviteEmail,
                avatar: "",
                role: inviteRole,
                joinedDate: new Date().toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
                status: "pending"
            }
            setTeams(teams.map(t => t.id === selectedTeam.id ? { ...t, members: [...t.members, newMember] } : t))
            setSelectedTeam({ ...selectedTeam, members: [...selectedTeam.members, newMember] })
            setInviteEmail("")
            setInviteDialogOpen(false)
        }
    }

    const handleRemoveMember = (memberId: string) => {
        if (selectedTeam) {
            const updatedMembers = selectedTeam.members.filter(m => m.id !== memberId)
            setTeams(teams.map(t => t.id === selectedTeam.id ? { ...t, members: updatedMembers } : t))
            setSelectedTeam({ ...selectedTeam, members: updatedMembers })
        }
    }

    const handleDeleteTeam = () => {
        if (selectedTeam) {
            const updatedTeams = teams.filter(t => t.id !== selectedTeam.id)
            setTeams(updatedTeams)
            setSelectedTeam(updatedTeams[0] || null)
        }
    }

    const filteredMembers = selectedTeam?.members.filter(m =>
        m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        m.email.toLowerCase().includes(searchQuery.toLowerCase())
    ) || []

    const btnPrimary = "bg-slate-700 hover:bg-slate-600 text-white border-0"
    const btnSecondary = "bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600"
    const btnDanger = "bg-red-600 hover:bg-red-700 text-white"
    const btnSuccess = "bg-emerald-600 hover:bg-emerald-700 text-white"

    return (
        <div className="flex flex-1 flex-col h-screen bg-slate-950">
            <header className="sticky top-0 z-10 flex h-16 shrink-0 items-center gap-3 border-b border-slate-800 px-5 bg-slate-900">
                <SidebarTrigger className="text-slate-400 hover:text-white" />
                <Separator orientation="vertical" className="h-5 bg-slate-700" />
                <div className="flex items-center gap-3">
                    <div className="h-9 w-9 rounded-xl bg-slate-800 flex items-center justify-center">
                        <Building2 className="h-4 w-4 text-slate-300" />
                    </div>
                    <div>
                        <h1 className="text-base font-semibold text-white tracking-tight">Teams</h1>
                        <p className="text-xs text-slate-500">{teams.length} team(s)</p>
                    </div>
                </div>
                <div className="ml-auto">
                    <Button onClick={() => setCreateDialogOpen(true)} className="h-10 px-4 bg-slate-700 hover:bg-slate-600 text-white rounded-lg">
                        <Plus className="h-4 w-4 mr-2" /> New Team
                    </Button>
                </div>
            </header>

            <div className="flex-1 flex overflow-hidden">
                <aside className="w-72 border-r border-slate-800 flex flex-col bg-slate-900">
                    <div className="p-4 border-b border-slate-800">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                            <Input placeholder="Search teams..." className="pl-9 h-10 bg-slate-800 border-slate-700 text-sm text-white placeholder:text-slate-500 rounded-lg" />
                        </div>
                    </div>
                    <ScrollArea className="flex-1">
                        <div className="p-2">
                            {teams.map((team) => (
                                <div
                                    key={team.id}
                                    onClick={() => setSelectedTeam(team)}
                                    className={`flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all mb-1 ${selectedTeam?.id === team.id ? "bg-slate-800 ring-1 ring-slate-700" : "hover:bg-slate-800/50"}`}
                                >
                                    <div className="h-11 w-11 rounded-xl bg-slate-800 flex items-center justify-center text-white font-semibold">
                                        {team.name[0]}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-white truncate leading-tight">{team.name}</p>
                                        <p className="text-xs text-slate-500 mt-0.5 leading-tight">{team.members.length} members</p>
                                    </div>
                                    <Badge className={`text-[10px] ${getPlanBadge(team.plan)}`}>{team.plan}</Badge>
                                </div>
                            ))}
                        </div>
                    </ScrollArea>
                </aside>

                {selectedTeam ? (
                    <main className="flex-1 flex flex-col overflow-hidden">
                        <div className="p-6 border-b border-slate-800 bg-slate-900/50">
                            <div className="flex items-start justify-between">
                                <div className="flex items-center gap-4">
                                    <div className="h-16 w-16 rounded-xl bg-slate-800 flex items-center justify-center text-white text-2xl font-bold">
                                        {selectedTeam.name[0]}
                                    </div>
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <h2 className="text-xl font-bold text-white">{selectedTeam.name}</h2>
                                            <Badge className={`text-xs ${getPlanBadge(selectedTeam.plan)}`}>{selectedTeam.plan}</Badge>
                                        </div>
                                        <p className="text-sm text-slate-400 mt-1">{selectedTeam.description || "No description"}</p>
                                        <p className="text-xs text-slate-500 mt-2 flex items-center gap-1">
                                            <Calendar className="h-3 w-3" /> Created {selectedTeam.createdAt}
                                        </p>
                                    </div>
                                </div>
                                <DropdownMenu>
                                    <DropdownMenuTrigger asChild>
                                        <Button className={btnSecondary}><Settings className="h-4 w-4" /></Button>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent align="end" className="bg-slate-900 border-slate-700 w-48">
                                        <DropdownMenuItem className="text-slate-300 focus:bg-slate-800">
                                            <Edit3 className="h-4 w-4 mr-2" /> Edit Team
                                        </DropdownMenuItem>
                                        <DropdownMenuSeparator className="bg-slate-700" />
                                        <DropdownMenuItem onClick={handleDeleteTeam} className="text-red-400 focus:bg-slate-800">
                                            <Trash2 className="h-4 w-4 mr-2" /> Delete Team
                                        </DropdownMenuItem>
                                    </DropdownMenuContent>
                                </DropdownMenu>
                            </div>
                        </div>

                        <div className="p-6 flex-1 overflow-hidden flex flex-col">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                    <Users className="h-5 w-5 text-slate-400" /> Members ({selectedTeam.members.length})
                                </h3>
                                <div className="flex items-center gap-2">
                                    <div className="relative">
                                        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-500" />
                                        <Input
                                            placeholder="Search members..."
                                            value={searchQuery}
                                            onChange={(e) => setSearchQuery(e.target.value)}
                                            className="pl-8 h-8 w-48 text-sm bg-slate-800 border-slate-700 text-white placeholder:text-slate-500"
                                        />
                                    </div>
                                    <Button onClick={() => setInviteDialogOpen(true)} className={btnSuccess}>
                                        <UserPlus className="h-4 w-4 mr-2" /> Invite
                                    </Button>
                                </div>
                            </div>

                            <ScrollArea className="flex-1">
                                <div className="space-y-2">
                                    {filteredMembers.map((member) => (
                                        <Card key={member.id} className="bg-slate-900 border-slate-800">
                                            <CardContent className="p-4">
                                                <div className="flex items-center gap-4">
                                                    <Avatar className="h-12 w-12 ring-2 ring-slate-700">
                                                        <AvatarImage src={member.avatar} />
                                                        <AvatarFallback className="bg-slate-700 text-white">{member.name[0]}</AvatarFallback>
                                                    </Avatar>
                                                    <div className="flex-1">
                                                        <div className="flex items-center gap-2">
                                                            <p className="font-medium text-white">{member.name}</p>
                                                            <Badge className={`text-[10px] ${getRoleBadge(member.role)}`}>
                                                                {getRoleIcon(member.role)} <span className="ml-1 capitalize">{member.role}</span>
                                                            </Badge>
                                                            {member.status === "pending" && (
                                                                <Badge className="text-[10px] bg-amber-600/20 text-amber-400">Pending</Badge>
                                                            )}
                                                        </div>
                                                        <p className="text-sm text-slate-400">{member.email}</p>
                                                        <p className="text-xs text-slate-500 mt-1">Joined {member.joinedDate}</p>
                                                    </div>
                                                    {member.role !== "owner" && (
                                                        <DropdownMenu>
                                                            <DropdownMenuTrigger asChild>
                                                                <Button size="sm" className={btnSecondary}><MoreVertical className="h-4 w-4" /></Button>
                                                            </DropdownMenuTrigger>
                                                            <DropdownMenuContent align="end" className="bg-slate-900 border-slate-700">
                                                                <DropdownMenuItem className="text-slate-300 focus:bg-slate-800">
                                                                    <Shield className="h-4 w-4 mr-2" /> Change Role
                                                                </DropdownMenuItem>
                                                                <DropdownMenuSeparator className="bg-slate-700" />
                                                                <DropdownMenuItem onClick={() => handleRemoveMember(member.id)} className="text-red-400 focus:bg-slate-800">
                                                                    <Trash2 className="h-4 w-4 mr-2" /> Remove
                                                                </DropdownMenuItem>
                                                            </DropdownMenuContent>
                                                        </DropdownMenu>
                                                    )}
                                                </div>
                                            </CardContent>
                                        </Card>
                                    ))}
                                </div>
                            </ScrollArea>
                        </div>
                    </main>
                ) : (
                    <div className="flex-1 flex items-center justify-center">
                        <div className="text-center">
                            <div className="p-6 bg-slate-900 rounded-full w-fit mx-auto mb-4">
                                <Building2 className="h-12 w-12 text-slate-600" />
                            </div>
                            <h3 className="text-lg font-semibold text-white mb-2">No team selected</h3>
                            <p className="text-sm text-slate-500 mb-4">Select a team or create a new one</p>
                            <Button onClick={() => setCreateDialogOpen(true)} className={btnPrimary}>
                                <Plus className="h-4 w-4 mr-2" /> Create Team
                            </Button>
                        </div>
                    </div>
                )}
            </div>

            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
                <DialogContent className="bg-slate-900 border-slate-800 max-w-md">
                    <DialogHeader>
                        <DialogTitle className="text-white">Create New Team</DialogTitle>
                        <DialogDescription className="text-slate-400">Add a new team to collaborate with others</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                        <div>
                            <Label className="text-slate-300">Team Name *</Label>
                            <Input
                                value={newTeam.name}
                                onChange={(e) => setNewTeam({ ...newTeam, name: e.target.value })}
                                placeholder="e.g. Engineering"
                                className="mt-1.5 bg-slate-800 border-slate-700 text-white"
                            />
                        </div>
                        <div>
                            <Label className="text-slate-300">Description</Label>
                            <Textarea
                                value={newTeam.description}
                                onChange={(e) => setNewTeam({ ...newTeam, description: e.target.value })}
                                placeholder="What does this team do?"
                                className="mt-1.5 bg-slate-800 border-slate-700 text-white"
                            />
                        </div>
                        <DialogFooter>
                            <Button onClick={() => setCreateDialogOpen(false)} className={btnSecondary}>Cancel</Button>
                            <Button onClick={handleCreateTeam} disabled={!newTeam.name.trim()} className={btnSuccess}>Create Team</Button>
                        </DialogFooter>
                    </div>
                </DialogContent>
            </Dialog>

            <Dialog open={inviteDialogOpen} onOpenChange={setInviteDialogOpen}>
                <DialogContent className="bg-slate-900 border-slate-800 max-w-md">
                    <DialogHeader>
                        <DialogTitle className="text-white">Invite Member</DialogTitle>
                        <DialogDescription className="text-slate-400">Invite someone to join {selectedTeam?.name}</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                        <div>
                            <Label className="text-slate-300">Email Address *</Label>
                            <Input
                                value={inviteEmail}
                                onChange={(e) => setInviteEmail(e.target.value)}
                                placeholder="colleague@company.com"
                                className="mt-1.5 bg-slate-800 border-slate-700 text-white"
                            />
                        </div>
                        <div>
                            <Label className="text-slate-300">Role</Label>
                            <Select value={inviteRole} onValueChange={(v: "admin" | "member") => setInviteRole(v)}>
                                <SelectTrigger className="mt-1.5 bg-slate-800 border-slate-700 text-white">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent className="bg-slate-900 border-slate-700">
                                    <SelectItem value="member" className="text-white focus:bg-slate-800">Member</SelectItem>
                                    <SelectItem value="admin" className="text-white focus:bg-slate-800">Admin</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <DialogFooter>
                            <Button onClick={() => setInviteDialogOpen(false)} className={btnSecondary}>Cancel</Button>
                            <Button onClick={handleInviteMember} disabled={!inviteEmail.trim()} className={btnSuccess}>
                                <Mail className="h-4 w-4 mr-2" /> Send Invite
                            </Button>
                        </DialogFooter>
                    </div>
                </DialogContent>
            </Dialog>
        </div>
    )
}
