"use client"

import { useState } from "react"
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
import { ArrowLeft, Loader2, CheckCircle2, MessageSquare, Mail } from "lucide-react"

export default function ForgotPasswordPage() {
    const [email, setEmail] = useState("")
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState("")
    const [success, setSuccess] = useState(false)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsLoading(true)
        setError("")

        try {
            const response = await fetch("/api/auth/forgot-password", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email })
            })
            const data = await response.json()

            if (data.success) {
                setSuccess(true)
            } else {
                setError(data.message || "Request failed")
            }
        } catch {
            setError("Network error. Please try again.")
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center p-8 bg-slate-950 relative overflow-hidden">
            <div className="absolute inset-0">
                <div className="absolute top-20 left-20 w-72 h-72 bg-amber-500/10 rounded-full blur-3xl" />
                <div className="absolute bottom-20 right-20 w-96 h-96 bg-orange-500/10 rounded-full blur-3xl" />
            </div>

            <Card className="w-full max-w-md border-slate-800 bg-slate-900/50 backdrop-blur-xl relative z-10">
                <CardHeader className="space-y-1 pb-6 text-center">
                    <div className="mx-auto p-4 bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl mb-4">
                        <Mail className="h-8 w-8 text-white" />
                    </div>
                    <div className="flex items-center justify-center gap-2 mb-2">
                        <MessageSquare className="h-5 w-5 text-amber-400" />
                        <span className="text-sm font-medium text-slate-400">LLM Chat</span>
                    </div>
                    <CardTitle className="text-2xl font-bold tracking-tight text-white">Reset your password</CardTitle>
                    <CardDescription className="text-slate-400">
                        Enter your email and we&apos;ll send you a link to reset your password
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
                            <Alert className="border-amber-800 bg-amber-950/50">
                                <CheckCircle2 className="h-4 w-4 text-amber-400" />
                                <AlertDescription className="text-amber-400">
                                    If an account exists with this email, you will receive a password reset link.
                                </AlertDescription>
                            </Alert>
                        )}
                        <div className="space-y-2">
                            <Label htmlFor="email" className="text-sm font-medium text-slate-300">Email address</Label>
                            <Input
                                id="email"
                                type="email"
                                placeholder="m@example.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                disabled={isLoading || success}
                                className="h-11 bg-slate-800 border-slate-700 text-white placeholder:text-slate-500 focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                            />
                        </div>
                        <Button
                            className="w-full h-11 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white font-medium border-0"
                            size="lg"
                            type="submit"
                            disabled={isLoading || success}
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Sending...
                                </>
                            ) : (
                                "Send Reset Link"
                            )}
                        </Button>
                    </CardContent>
                </form>
                <CardFooter className="flex flex-col space-y-4 pt-2">
                    <Link
                        href="/login"
                        className="flex items-center justify-center gap-2 text-sm text-slate-400 hover:text-amber-400 transition-colors"
                    >
                        <ArrowLeft className="h-4 w-4" />
                        Back to login
                    </Link>
                </CardFooter>
            </Card>
        </div>
    )
}
