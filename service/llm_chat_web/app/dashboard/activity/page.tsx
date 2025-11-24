"use client"

import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useCallback, useState } from "react"
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

export default function ActivityPage() {
    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)
    const [selectedNode, setSelectedNode] = useState<Node | null>(null)
    const [formData, setFormData] = useState<Record<string, string>>({})
    const [executionOutput, setExecutionOutput] = useState<string>('')

    const onConnect = useCallback(
        (params: Connection) => setEdges((eds) => addEdge({
            ...params,
            markerEnd: { type: MarkerType.ArrowClosed },
        }, eds)),
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
                const position = {
                    x: event.clientX - reactFlowBounds.left - 75,
                    y: event.clientY - reactFlowBounds.top - 20,
                }
                const newNode: Node = {
                    id: `${component.id}-${Date.now()}`,
                    type: 'default',
                    position,
                    data: { label: component.name, componentId: component.id },
                }
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

    const handleExecute = () => {
        if (!selectedNode?.data.componentId) return

        const schema = activitySchemas[selectedNode.data.componentId as keyof typeof activitySchemas]
        if (!schema) return

        const mockOutput: Record<string, unknown> = {}
        Object.entries(schema.outputs).forEach(([key, outputSchema]) => {
            switch (outputSchema.type) {
                case 'boolean':
                    mockOutput[key] = true
                    break
                case 'number':
                    mockOutput[key] = Math.floor(Math.random() * 100)
                    break
                case 'array':
                    mockOutput[key] = ['item1', 'item2']
                    break
                case 'json':
                    mockOutput[key] = { sample: 'data' }
                    break
                default:
                    mockOutput[key] = `${key}-value-${Date.now()}`
            }
        })

        const response = {
            activityId: selectedNode.data.componentId as string,
            timestamp: new Date().toISOString(),
            inputs: formData,
            outputs: mockOutput
        }

        setExecutionOutput(JSON.stringify(response, null, 2))
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

    return (
        <div className="flex flex-col h-screen">
            <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
                <SidebarTrigger className="-ml-1" />
                <Separator orientation="vertical" className="mr-2 h-4" />
                <h1 className="text-lg font-semibold">Activity Flow</h1>
            </header>

            <ResizablePanelGroup direction="horizontal" className="flex-1">
                <ResizablePanel defaultSize={20} minSize={15} maxSize={30}>
                    <ActivityList onDragStart={onDragStart} />
                </ResizablePanel>

                <ResizableHandle withHandle />

                <ResizablePanel defaultSize={50}>
                    <div className="h-full flex flex-col">
                        <div
                            className="flex-1 bg-muted/20"
                            onDrop={onDrop}
                            onDragOver={onDragOver}
                        >
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
                            >
                                <Controls />
                                <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
                            </ReactFlow>
                        </div>

                        <div className="h-64 border-t">
                            <Tabs defaultValue="traces" className="h-full flex flex-col">
                                <div className="border-b px-4">
                                    <TabsList>
                                        <TabsTrigger value="traces">Traces</TabsTrigger>
                                        <TabsTrigger value="logs">Logs</TabsTrigger>
                                    </TabsList>
                                </div>
                                <TabsContent value="traces" className="flex-1 m-0 p-4 overflow-hidden">
                                    <ScrollArea className="h-full">
                                        <div className="space-y-2">
                                            {traceLogs.map((trace) => (
                                                <Card key={trace.id} className="p-3 hover:bg-accent/50 cursor-pointer transition-colors">
                                                    <div className="flex items-center justify-between">
                                                        <div className="flex items-center gap-3">
                                                            <Badge variant={trace.status === "success" ? "default" : "outline"}>
                                                                {trace.service}
                                                            </Badge>
                                                            <span className="text-sm font-medium">{trace.operation}</span>
                                                        </div>
                                                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                                            <span>{trace.spans} spans</span>
                                                            <span className="font-mono">{trace.duration}</span>
                                                        </div>
                                                    </div>
                                                </Card>
                                            ))}
                                        </div>
                                    </ScrollArea>
                                </TabsContent>
                                <TabsContent value="logs" className="flex-1 m-0 p-4 overflow-hidden">
                                    <ScrollArea className="h-full">
                                        <div className="font-mono text-xs space-y-1">
                                            <div className="text-muted-foreground">[2024-11-24 23:23:09] INFO Starting workflow</div>
                                            <div className="text-green-500">[2024-11-24 23:23:11] SUCCESS Activity executed</div>
                                        </div>
                                    </ScrollArea>
                                </TabsContent>
                            </Tabs>
                        </div>
                    </div>
                </ResizablePanel>

                {selectedNode && (
                    <>
                        <ResizableHandle withHandle />
                        <ResizablePanel defaultSize={30} minSize={25} maxSize={40}>
                            <ActivityPanel
                                node={selectedNode}
                                formData={formData}
                                executionOutput={executionOutput}
                                onInputChange={handleInputChange}
                                onExecute={handleExecute}
                                onDelete={handleDeleteNode}
                            />
                        </ResizablePanel>
                    </>
                )}
            </ResizablePanelGroup>
        </div>
    )
}
