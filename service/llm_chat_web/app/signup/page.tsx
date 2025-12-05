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
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Loader2, CheckCircle2, MessageSquare, Sparkles } from "lucide-react"

export default function SignupPage() {
    const router = useRouter()
    const [name, setName] = useState("")
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const [confirmPassword, setConfirmPassword] = useState("")
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState("")
    const [success, setSuccess] = useState(false)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsLoading(true)
        setError("")

        if (password !== confirmPassword) {
            setError("Passwords do not match")
            setIsLoading(false)
            return
        }

        if (password.length < 6) {
            setError("Password must be at least 6 characters")
            setIsLoading(false)
            return
        }

        try {
            const response = await fetch("/api/auth/signup", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, email, password, confirmPassword })
            })
            const data = await response.json()

            if (data.success) {
                setSuccess(true)
                setTimeout(() => router.push("/login"), 2000)
            } else {
                setError(data.message || "Signup failed")
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
                    <div className="absolute top-20 left-20 w-72 h-72 bg-emerald-500/10 rounded-full blur-3xl" />
                    <div className="absolute bottom-20 right-20 w-96 h-96 bg-green-500/10 rounded-full blur-3xl" />
                </div>
                <div className="relative z-10 flex flex-col justify-center px-12 text-white">
                    <div className="flex items-center gap-3 mb-8">
                        <div className="p-3 bg-gradient-to-br from-emerald-500 to-green-600 rounded-xl">
                            <MessageSquare className="h-8 w-8" />
                        </div>
                        <span className="text-2xl font-bold">LLM Chat</span>
                    </div>
                    <h1 className="text-4xl font-bold leading-tight mb-4">
                        Start your journey
                        <br />
                        <span className="bg-gradient-to-r from-emerald-400 to-green-500 bg-clip-text text-transparent">
                            with AI-Powered Tools
                        </span>
                    </h1>
                    <p className="text-lg text-slate-400 max-w-md">
                        Create your account and unlock powerful AI conversation management features.
                    </p>
                    <div className="mt-12 space-y-4">
                        <div className="flex items-center gap-3 text-slate-300">
                            <div className="p-2 bg-slate-800 rounded-lg">
                                <Sparkles className="h-5 w-5 text-emerald-400" />
                            </div>
                            <span>Free tier with essential features</span>
                        </div>
                        <div className="flex items-center gap-3 text-slate-300">
                            <div className="p-2 bg-slate-800 rounded-lg">
                                <Sparkles className="h-5 w-5 text-emerald-400" />
                            </div>
                            <span>No credit card required</span>
                        </div>
                        <div className="flex items-center gap-3 text-slate-300">
                            <div className="p-2 bg-slate-800 rounded-lg">
                                <Sparkles className="h-5 w-5 text-emerald-400" />
                            </div>
                            <span>Get started in seconds</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="flex-1 flex items-center justify-center p-8">
                <Card className="w-full max-w-md border-slate-800 bg-slate-900/50 backdrop-blur-xl">
                    <CardHeader className="space-y-1 pb-6">
                        <div className="lg:hidden flex items-center gap-2 mb-4">
                            <div className="p-2 bg-gradient-to-br from-emerald-500 to-green-600 rounded-lg">
                                <MessageSquare className="h-5 w-5 text-white" />
                            </div>
                            <span className="text-lg font-bold text-white">LLM Chat</span>
                        </div>
                        <CardTitle className="text-2xl font-bold tracking-tight text-white">Create an account</CardTitle>
                        <CardDescription className="text-slate-400">
                            Enter your information to get started
                        </CardDescription>
                    </CardHeader>
                    <form onSubmit={handleSubmit}>
                        <CardContent className="space-y-4">
                            {error && (
                                <Alert variant="destructive" className="border-red-900 bg-red-950/50 text-red-400">
                                    <AlertDescription>{error}</AlertDescription>
                                </Alert>
                            )}
                            {success && (
                                <Alert className="border-emerald-800 bg-emerald-950/50">
                                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                                    <AlertDescription className="text-emerald-400">
                                        Account created! Redirecting to login...
                                    </AlertDescription>
                                </Alert>
                            )}
                            <div className="space-y-2">
                                <Label htmlFor="name" className="text-sm font-medium text-slate-300">Full Name</Label>
                                <Input
                                    id="name"
                                    type="text"
                                    placeholder="John Doe"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    required
                                    disabled={isLoading || success}
                                    className="h-11 bg-slate-800 border-slate-700 text-white placeholder:text-slate-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="email" className="text-sm font-medium text-slate-300">Email</Label>
                                <Input
                                    id="email"
                                    type="email"
                                    placeholder="m@example.com"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    disabled={isLoading || success}
                                    className="h-11 bg-slate-800 border-slate-700 text-white placeholder:text-slate-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
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
                                    disabled={isLoading || success}
                                    className="h-11 bg-slate-800 border-slate-700 text-white placeholder:text-slate-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="confirm-password" className="text-sm font-medium text-slate-300">Confirm Password</Label>
                                <Input
                                    id="confirm-password"
                                    type="password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    required
                                    disabled={isLoading || success}
                                    className="h-11 bg-slate-800 border-slate-700 text-white placeholder:text-slate-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                                />
                            </div>
                            <Button
                                className="w-full h-11 bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white font-medium border-0"
                                size="lg"
                                type="submit"
                                disabled={isLoading || success}
                            >
                                {isLoading ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Creating account...
                                    </>
                                ) : (
                                    "Create Account"
                                )}
                            </Button>
                        </CardContent>
                    </form>
                    <CardFooter className="flex flex-col space-y-4 pt-2">
                        <div className="text-sm text-center text-slate-400">
                            Already have an account?{" "}
                            <Link href="/login" className="text-emerald-400 hover:text-emerald-300 font-medium">
                                Sign in
                            </Link>
                        </div>
                    </CardFooter>
                </Card>
            </div>
        </div>
    )
}
