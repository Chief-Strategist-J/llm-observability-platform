"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Loader2, MessageSquare, Sparkles } from "lucide-react"

export default function LoginPage() {
    const router = useRouter()
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const [rememberMe, setRememberMe] = useState(false)
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState("")

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsLoading(true)
        setError("")

        try {
            const response = await fetch("/api/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password, rememberMe })
            })
            const data = await response.json()

            if (data.success) {
                router.push("/dashboard")
                router.refresh()
            } else {
                setError(data.message || "Login failed")
            }
        } catch {
            setError("Network error. Please try again.")
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="min-h-screen flex bg-slate-950">
            <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
                <div className="absolute inset-0">
                    <div className="absolute top-20 left-20 w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl" />
                    <div className="absolute bottom-20 right-20 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
                </div>
                <div className="relative z-10 flex flex-col justify-center px-12 text-white">
                    <div className="flex items-center gap-3 mb-8">
                        <div className="p-3 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl">
                            <MessageSquare className="h-8 w-8" />
                        </div>
                        <span className="text-2xl font-bold">LLM Chat</span>
                    </div>
                    <h1 className="text-4xl font-bold leading-tight mb-4">
                        Welcome to your
                        <br />
                        <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                            AI-Powered Dashboard
                        </span>
                    </h1>
                    <p className="text-lg text-slate-400 max-w-md">
                        Manage conversations, monitor activity, and analyze your AI workflows all in one place.
                    </p>
                    <div className="mt-12 space-y-4">
                        <div className="flex items-center gap-3 text-slate-300">
                            <div className="p-2 bg-slate-800 rounded-lg">
                                <Sparkles className="h-5 w-5 text-cyan-400" />
                            </div>
                            <span>Real-time AI conversation tracking</span>
                        </div>
                        <div className="flex items-center gap-3 text-slate-300">
                            <div className="p-2 bg-slate-800 rounded-lg">
                                <Sparkles className="h-5 w-5 text-cyan-400" />
                            </div>
                            <span>Advanced analytics and insights</span>
                        </div>
                        <div className="flex items-center gap-3 text-slate-300">
                            <div className="p-2 bg-slate-800 rounded-lg">
                                <Sparkles className="h-5 w-5 text-cyan-400" />
                            </div>
                            <span>Team collaboration features</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="flex-1 flex items-center justify-center p-8">
                <Card className="w-full max-w-md border-slate-800 bg-slate-900/50 backdrop-blur-xl">
                    <CardHeader className="space-y-1 pb-6">
                        <div className="lg:hidden flex items-center gap-2 mb-4">
                            <div className="p-2 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-lg">
                                <MessageSquare className="h-5 w-5 text-white" />
                            </div>
                            <span className="text-lg font-bold text-white">LLM Chat</span>
                        </div>
                        <CardTitle className="text-2xl font-bold tracking-tight text-white">Welcome back</CardTitle>
                        <CardDescription className="text-slate-400">
                            Enter your credentials to access your account
                        </CardDescription>
                    </CardHeader>
                    <form onSubmit={handleSubmit}>
                        <CardContent className="space-y-4">
                            {error && (
                                <Alert variant="destructive" className="border-red-900 bg-red-950/50 text-red-400">
                                    <AlertDescription>{error}</AlertDescription>
                                </Alert>
                            )}
                            <div className="space-y-2">
                                <Label htmlFor="email" className="text-sm font-medium text-slate-300">Email</Label>
                                <Input
                                    id="email"
                                    type="email"
                                    placeholder="m@example.com"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    disabled={isLoading}
                                    className="h-11 bg-slate-800 border-slate-700 text-white placeholder:text-slate-500 focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="password" className="text-sm font-medium text-slate-300">Password</Label>
                                <Input
                                    id="password"
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    disabled={isLoading}
                                    className="h-11 bg-slate-800 border-slate-700 text-white placeholder:text-slate-500 focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                                />
                            </div>
                            <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-2">
                                    <Checkbox
                                        id="remember"
                                        checked={rememberMe}
                                        onCheckedChange={(checked) => setRememberMe(checked === true)}
                                        disabled={isLoading}
                                        className="border-slate-600 data-[state=checked]:bg-cyan-500 data-[state=checked]:border-cyan-500"
                                    />
                                    <label
                                        htmlFor="remember"
                                        className="text-sm font-medium leading-none cursor-pointer text-slate-400"
                                    >
                                        Remember me
                                    </label>
                                </div>
                                <Link
                                    href="/forgot-password"
                                    className="text-sm text-cyan-400 hover:text-cyan-300 transition-colors"
                                >
                                    Forgot password?
                                </Link>
                            </div>
                            <Button
                                className="w-full h-11 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white font-medium border-0"
                                size="lg"
                                type="submit"
                                disabled={isLoading}
                            >
                                {isLoading ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Signing in...
                                    </>
                                ) : (
                                    "Sign in"
                                )}
                            </Button>
                        </CardContent>
                    </form>
                    <CardFooter className="flex flex-col space-y-4 pt-2">
                        <div className="text-sm text-center text-slate-400">
                            Don&apos;t have an account?{" "}
                            <Link href="/signup" className="text-cyan-400 hover:text-cyan-300 font-medium">
                                Sign up
                            </Link>
                        </div>
                    </CardFooter>
                </Card>
            </div>
        </div>
    )
}
