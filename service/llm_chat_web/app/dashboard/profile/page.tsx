"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/hooks/use-auth"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Loader2, CheckCircle2, User, Mail, Shield, Lock, Pencil } from "lucide-react"

export default function ProfilePage() {
    const { user, refreshSession } = useAuth()
    const [name, setName] = useState("")
    const [currentPassword, setCurrentPassword] = useState("")
    const [newPassword, setNewPassword] = useState("")
    const [confirmPassword, setConfirmPassword] = useState("")
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState("")
    const [success, setSuccess] = useState("")

    useEffect(() => {
        if (user) {
            setName(user.name)
        }
    }, [user])

    const handleUpdateProfile = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsLoading(true)
        setError("")
        setSuccess("")

        try {
            const response = await fetch("/api/user/profile", {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name })
            })
            const data = await response.json()

            if (data.success) {
                setSuccess("Profile updated successfully")
                await refreshSession()
            } else {
                setError(data.message || "Update failed")
            }
        } catch {
            setError("Network error. Please try again.")
        } finally {
            setIsLoading(false)
        }
    }

    const handleChangePassword = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsLoading(true)
        setError("")
        setSuccess("")

        if (newPassword !== confirmPassword) {
            setError("Passwords do not match")
            setIsLoading(false)
            return
        }

        if (newPassword.length < 6) {
            setError("Password must be at least 6 characters")
            setIsLoading(false)
            return
        }

        try {
            const response = await fetch("/api/user/profile", {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ currentPassword, newPassword })
            })
            const data = await response.json()

            if (data.success) {
                setSuccess("Password changed successfully")
                setCurrentPassword("")
                setNewPassword("")
                setConfirmPassword("")
            } else {
                setError(data.message || "Password change failed")
            }
        } catch {
            setError("Network error. Please try again.")
        } finally {
            setIsLoading(false)
        }
    }

    const getInitials = (name: string) => {
        return name
            .split(" ")
            .map((n) => n[0])
            .join("")
            .toUpperCase()
            .slice(0, 2)
    }

    return (
        <div className="flex flex-1 flex-col h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
            <header className="flex h-16 shrink-0 items-center gap-2 border-b bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl px-4">
                <SidebarTrigger className="-ml-1" />
                <Separator orientation="vertical" className="mr-2 h-4" />
                <h1 className="text-lg font-semibold">Profile</h1>
            </header>

            <div className="flex-1 p-8 overflow-auto">
                <div className="max-w-4xl mx-auto space-y-6">
                    {error && (
                        <Alert variant="destructive" className="animate-in fade-in-0 slide-in-from-top-1">
                            <AlertDescription>{error}</AlertDescription>
                        </Alert>
                    )}
                    {success && (
                        <Alert className="border-emerald-500 bg-emerald-50 dark:bg-emerald-950 animate-in fade-in-0 slide-in-from-top-1">
                            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                            <AlertDescription className="text-emerald-700 dark:text-emerald-300">
                                {success}
                            </AlertDescription>
                        </Alert>
                    )}

                    <Card className="border-0 shadow-xl bg-gradient-to-br from-violet-600 via-purple-600 to-indigo-700 text-white overflow-hidden relative">
                        <div className="absolute inset-0 opacity-20">
                            <div className="absolute top-10 left-10 w-40 h-40 bg-white/20 rounded-full blur-3xl" />
                            <div className="absolute bottom-10 right-10 w-60 h-60 bg-purple-300/30 rounded-full blur-3xl" />
                        </div>
                        <CardHeader className="relative z-10">
                            <div className="flex items-center gap-6">
                                <Avatar className="h-24 w-24 border-4 border-white/20 shadow-xl">
                                    <AvatarImage src={user?.avatar} alt={user?.name} />
                                    <AvatarFallback className="text-2xl bg-white/20 text-white">
                                        {user?.name ? getInitials(user.name) : "U"}
                                    </AvatarFallback>
                                </Avatar>
                                <div>
                                    <CardTitle className="text-3xl font-bold">{user?.name}</CardTitle>
                                    <CardDescription className="flex items-center gap-2 mt-2 text-white/80">
                                        <Mail className="h-4 w-4" />
                                        {user?.email}
                                    </CardDescription>
                                    <Badge
                                        className={`mt-3 ${user?.role === "admin"
                                            ? "bg-amber-500/20 text-amber-200 border-amber-400/30"
                                            : "bg-white/20 text-white border-white/30"}`}
                                    >
                                        <Shield className="h-3 w-3 mr-1" />
                                        {user?.role?.toUpperCase()}
                                    </Badge>
                                </div>
                            </div>
                        </CardHeader>
                    </Card>

                    <div className="grid gap-6 md:grid-cols-2">
                        <Card className="border-0 shadow-lg bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2 text-lg">
                                    <div className="p-2 bg-violet-100 dark:bg-violet-900/30 rounded-lg">
                                        <Pencil className="h-4 w-4 text-violet-600" />
                                    </div>
                                    Personal Information
                                </CardTitle>
                                <CardDescription>
                                    Update your personal details
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                <form onSubmit={handleUpdateProfile} className="space-y-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="name" className="text-sm font-medium">Full Name</Label>
                                        <Input
                                            id="name"
                                            value={name}
                                            onChange={(e) => setName(e.target.value)}
                                            disabled={isLoading}
                                            className="h-11 bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-violet-500 focus:border-transparent"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="email" className="text-sm font-medium">Email</Label>
                                        <Input
                                            id="email"
                                            value={user?.email || ""}
                                            disabled
                                            className="h-11 bg-slate-100 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700"
                                        />
                                        <p className="text-xs text-muted-foreground">
                                            Email cannot be changed
                                        </p>
                                    </div>
                                    <Button
                                        type="submit"
                                        disabled={isLoading}
                                        className="w-full h-11 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white font-medium shadow-lg shadow-violet-500/25"
                                    >
                                        {isLoading ? (
                                            <>
                                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                Saving...
                                            </>
                                        ) : (
                                            "Save Changes"
                                        )}
                                    </Button>
                                </form>
                            </CardContent>
                        </Card>

                        <Card className="border-0 shadow-lg bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2 text-lg">
                                    <div className="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
                                        <Lock className="h-4 w-4 text-amber-600" />
                                    </div>
                                    Change Password
                                </CardTitle>
                                <CardDescription>
                                    Keep your account secure
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                <form onSubmit={handleChangePassword} className="space-y-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="current-password" className="text-sm font-medium">Current Password</Label>
                                        <Input
                                            id="current-password"
                                            type="password"
                                            value={currentPassword}
                                            onChange={(e) => setCurrentPassword(e.target.value)}
                                            disabled={isLoading}
                                            className="h-11 bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="new-password" className="text-sm font-medium">New Password</Label>
                                        <Input
                                            id="new-password"
                                            type="password"
                                            value={newPassword}
                                            onChange={(e) => setNewPassword(e.target.value)}
                                            disabled={isLoading}
                                            className="h-11 bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="confirm-new-password" className="text-sm font-medium">Confirm Password</Label>
                                        <Input
                                            id="confirm-new-password"
                                            type="password"
                                            value={confirmPassword}
                                            onChange={(e) => setConfirmPassword(e.target.value)}
                                            disabled={isLoading}
                                            className="h-11 bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                                        />
                                    </div>
                                    <Button
                                        type="submit"
                                        disabled={isLoading}
                                        className="w-full h-11 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white font-medium shadow-lg shadow-amber-500/25"
                                    >
                                        {isLoading ? (
                                            <>
                                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                Updating...
                                            </>
                                        ) : (
                                            "Change Password"
                                        )}
                                    </Button>
                                </form>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </div>
        </div>
    )
}
