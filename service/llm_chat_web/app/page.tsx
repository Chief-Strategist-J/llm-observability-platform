import Link from "next/link"
import { ArrowRight, MessageSquare, BarChart3, Zap, Shield, Users, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-950">
      <header className="sticky top-0 z-50 w-full border-b border-slate-800 bg-slate-950/90 backdrop-blur-xl">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-lg">
              <MessageSquare className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white">LLM Chat</span>
          </div>
          <nav className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost" className="text-slate-400 hover:text-white hover:bg-slate-800">
                Sign In
              </Button>
            </Link>
            <Link href="/signup">
              <Button className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white border-0">
                Get Started
              </Button>
            </Link>
          </nav>
        </div>
      </header>

      <main>
        <section className="relative overflow-hidden py-24 md:py-32">
          <div className="absolute inset-0">
            <div className="absolute top-20 left-1/4 w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl" />
            <div className="absolute bottom-20 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
          </div>
          <div className="container mx-auto px-4 relative">
            <div className="mx-auto max-w-4xl text-center">
              <div className="inline-flex items-center gap-2 bg-slate-800/50 text-cyan-400 px-4 py-2 rounded-full text-sm font-medium mb-6 border border-slate-700">
                <Sparkles className="h-4 w-4" />
                AI-Powered Conversation Platform
              </div>
              <h1 className="text-5xl md:text-6xl font-bold tracking-tight mb-6 text-white">
                Manage your AI
                <br />
                <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                  conversations smarter
                </span>
              </h1>
              <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-10">
                Monitor activity, analyze workflows, and collaborate with your team - all in one beautiful dashboard.
              </p>
              <div className="flex items-center justify-center gap-4">
                <Link href="/signup">
                  <Button size="lg" className="h-12 px-8 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white border-0">
                    Start for Free
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Button>
                </Link>
                <Link href="/login">
                  <Button size="lg" variant="outline" className="h-12 px-8 border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white">
                    Sign In
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </section>

        <section className="py-20 bg-slate-900/50">
          <div className="container mx-auto px-4">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4 text-white">Everything you need</h2>
              <p className="text-slate-400 max-w-xl mx-auto">
                Powerful features to help you manage AI conversations at scale
              </p>
            </div>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              <Card className="group border-slate-800 bg-slate-900/50 hover:bg-slate-800/50 transition-all duration-300 hover:-translate-y-1">
                <CardHeader>
                  <div className="p-3 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl w-fit mb-3 group-hover:scale-110 transition-transform">
                    <MessageSquare className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle className="text-xl text-white">Smart Chat</CardTitle>
                  <CardDescription className="text-slate-400">
                    One-on-one and group conversations with AI-powered insights
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Link href="/login">
                    <Button variant="link" className="p-0 text-cyan-400 hover:text-cyan-300 font-medium">
                      Explore Chat
                      <ArrowRight className="ml-1 h-4 w-4" />
                    </Button>
                  </Link>
                </CardContent>
              </Card>

              <Card className="group border-slate-800 bg-slate-900/50 hover:bg-slate-800/50 transition-all duration-300 hover:-translate-y-1">
                <CardHeader>
                  <div className="p-3 bg-gradient-to-br from-emerald-500 to-green-600 rounded-xl w-fit mb-3 group-hover:scale-110 transition-transform">
                    <BarChart3 className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle className="text-xl text-white">Analytics</CardTitle>
                  <CardDescription className="text-slate-400">
                    Real-time metrics, insights, and comprehensive reporting
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Link href="/login">
                    <Button variant="link" className="p-0 text-emerald-400 hover:text-emerald-300 font-medium">
                      View Dashboard
                      <ArrowRight className="ml-1 h-4 w-4" />
                    </Button>
                  </Link>
                </CardContent>
              </Card>

              <Card className="group border-slate-800 bg-slate-900/50 hover:bg-slate-800/50 transition-all duration-300 hover:-translate-y-1">
                <CardHeader>
                  <div className="p-3 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl w-fit mb-3 group-hover:scale-110 transition-transform">
                    <Zap className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle className="text-xl text-white">Workflows</CardTitle>
                  <CardDescription className="text-slate-400">
                    Visualize and automate your AI conversation flows
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Link href="/login">
                    <Button variant="link" className="p-0 text-amber-400 hover:text-amber-300 font-medium">
                      View Flows
                      <ArrowRight className="ml-1 h-4 w-4" />
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        <section className="py-20">
          <div className="container mx-auto px-4">
            <div className="grid md:grid-cols-3 gap-8 text-center">
              <div className="p-6">
                <div className="p-3 bg-slate-800 rounded-full w-fit mx-auto mb-4">
                  <Shield className="h-8 w-8 text-cyan-400" />
                </div>
                <h3 className="text-lg font-semibold mb-2 text-white">Enterprise Security</h3>
                <p className="text-slate-400 text-sm">
                  Bank-level encryption and compliance standards
                </p>
              </div>
              <div className="p-6">
                <div className="p-3 bg-slate-800 rounded-full w-fit mx-auto mb-4">
                  <Zap className="h-8 w-8 text-emerald-400" />
                </div>
                <h3 className="text-lg font-semibold mb-2 text-white">Lightning Fast</h3>
                <p className="text-slate-400 text-sm">
                  Optimized performance for instant responses
                </p>
              </div>
              <div className="p-6">
                <div className="p-3 bg-slate-800 rounded-full w-fit mx-auto mb-4">
                  <Users className="h-8 w-8 text-amber-400" />
                </div>
                <h3 className="text-lg font-semibold mb-2 text-white">Team Collaboration</h3>
                <p className="text-slate-400 text-sm">
                  Work together seamlessly with your team
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="py-20 bg-gradient-to-br from-cyan-600 via-blue-600 to-indigo-700 relative overflow-hidden">
          <div className="absolute inset-0">
            <div className="absolute top-10 left-10 w-40 h-40 bg-white/5 rounded-full blur-2xl" />
            <div className="absolute bottom-10 right-10 w-60 h-60 bg-blue-400/10 rounded-full blur-3xl" />
          </div>
          <div className="container mx-auto px-4 text-center relative">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Ready to get started?
            </h2>
            <p className="text-white/80 max-w-xl mx-auto mb-8">
              Join thousands of users already using our platform to manage their AI conversations.
            </p>
            <Link href="/signup">
              <Button size="lg" className="h-12 px-8 bg-white text-blue-600 hover:bg-slate-100 font-medium">
                Create Your Free Account
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-800 py-8 bg-slate-950">
        <div className="container mx-auto px-4 text-center text-sm text-slate-500">
          <p>&copy; 2024 LLM Chat. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
