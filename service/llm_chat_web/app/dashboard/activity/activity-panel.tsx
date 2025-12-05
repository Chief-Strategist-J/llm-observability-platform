import { Node } from "@xyflow/react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"
import { Trash2, Play, Settings, FileOutput, FileInput, Edit, Wand2 } from "lucide-react"
import { useRouter } from "next/navigation"
import { ActivityForm } from "./activity-form"
import { activityComponents, activitySchemas, type CustomActivity, type ActivitySchema } from "./activity-data"
import { Sparkles } from "lucide-react"
import { ExecutionResult } from "./execution-result"

interface ActivityPanelProps {
    node: Node
    formData: Record<string, string>
    executionOutput: string
    onInputChange: (key: string, value: string) => void
    onExecute: () => void
    onDelete: () => void
    customActivities?: CustomActivity[]
}

export function ActivityPanel({ node, formData, executionOutput, onInputChange, onExecute, onDelete, customActivities = [] }: ActivityPanelProps) {
    const router = useRouter()
    let componentData: any = activityComponents.find(c => c.id === node.data.componentId)
    let schema: ActivitySchema | null = componentData?.id ? activitySchemas[componentData.id] : null

    if (!componentData) {
        const customActivity = customActivities.find(c => c.id === node.data.componentId)
        if (customActivity) {
            componentData = {
                id: customActivity.id,
                name: customActivity.name,
                icon: Sparkles,
                category: "custom",
                description: customActivity.description
            }

            const inputs: Record<string, any> = {}
            customActivity.inputs.forEach(inp => {
                inputs[inp.name] = {
                    type: inp.type,
                    description: inp.description,
                    required: inp.required
                }
            })

            const outputs: Record<string, any> = {}
            customActivity.outputs.forEach(out => {
                outputs[out.name] = {
                    type: out.type,
                    description: out.description
                }
            })

            schema = { inputs, outputs }
        }
    }

    if (!componentData || !schema) {
        return null
    }

    const fillExampleData = () => {
        if (!schema?.inputs) return
        Object.entries(schema.inputs).forEach(([key, field]) => {
            let value = ""
            switch (field.type) {
                case 'string': value = "example-" + key; break
                case 'number': value = "42"; break
                case 'boolean': value = "true"; break
                case 'json': value = '{"key": "value"}'; break
                case 'array': value = '["item1", "item2"]'; break
                default: value = "test";
            }
            onInputChange(key, value)
        })
    }

    return (
        <div className="h-full flex flex-col bg-slate-900 border-l border-slate-800">
            <div className="p-4 border-b border-slate-800 bg-gradient-to-r from-slate-900 to-slate-800/50">
                <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                            <div className={`p-1.5 rounded-md ${componentData.category === 'custom' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-blue-500/10 text-blue-500'}`}>
                                <componentData.icon className="h-4 w-4" />
                            </div>
                            <h2 className="text-sm font-semibold text-white truncate tracking-tight">{String(node.data.label)}</h2>
                        </div>
                        <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                            <Badge variant="outline" className="text-[10px] bg-slate-950/50 text-slate-400 border-slate-700 capitalize">
                                {componentData.category}
                            </Badge>
                            <p className="text-[11px] text-slate-500 leading-tight line-clamp-1">{componentData.description}</p>
                        </div>
                    </div>
                    <div className="flex items-center">
                        {componentData.category === 'custom' && (
                            <Button
                                size="sm"
                                className="h-7 w-7 p-0 bg-transparent hover:bg-slate-800 text-slate-500 hover:text-white transition-colors mr-1"
                                onClick={() => router.push(`/dashboard/activity/create?edit=${componentData.id}`)}
                            >
                                <Edit className="h-3.5 w-3.5" />
                            </Button>
                        )}
                        <Button
                            size="sm"
                            className="h-7 w-7 p-0 bg-transparent hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-colors"
                            onClick={onDelete}
                        >
                            <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                    </div>
                </div>
            </div>

            <Tabs defaultValue="form" className="flex-1 flex flex-col">
                <div className="border-b border-slate-800 px-4 py-2">
                    <TabsList className="bg-slate-800/50 p-1">
                        <TabsTrigger value="input" className="text-xs data-[state=active]:bg-slate-700 data-[state=active]:text-white text-slate-400">
                            <FileInput className="h-3 w-3 mr-1" /> Input
                        </TabsTrigger>
                        <TabsTrigger value="form" className="text-xs data-[state=active]:bg-slate-700 data-[state=active]:text-white text-slate-400">
                            <Settings className="h-3 w-3 mr-1" /> Configure
                        </TabsTrigger>
                        <TabsTrigger value="output" className="text-xs data-[state=active]:bg-slate-700 data-[state=active]:text-white text-slate-400">
                            <FileOutput className="h-3 w-3 mr-1" /> Output
                        </TabsTrigger>
                    </TabsList>
                </div>

                <TabsContent value="input" className="flex-1 m-0 p-4 overflow-hidden">
                    <ScrollArea className="h-full">
                        <div className="space-y-3">
                            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Input from Previous Activity</h3>
                            <Card className="p-3 bg-slate-800/50 border-slate-700">
                                <pre className="text-xs text-slate-300 whitespace-pre-wrap break-words font-mono">
                                    {JSON.stringify({ previousOutput: "data from previous activity" }, null, 2)}
                                </pre>
                            </Card>
                        </div>
                    </ScrollArea>
                </TabsContent>

                <TabsContent value="form" className="flex-1 m-0 overflow-hidden flex flex-col">
                    <div className="px-4 py-2 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
                        <Button onClick={onExecute} size="sm" className="h-6 px-2 text-[10px] bg-emerald-600 hover:bg-emerald-700 text-white border border-emerald-500/50 shadow-sm shadow-emerald-900/20">
                            <Play className="h-3 w-3 mr-1.5" /> Run
                        </Button>
                        <Button onClick={fillExampleData} size="sm" variant="ghost" className="h-6 text-[10px] text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10">
                            <Wand2 className="h-3 w-3 mr-1.5" /> Fill Example
                        </Button>
                    </div>
                    <div className="flex-1 overflow-hidden">
                        <ActivityForm
                            activityId={componentData.id}
                            formData={formData}
                            onInputChange={onInputChange}
                            onExecute={onExecute}
                            schema={schema}
                        />
                    </div>
                </TabsContent>

                <TabsContent value="output" className="flex-1 m-0 overflow-hidden flex flex-col">
                    <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
                        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Execution Output</h3>
                        <Button onClick={onExecute} size="sm" className="h-7 px-3 text-xs bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm shadow-emerald-900/20">
                            <Play className="h-3 w-3 mr-1.5" /> Run Activity
                        </Button>
                    </div>
                    <div className="flex-1 overflow-hidden bg-slate-950">
                        {executionOutput ? (
                            <ExecutionResult output={executionOutput} />
                        ) : (
                            <div className="flex flex-col items-center justify-center h-full text-slate-600 gap-3 p-8 text-center">
                                <div className="h-12 w-12 rounded-full bg-slate-900 flex items-center justify-center">
                                    <Play className="h-5 w-5 ml-0.5 opacity-50" />
                                </div>
                                <div className="space-y-1">
                                    <p className="text-sm font-medium text-slate-400">Ready to Run</p>
                                    <p className="text-xs text-slate-600">Configure inputs and click Run to see results here.</p>
                                </div>
                            </div>
                        )}
                    </div>
                </TabsContent>
            </Tabs>
        </div>
    )
}
