"use client"

import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { useCallback, useState, useEffect } from "react"
import {
    ReactFlow,
    Controls,
    Background,
    useNodesState,
    useEdgesState,
    addEdge,
    BackgroundVariant,
    Node,
    Edge,
    Connection,
    MarkerType,
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable"
import { ActivityList } from "./activity-list"
import { ActivityPanel } from "./activity-panel"
import { activitySchemas, type ActivityComponent } from "./activity-data"
import { MessageSquare, Send, ThumbsUp, Reply, MoreVertical, Clock, Activity, Plus, Code2, Play, Loader2 } from "lucide-react"
import { ExecutionResult } from "./execution-result"
import { useRouter } from "next/navigation"

interface CustomActivity {
    id: string
    name: string
    description: string
    category: string
    inputs: { name: string; type: string; description: string; required: boolean }[]
    outputs: { name: string; type: string; description: string }[]
    code: string
    createdAt: string
}

const initialNodes: Node[] = [
    { id: "1", type: "input", data: { label: "Start" }, position: { x: 250, y: 50 } },
    { id: "2", data: { label: "HTTP Request", componentId: "http-request" }, position: { x: 250, y: 150 } },
    { id: "3", type: "output", data: { label: "Response" }, position: { x: 250, y: 250 } },
]

const initialEdges: Edge[] = [
    { id: "e1-2", source: "1", target: "2", animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
    { id: "e2-3", source: "2", target: "3", markerEnd: { type: MarkerType.ArrowClosed } },
]

const traceLogs = [
    { id: 1, service: "http-request", operation: "GET Request", duration: "182.5ms", spans: 3, status: "success" },
    { id: 2, service: "configure-logs", operation: "Configure Source", duration: "365.01ms", spans: 7, status: "success" },
]

interface Discussion {
    id: string
    author: string
    avatar: string
    content: string
    time: string
    likes: number
    replies: { author: string; avatar: string; content: string; time: string }[]
}

const initialDiscussions: Discussion[] = [
    {
        id: "d1",
        author: "Jackson Lee",
        avatar: "/avatars/02.png",
        content: "Should we add retry logic to the HTTP Request node? I noticed some timeouts during peak hours.",
        time: "2 hours ago",
        likes: 3,
        replies: [
            { author: "Sofia Davis", avatar: "/avatars/03.png", content: "Good idea! We can use exponential backoff.", time: "1 hour ago" }
        ]
    },
    {
        id: "d2",
        author: "You",
        avatar: "/avatars/01.png",
        content: "Added error handling for the response node. Let me know if you see any edge cases.",
        time: "30 minutes ago",
        likes: 1,
        replies: []
    }
]

export default function ActivityPage() {
    const router = useRouter()
    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)
    const [selectedNode, setSelectedNode] = useState<Node | null>(null)
    const [formData, setFormData] = useState<Record<string, string>>({})
    const [executionOutput, setExecutionOutput] = useState<string>('')
    const [discussions, setDiscussions] = useState<Discussion[]>(initialDiscussions)
    const [newComment, setNewComment] = useState("")
    const [activeTab, setActiveTab] = useState("traces")
    const [customActivities, setCustomActivities] = useState<CustomActivity[]>([])
    const [isRunning, setIsRunning] = useState(false)
    const [replyingTo, setReplyingTo] = useState<string | null>(null)

    useEffect(() => {
        const stored = localStorage.getItem('customActivities')
        if (stored) {
            try {
                const parsed = JSON.parse(stored)
                if (parsed.length > 0) {
                    setCustomActivities(parsed)
                    return
                }
            } catch (e) {
                console.error('Failed to load custom activities', e)
            }
        }

        // Default Demo Activity
        const demoActivity: CustomActivity = {
            id: 'demo-fetch-todo',
            name: 'Demo: Fetch Todo',
            description: 'Fetches a todo item from a public API. Try running this!',
            category: 'testing',
            inputs: [{ name: 'todoId', type: 'number', description: 'ID of the todo to fetch (1-200)', required: true }],
            outputs: [{ name: 'title', type: 'string', description: 'Title of the todo' }, { name: 'completed', type: 'boolean', description: 'Completion status' }],
            code: `async function process(inputs) {
  console.log("Starting fetch for Todo ID:", inputs.todoId);
  
  // Real API call to JSONPlaceholder
  const response = await fetch(\`https://jsonplaceholder.typicode.com/todos/\${inputs.todoId}\`);
  
  if (!response.ok) {
    throw new Error(\`API request failed with status \${response.status}\`);
  }
  
  const data = await response.json();
  console.log("Data received:", data);
  
  return {
    title: data.title,
    completed: data.completed,
    fullResponse: data
  };
}`,
            createdAt: new Date().toISOString()
        }

        setCustomActivities([demoActivity])
        localStorage.setItem('customActivities', JSON.stringify([demoActivity]))
    }, [])

    const getCustomActivityCode = (componentId: string) => {
        const custom = customActivities.find(a => a.id === componentId)
        return custom?.code || null
    }

    const runActivity = async () => {
        if (!selectedNode?.data.componentId) return
        setIsRunning(true)
        setExecutionOutput('')
        const custom = customActivities.find(a => a.id === selectedNode.data.componentId)

        try {
            if (custom) {
                // Prepare inputs
                const mockInputs: Record<string, unknown> = {}
                custom.inputs.forEach(inp => {
                    switch (inp.type) {
                        case 'string': mockInputs[inp.name] = `test-${inp.name}`; break
                        case 'number': mockInputs[inp.name] = 42; break
                        case 'boolean': mockInputs[inp.name] = true; break
                        case 'json': mockInputs[inp.name] = { key: 'value' }; break
                        case 'array': mockInputs[inp.name] = ['item1', 'item2']; break
                    }
                })

                // Capture console.log
                const logs: string[] = []
                const mockConsole = {
                    log: (...args: any[]) => logs.push(args.map(a => String(a)).join(' ')),
                    error: (...args: any[]) => logs.push('[ERROR] ' + args.map(a => String(a)).join(' ')),
                    warn: (...args: any[]) => logs.push('[WARN] ' + args.map(a => String(a)).join(' '))
                }

                // Execute custom code
                const executionFunction = new Function('inputs', 'console', `
                    return (async () => {
                        try {
                            ${custom.code}
                            if (typeof process !== 'function') {
                                throw new Error("Function 'process' is not defined. Please define 'async function process(inputs) { ... }'");
                            }
                            return await process(inputs);
                        } catch (e) {
                            throw e;
                        }
                    })();
                `)

                const result = await executionFunction(mockInputs, mockConsole)

                setExecutionOutput(JSON.stringify({
                    activity: custom.name,
                    status: 'success',
                    executedAt: new Date().toISOString(),
                    inputs: mockInputs,
                    outputs: result,
                    logs: logs.length > 0 ? logs : undefined
                }, null, 2))

            } else if (selectedNode.data.componentId === 'http-request') {
                // Real HTTP Request Execution
                const method = formData.method || 'GET'
                const url = formData.url
                const headers = formData.headers ? JSON.parse(formData.headers) : {}
                const body = formData.body ? JSON.parse(formData.body) : undefined

                if (!url) throw new Error("URL is required")

                const startTime = performance.now()
                const response = await fetch(url, {
                    method,
                    headers: { 'Content-Type': 'application/json', ...headers },
                    body: method !== 'GET' && method !== 'HEAD' ? JSON.stringify(body) : undefined
                })
                const endTime = performance.now()

                let data
                const contentType = response.headers.get('content-type')
                if (contentType && contentType.includes('application/json')) {
                    data = await response.json()
                } else {
                    data = await response.text()
                }

                setExecutionOutput(JSON.stringify({
                    activity: "HTTP Request",
                    status: response.ok ? 'success' : 'error',
                    statusCode: response.status,
                    duration: `${(endTime - startTime).toFixed(2)}ms`,
                    executedAt: new Date().toISOString(),
                    request: { method, url, headers, body },
                    response: data
                }, null, 2))

            } else {
                // Other built-in activities (still mock for now as they require backend)
                setTimeout(() => {
                    setExecutionOutput(JSON.stringify({
                        activity: selectedNode.data.label,
                        status: 'success',
                        executedAt: new Date().toISOString(),
                        message: 'Simulation successful (Backend integration required for real execution)',
                        inputs: formData
                    }, null, 2))
                }, 1000)
            }
        } catch (error: any) {
            setExecutionOutput(JSON.stringify({
                activity: selectedNode.data.label,
                status: 'error',
                executedAt: new Date().toISOString(),
                error: error.message || String(error)
            }, null, 2))
        } finally {
            setIsRunning(false)
        }
    }

    const onConnect = useCallback(
        (params: Connection) => setEdges((eds) => addEdge({ ...params, markerEnd: { type: MarkerType.ArrowClosed } }, eds)),
        [setEdges]
    )

    const onDragStart = (event: React.DragEvent, component: ActivityComponent) => {
        event.dataTransfer.setData('application/reactflow', JSON.stringify(component))
        event.dataTransfer.effectAllowed = 'move'
    }

    const onDrop = useCallback(
        (event: React.DragEvent) => {
            event.preventDefault()
            const reactFlowBounds = event.currentTarget.getBoundingClientRect()
            const componentData = event.dataTransfer.getData('application/reactflow')
            if (componentData) {
                const component = JSON.parse(componentData)
                const position = { x: event.clientX - reactFlowBounds.left - 75, y: event.clientY - reactFlowBounds.top - 20 }
                const newNode: Node = { id: `${component.id}-${Date.now()}`, type: 'default', position, data: { label: component.name, componentId: component.id } }
                setNodes((nds) => nds.concat(newNode))
            }
        },
        [setNodes]
    )

    const onDragOver = useCallback((event: React.DragEvent) => {
        event.preventDefault()
        event.dataTransfer.dropEffect = 'move'
    }, [])

    const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
        setSelectedNode(node)
        setFormData({})
        setExecutionOutput('')
    }, [])

    const handleInputChange = (key: string, value: string) => {
        setFormData(prev => ({ ...prev, [key]: value }))
    }



    const handleDeleteNode = () => {
        if (!selectedNode) return
        setNodes((nds) => nds.filter((n) => n.id !== selectedNode.id))
        setEdges((eds) => eds.filter((e) => e.source !== selectedNode.id && e.target !== selectedNode.id))
        setSelectedNode(null)
        setFormData({})
        setExecutionOutput('')
    }

    const onNodesDelete = useCallback((deleted: Node[]) => {
        if (selectedNode && deleted.find(n => n.id === selectedNode.id)) {
            setSelectedNode(null)
            setFormData({})
            setExecutionOutput('')
        }
    }, [selectedNode])

    const handleAddComment = () => {
        if (newComment.trim()) {
            if (replyingTo) {
                setDiscussions(discussions.map(d => {
                    if (d.id === replyingTo) {
                        return {
                            ...d,
                            replies: [...d.replies, {
                                author: "You",
                                avatar: "/avatars/01.png",
                                content: newComment,
                                time: "Just now"
                            }]
                        }
                    }
                    return d
                }))
                setReplyingTo(null)
            } else {
                const newDiscussion: Discussion = {
                    id: `d${Date.now()}`,
                    author: "You",
                    avatar: "/avatars/01.png",
                    content: newComment,
                    time: "Just now",
                    likes: 0,
                    replies: []
                }
                setDiscussions([newDiscussion, ...discussions])
            }
            setNewComment("")
        }
    }

    const handleLike = (id: string) => {
        setDiscussions(discussions.map(d => {
            if (d.id === id) {
                return { ...d, likes: d.likes + 1 }
            }
            return d
        }))
    }

    return (
        <div className="flex flex-col h-screen bg-slate-950">
            <header className="flex h-14 shrink-0 items-center gap-3 border-b border-slate-800 px-4 bg-slate-900">
                <SidebarTrigger className="text-slate-400 hover:text-white" />
                <Separator orientation="vertical" className="h-5 bg-slate-700" />
                <div className="flex items-center gap-2">
                    <div className="h-8 w-8 rounded-lg bg-slate-800 flex items-center justify-center">
                        <Activity className="h-4 w-4 text-slate-300" />
                    </div>
                    <div>
                        <h1 className="text-base font-semibold text-white tracking-tight">Activity Flow</h1>
                        <p className="text-xs text-slate-500">{nodes.length} nodes • {edges.length} connections</p>
                    </div>
                </div>
                <div className="ml-auto">
                    <Button onClick={() => router.push('/dashboard/activity/create')} size="sm" className="h-8 px-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg">
                        <Plus className="h-4 w-4 mr-1.5" /> Create Activity
                    </Button>
                </div>
            </header>

            <ResizablePanelGroup direction="horizontal" className="flex-1">
                <ResizablePanel defaultSize={18} minSize={15} maxSize={25}>
                    <ActivityList onDragStart={onDragStart} customActivities={customActivities} />
                </ResizablePanel>

                <ResizableHandle className="w-1 bg-slate-800 hover:bg-slate-700 transition-colors" />

                <ResizablePanel defaultSize={52}>
                    <ResizablePanelGroup direction="vertical" className="h-full">
                        <ResizablePanel defaultSize={60} minSize={30}>
                            <div className="h-full bg-slate-900/50" onDrop={onDrop} onDragOver={onDragOver}>
                                <ReactFlow
                                    nodes={nodes}
                                    edges={edges}
                                    onNodesChange={onNodesChange}
                                    onEdgesChange={onEdgesChange}
                                    onConnect={onConnect}
                                    onNodeClick={onNodeClick}
                                    onNodesDelete={onNodesDelete}
                                    fitView
                                    deleteKeyCode="Delete"
                                    style={{ background: '#0f172a' }}
                                >
                                    <Controls className="!bg-slate-800 !border-slate-700 !rounded-lg [&>button]:!bg-slate-800 [&>button]:!border-slate-700 [&>button]:!text-slate-300 [&>button:hover]:!bg-slate-700" />
                                    <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#334155" />
                                </ReactFlow>
                            </div>
                        </ResizablePanel>

                        <ResizableHandle className="h-1 bg-slate-800 hover:bg-slate-700 transition-colors" />

                        <ResizablePanel defaultSize={40} minSize={20} maxSize={60}>
                            <div className="h-full border-t border-slate-800 bg-slate-900 flex flex-col overflow-hidden">
                                <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col overflow-hidden">
                                    <div className="border-b border-slate-800 px-4 py-2 shrink-0">
                                        <TabsList className="bg-slate-800/50 p-1">
                                            <TabsTrigger value="traces" className="text-xs data-[state=active]:bg-slate-700 data-[state=active]:text-white text-slate-400">Traces</TabsTrigger>
                                            <TabsTrigger value="logs" className="text-xs data-[state=active]:bg-slate-700 data-[state=active]:text-white text-slate-400">Logs</TabsTrigger>
                                            <TabsTrigger value="code" className="text-xs data-[state=active]:bg-slate-700 data-[state=active]:text-white text-slate-400">
                                                <Code2 className="h-3 w-3 mr-1" /> Code
                                            </TabsTrigger>
                                            <TabsTrigger value="discussion" className="text-xs data-[state=active]:bg-slate-700 data-[state=active]:text-white text-slate-400">
                                                <MessageSquare className="h-3 w-3 mr-1" /> Discussion
                                            </TabsTrigger>
                                        </TabsList>
                                    </div>

                                    <TabsContent value="traces" className="flex-1 m-0 p-4 overflow-hidden">
                                        <ScrollArea className="h-full">
                                            <div className="space-y-2">
                                                {traceLogs.map((trace) => (
                                                    <Card key={trace.id} className="p-3 bg-slate-800/50 border-slate-700 hover:bg-slate-800 cursor-pointer transition-colors">
                                                        <div className="flex items-center justify-between">
                                                            <div className="flex items-center gap-3">
                                                                <Badge className={`text-xs ${trace.status === "success" ? "bg-emerald-600/20 text-emerald-400" : "bg-slate-600/20 text-slate-400"}`}>
                                                                    {trace.service}
                                                                </Badge>
                                                                <span className="text-sm font-medium text-white">{trace.operation}</span>
                                                            </div>
                                                            <div className="flex items-center gap-4 text-xs text-slate-400">
                                                                <span>{trace.spans} spans</span>
                                                                <span className="font-mono text-slate-300">{trace.duration}</span>
                                                            </div>
                                                        </div>
                                                    </Card>
                                                ))}
                                            </div>
                                        </ScrollArea>
                                    </TabsContent>

                                    <TabsContent value="logs" className="flex-1 m-0 p-4 overflow-hidden">
                                        <ScrollArea className="h-full">
                                            <div className="font-mono text-xs space-y-1.5">
                                                <div className="text-slate-400 flex gap-2"><span className="text-slate-600">[2024-11-24 23:23:09]</span><span className="text-blue-400">INFO</span> Starting workflow</div>
                                                <div className="text-slate-400 flex gap-2"><span className="text-slate-600">[2024-11-24 23:23:11]</span><span className="text-emerald-400">SUCCESS</span> Activity executed</div>
                                                <div className="text-slate-400 flex gap-2"><span className="text-slate-600">[2024-11-24 23:23:12]</span><span className="text-blue-400">INFO</span> Processing response</div>
                                            </div>
                                        </ScrollArea>
                                    </TabsContent>

                                    <TabsContent value="code" className="flex-1 m-0 overflow-hidden flex flex-col">
                                        <ScrollArea className="h-full">
                                            <div className="p-4 space-y-4">
                                                {selectedNode?.data.componentId ? (
                                                    <>
                                                        <div className="flex items-center justify-between">
                                                            <div className="flex items-center gap-2">
                                                                <span className="text-xs font-medium text-slate-400 uppercase tracking-wide">Activity Code</span>
                                                                <Badge className="text-[10px] bg-slate-800 text-slate-400">{String(selectedNode.data.componentId)}</Badge>
                                                                {customActivities.find(a => a.id === selectedNode.data.componentId) && (
                                                                    <Badge className="text-[10px] bg-emerald-600/20 text-emerald-400">Custom</Badge>
                                                                )}
                                                            </div>
                                                            <Button onClick={runActivity} disabled={isRunning} size="sm" className="h-7 px-3 text-xs bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg">
                                                                {isRunning ? <><Loader2 className="h-3 w-3 mr-1.5 animate-spin" /> Running...</> : <><Play className="h-3 w-3 mr-1.5" /> Run</>}
                                                            </Button>
                                                        </div>
                                                        <pre className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg text-xs font-mono text-emerald-300 overflow-x-auto whitespace-pre-wrap">
                                                            {getCustomActivityCode(String(selectedNode.data.componentId)) || `async function ${String(selectedNode.data.componentId).replace(/-/g, '_')}(inputs) {
  // Activity: ${String(selectedNode.data.label)}
  
  const result = await executeActivity({
    type: "${selectedNode.data.componentId}",
    inputs: inputs
  });
  
  return {
    success: result.status === "ok",
    data: result.data,
    timestamp: new Date().toISOString()
  };
}`}
                                                        </pre>
                                                        <div className="flex-1 min-h-0 mt-4">
                                                            <ExecutionResult output={executionOutput} />
                                                        </div>
                                                    </>
                                                ) : (
                                                    <div className="flex flex-col items-center justify-center h-32 text-slate-500">
                                                        <Code2 className="h-8 w-8 mb-2 opacity-50" />
                                                        <p className="text-xs">Select a node to view code</p>
                                                    </div>
                                                )}
                                            </div>
                                        </ScrollArea>
                                    </TabsContent>

                                    <TabsContent value="discussion" className="flex-1 m-0 overflow-hidden flex flex-col">
                                        <div className="p-3 border-b border-slate-800">
                                            <div className="flex flex-col gap-2 w-full">
                                                {replyingTo && (
                                                    <div className="flex items-center justify-between bg-slate-800/50 px-3 py-1.5 rounded-md border border-slate-700/50">
                                                        <span className="text-xs text-slate-400">Replying to <span className="text-emerald-400">@{discussions.find(d => d.id === replyingTo)?.author}</span></span>
                                                        <button onClick={() => setReplyingTo(null)} className="text-slate-500 hover:text-slate-300">
                                                            <Plus className="h-3 w-3 rotate-45" />
                                                        </button>
                                                    </div>
                                                )}
                                                <div className="flex gap-2">
                                                    <Input
                                                        placeholder={replyingTo ? "Write a reply..." : "Add a comment about this workflow..."}
                                                        value={newComment}
                                                        onChange={(e) => setNewComment(e.target.value)}
                                                        onKeyDown={(e) => { if (e.key === "Enter") handleAddComment() }}
                                                        className="flex-1 h-9 text-sm bg-slate-800 border-slate-700 text-white placeholder:text-slate-500"
                                                    />
                                                    <Button onClick={handleAddComment} disabled={!newComment.trim()} className="h-9 px-3 bg-slate-700 hover:bg-slate-600 text-white">
                                                        <Send className="h-3.5 w-3.5" />
                                                    </Button>
                                                </div>
                                            </div>
                                        </div>
                                        <ScrollArea className="flex-1 p-3 min-h-0">
                                            <div className="space-y-3">
                                                {discussions.map((d) => (
                                                    <div key={d.id} className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50">
                                                        <div className="flex items-start gap-2.5">
                                                            <Avatar className="h-7 w-7">
                                                                <AvatarImage src={d.avatar} />
                                                                <AvatarFallback className="bg-slate-700 text-white text-xs">{d.author[0]}</AvatarFallback>
                                                            </Avatar>
                                                            <div className="flex-1 min-w-0">
                                                                <div className="flex items-center gap-2">
                                                                    <span className="text-sm font-medium text-white">{d.author}</span>
                                                                    <span className="text-xs text-slate-500 flex items-center gap-1"><Clock className="h-3 w-3" />{d.time}</span>
                                                                </div>
                                                                <p className="text-sm text-slate-300 mt-1 leading-relaxed">{d.content}</p>
                                                                <div className="flex items-center gap-3 mt-2">
                                                                    <button onClick={() => handleLike(d.id)} className="text-xs text-slate-500 hover:text-emerald-400 transition-colors flex items-center gap-1"><ThumbsUp className="h-3 w-3" /> {d.likes}</button>
                                                                    <button onClick={() => setReplyingTo(d.id)} className="text-xs text-slate-500 hover:text-blue-400 transition-colors flex items-center gap-1"><Reply className="h-3 w-3" /> Reply</button>
                                                                </div>
                                                                {d.replies.length > 0 && (
                                                                    <div className="mt-2 pl-3 border-l-2 border-slate-700 space-y-2">
                                                                        {d.replies.map((r, i) => (
                                                                            <div key={i} className="flex items-start gap-2">
                                                                                <Avatar className="h-5 w-5">
                                                                                    <AvatarImage src={r.avatar} />
                                                                                    <AvatarFallback className="bg-slate-700 text-white text-[10px]">{r.author[0]}</AvatarFallback>
                                                                                </Avatar>
                                                                                <div>
                                                                                    <div className="flex items-center gap-1.5">
                                                                                        <span className="text-xs font-medium text-white">{r.author}</span>
                                                                                        <span className="text-[10px] text-slate-500">{r.time}</span>
                                                                                    </div>
                                                                                    <p className="text-xs text-slate-400 mt-0.5">{r.content}</p>
                                                                                </div>
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </ScrollArea>
                                    </TabsContent>
                                </Tabs>
                            </div>
                        </ResizablePanel>
                    </ResizablePanelGroup>
                </ResizablePanel>

                {selectedNode && (
                    <>
                        <ResizableHandle className="w-1 bg-slate-800 hover:bg-slate-700 transition-colors" />
                        <ResizablePanel defaultSize={30} minSize={25} maxSize={40}>
                            <ActivityPanel
                                node={selectedNode}
                                formData={formData}
                                executionOutput={executionOutput}
                                onInputChange={handleInputChange}
                                onExecute={runActivity}
                                onDelete={handleDeleteNode}
                                customActivities={customActivities}
                            />
                        </ResizablePanel>
                    </>
                )}
            </ResizablePanelGroup>
        </div>
    )
}
