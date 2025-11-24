import Link from "next/link"
import { ArrowRight, MessageSquare, BarChart3, Network, History } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-6 w-6 text-primary" />
            <span className="text-xl font-bold">LLM Chat</span>
          </div>
          <nav className="flex items-center gap-4">
            <Link href="/login">
              <Button variant="ghost">
                Sign In
              </Button>
            </Link>
            <Link href="/signup">
              <Button>
                Get Started
              </Button>
            </Link>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <section className="container px-4 py-24 md:py-32">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
              Welcome to Your AI-Powered Dashboard
            </h1>
            <p className="mt-6 text-lg leading-8 text-muted-foreground">
              Manage conversations, monitor activity, and analyze your AI workflows all in one place.
              Experience the future of intelligent chat management.
            </p>
            <div className="mt-10 flex items-center justify-center gap-4">
              <Link href="/dashboard">
                <Button size="lg">
                  Go to Dashboard
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
              <Link href="/signup">
                <Button size="lg" variant="outline">
                  Sign Up
                </Button>
              </Link>
            </div>
          </div>
        </section>

        <section className="container px-4 py-16">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader>
                <MessageSquare className="h-8 w-8 text-primary" />
                <CardTitle>Chat</CardTitle>
                <CardDescription>
                  One-on-one and group conversations
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Link href="/dashboard/chat">
                  <Button variant="link" className="p-0">
                    Explore Chat
                    <ArrowRight className="ml-1 h-3 w-3" />
                  </Button>
                </Link>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <BarChart3 className="h-8 w-8 text-primary" />
                <CardTitle>Analytics</CardTitle>
                <CardDescription>
                  Real-time metrics and insights
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Link href="/dashboard">
                  <Button variant="link" className="p-0">
                    View Dashboard
                    <ArrowRight className="ml-1 h-3 w-3" />
                  </Button>
                </Link>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <Network className="h-8 w-8 text-primary" />
                <CardTitle>Activity Flow</CardTitle>
                <CardDescription>
                  Visualize your AI workflows
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Link href="/dashboard/activity">
                  <Button variant="link" className="p-0">
                    View Flows
                    <ArrowRight className="ml-1 h-3 w-3" />
                  </Button>
                </Link>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <History className="h-8 w-8 text-primary" />
                <CardTitle>History</CardTitle>
                <CardDescription>
                  Track all your activities
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Link href="/dashboard/history">
                  <Button variant="link" className="p-0">
                    View History
                    <ArrowRight className="ml-1 h-3 w-3" />
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        </section>

        <section className="container px-4 py-16">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold">Ready to get started?</h2>
            <p className="mt-4 text-muted-foreground">
              Join thousands of users already using our platform to manage their AI conversations.
            </p>
            <div className="mt-8">
              <Link href="/signup">
                <Button size="lg">
                  Create Your Account
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t py-8">
        <div className="container px-4 text-center text-sm text-muted-foreground">
          <p>&copy; 2024 LLM Chat. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
