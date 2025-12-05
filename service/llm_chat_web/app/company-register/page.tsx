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
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Loader2, CheckCircle2, Building2, ArrowLeft, Sparkles, MessageSquare } from "lucide-react"

export default function CompanyRegisterPage() {
    const router = useRouter()
    const [name, setName] = useState("")
    const [plan, setPlan] = useState("free")
    const [address, setAddress] = useState("")
    const [phone, setPhone] = useState("")
    const [website, setWebsite] = useState("")
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState("")
    const [success, setSuccess] = useState(false)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsLoading(true)
        setError("")

        try {
            const response = await fetch("/api/company/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, plan, address, phone, website })
            })
            const data = await response.json()

            if (data.success) {
                setSuccess(true)
                setTimeout(() => router.push("/dashboard"), 2000)
            } else {
                if (response.status === 401) {
                    router.push("/login")
                    return
                }
                setError(data.message || "Registration failed")
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
                    <div className="absolute top-20 left-20 w-72 h-72 bg-indigo-500/10 rounded-full blur-3xl" />
                    <div className="absolute bottom-20 right-20 w-96 h-96 bg-violet-500/10 rounded-full blur-3xl" />
                </div>
                <div className="relative z-10 flex flex-col justify-center px-12 text-white">
                    <div className="flex items-center gap-3 mb-8">
                        <div className="p-3 bg-gradient-to-br from-indigo-500 to-violet-600 rounded-xl">
                            <MessageSquare className="h-8 w-8" />
                        </div>
                        <span className="text-2xl font-bold">LLM Chat</span>
                    </div>
                    <h1 className="text-4xl font-bold leading-tight mb-4">
                        Set up your
                        <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-200 to-yellow-400">
                            Company Profile
                        </span>
                    </h1>
                    <p className="text-lg text-white/80 max-w-md">
                        Register your company to unlock team features and manage your AI workspace.
                    </p>
                    <div className="mt-12 space-y-4">
                        <div className="flex items-center gap-3 text-slate-300">
                            <div className="p-2 bg-slate-800 rounded-lg">
                                <Sparkles className="h-5 w-5 text-indigo-400" />
                            </div>
                            <span>Invite unlimited team members</span>
                        </div>
                        <div className="flex items-center gap-3 text-slate-300">
                            <div className="p-2 bg-slate-800 rounded-lg">
                                <Sparkles className="h-5 w-5 text-indigo-400" />
                            </div>
                            <span>Centralized billing and management</span>
                        </div>
                        <div className="flex items-center gap-3 text-slate-300">
                            <div className="p-2 bg-slate-800 rounded-lg">
                                <Sparkles className="h-5 w-5 text-indigo-400" />
                            </div>
                            <span>Advanced analytics for your team</span>
                        </div>
                    </div>
                </div>
                <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-black/20 to-transparent" />
            </div>

            <div className="flex-1 flex items-center justify-center p-8">
                <Card className="w-full max-w-md border-slate-800 bg-slate-900/50 backdrop-blur-xl">
                    <CardHeader className="space-y-1 pb-6">
                        <div className="lg:hidden flex items-center gap-2 mb-4">
                            <Building2 className="h-6 w-6 text-indigo-400" />
                            <span className="text-lg font-bold text-white">LLM Chat</span>
                        </div>
                        <CardTitle className="text-2xl font-bold tracking-tight text-white">Register Company</CardTitle>
                        <CardDescription className="text-slate-400">
                            Enter your company details to get started
                        </CardDescription>
                    </CardHeader>
                    <form onSubmit={handleSubmit}>
                        <CardContent className="space-y-4">
                            {error && (
                                <Alert variant="destructive" className="animate-in fade-in-0 slide-in-from-top-1">
                                    <AlertDescription>{error}</AlertDescription>
                                </Alert>
                            )}
                            {success && (
                                <Alert className="border-indigo-800 bg-indigo-950/50">
                                    <CheckCircle2 className="h-4 w-4 text-indigo-400" />
                                    <AlertDescription className="text-indigo-400">
                                        Company registered! Redirecting...
                                    </AlertDescription>
                                </Alert>
                            )}
                            <div className="space-y-2">
                                <Label htmlFor="name" className="text-sm font-medium text-slate-300">Company Name <span className="text-red-400">*</span></Label>
                                <Input
                                    id="name"
                                    type="text"
                                    placeholder="Acme Inc."
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    required
                                    disabled={isLoading || success}
                                    className="h-11 bg-slate-800 border-slate-700 text-white placeholder:text-slate-500 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="plan" className="text-sm font-medium">Plan</Label>
                                <Select value={plan} onValueChange={setPlan} disabled={isLoading || success}>
                                    <SelectTrigger className="h-11 bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700">
                                        <SelectValue placeholder="Select a plan" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="free">Free</SelectItem>
                                        <SelectItem value="startup">Startup</SelectItem>
                                        <SelectItem value="enterprise">Enterprise</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="address" className="text-sm font-medium">Address</Label>
                                <Textarea
                                    id="address"
                                    placeholder="123 Main St, City, Country"
                                    value={address}
                                    onChange={(e) => setAddress(e.target.value)}
                                    disabled={isLoading || success}
                                    className="bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 resize-none"
                                    rows={2}
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="phone" className="text-sm font-medium">Phone</Label>
                                    <Input
                                        id="phone"
                                        type="tel"
                                        placeholder="+1 234 567 890"
                                        value={phone}
                                        onChange={(e) => setPhone(e.target.value)}
                                        disabled={isLoading || success}
                                        className="h-11 bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="website" className="text-sm font-medium">Website</Label>
                                    <Input
                                        id="website"
                                        type="url"
                                        placeholder="https://example.com"
                                        value={website}
                                        onChange={(e) => setWebsite(e.target.value)}
                                        disabled={isLoading || success}
                                        className="h-11 bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700"
                                    />
                                </div>
                            </div>
                            <Button
                                className="w-full h-11 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-medium shadow-lg shadow-blue-500/25 transition-all hover:shadow-xl hover:shadow-blue-500/30"
                                size="lg"
                                type="submit"
                                disabled={isLoading || success}
                            >
                                {isLoading ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Registering...
                                    </>
                                ) : (
                                    "Register Company"
                                )}
                            </Button>
                        </CardContent>
                    </form>
                    <CardFooter className="flex flex-col space-y-4 pt-2">
                        <Link
                            href="/dashboard"
                            className="flex items-center justify-center gap-2 text-sm text-muted-foreground hover:text-blue-600 transition-colors"
                        >
                            <ArrowLeft className="h-4 w-4" />
                            Back to dashboard
                        </Link>
                    </CardFooter>
                </Card>
            </div>
        </div>
    )
}
