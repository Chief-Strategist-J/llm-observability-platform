import { Node } from "@xyflow/react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"
import { Trash2 } from "lucide-react"
import { ActivityForm } from "./activity-form"
import { activityComponents, activitySchemas } from "./activity-data"

interface ActivityPanelProps {
    node: Node
    formData: Record<string, string>
    executionOutput: string
    onInputChange: (key: string, value: string) => void
    onExecute: () => void
    onDelete: () => void
}

export function ActivityPanel({
    node,
    formData,
    executionOutput,
    onInputChange,
    onExecute,
    onDelete
}: ActivityPanelProps) {
    const componentData = activityComponents.find(c => c.id === node.data.componentId)
    const schema = componentData?.id ? activitySchemas[componentData.id] : null

    if (!componentData || !schema) {
        return null
    }

    return (
        <div className="h-full flex flex-col bg-background">
            <div className="p-4 border-b">
                <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                        <h2 className="font-semibold truncate">{String(node.data.label)}</h2>
                        <div className="flex items-center gap-2 mt-1 flex-wrap">
                            <Badge variant="outline" className="text-xs capitalize">
                                {componentData.category}
                            </Badge>
                            <p className="text-xs text-muted-foreground">{componentData.description}</p>
                        </div>
                    </div>
                    <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10"
                        onClick={onDelete}
                    >
                        <Trash2 className="h-4 w-4" />
                    </Button>
                </div>
            </div>

            <Tabs defaultValue="input" className="flex-1 flex flex-col">
                <div className="border-b px-4">
                    <TabsList>
                        <TabsTrigger value="input">Input</TabsTrigger>
                        <TabsTrigger value="form">Form</TabsTrigger>
                        <TabsTrigger value="output">Output</TabsTrigger>
                    </TabsList>
                </div>

                <TabsContent value="input" className="flex-1 m-0 p-4 overflow-hidden">
                    <ScrollArea className="h-full">
                        <div className="space-y-3">
                            <h3 className="text-sm font-semibold">Input from Previous Activity</h3>
                            <Card className="p-3 bg-muted/30">
                                <pre className="text-xs text-muted-foreground whitespace-pre-wrap break-words">
                                    {JSON.stringify({ previousOutput: "data from previous activity" }, null, 2)}
                                </pre>
                            </Card>
                        </div>
                    </ScrollArea>
                </TabsContent>

                <TabsContent value="form" className="flex-1 m-0 overflow-hidden">
                    <ActivityForm
                        activityId={componentData.id}
                        formData={formData}
                        onInputChange={onInputChange}
                        onExecute={onExecute}
                    />
                </TabsContent>

                <TabsContent value="output" className="flex-1 m-0 p-4 overflow-hidden">
                    <ScrollArea className="h-full">
                        <div className="space-y-3">
                            <h3 className="text-sm font-semibold">Execution Output</h3>
                            <Card className="p-3 bg-muted/30">
                                <pre className="text-xs whitespace-pre-wrap break-words">
                                    {executionOutput || 'No output yet. Click Execute to run.'}
                                </pre>
                            </Card>

                            {schema.outputs && !executionOutput && (
                                <div className="mt-4">
                                    <h4 className="text-xs font-semibold mb-2 text-muted-foreground">Expected Output Schema:</h4>
                                    <div className="space-y-2">
                                        {Object.entries(schema.outputs).map(([key, outputSchema]) => (
                                            <div key={key} className="text-xs">
                                                <span className="font-mono text-primary">{key}</span>
                                                <span className="text-muted-foreground"> ({outputSchema.type})</span>
                                                <span className="text-muted-foreground"> - {outputSchema.description}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </ScrollArea>
                </TabsContent>
            </Tabs>
        </div>
    )
}
