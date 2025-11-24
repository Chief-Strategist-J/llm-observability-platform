import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { activitySchemas, type ActivitySchema } from "./activity-data"

interface ActivityFormProps {
    activityId: string
    formData: Record<string, string>
    onInputChange: (key: string, value: string) => void
    onExecute: () => void
}

export function ActivityForm({ activityId, formData, onInputChange, onExecute }: ActivityFormProps) {
    const schema = activitySchemas[activityId]

    if (!schema) {
        return (
            <div className="p-4 text-center text-muted-foreground">
                No schema defined for this activity
            </div>
        )
    }

    return (
        <ScrollArea className="h-full">
            <div className="p-4 space-y-4">
                {Object.entries(schema.inputs).map(([key, inputSchema]) => (
                    <div key={key} className="space-y-2">
                        <Label className="text-sm font-medium">
                            {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                            {inputSchema.required && <span className="text-destructive ml-1">*</span>}
                        </Label>
                        <p className="text-xs text-muted-foreground">{inputSchema.description}</p>

                        {inputSchema.type === 'select' && key === 'method' ? (
                            <Select
                                value={formData[key] || 'GET'}
                                onValueChange={(val) => onInputChange(key, val)}
                            >
                                <SelectTrigger className="h-9">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="GET">GET</SelectItem>
                                    <SelectItem value="POST">POST</SelectItem>
                                    <SelectItem value="PUT">PUT</SelectItem>
                                    <SelectItem value="DELETE">DELETE</SelectItem>
                                    <SelectItem value="PATCH">PATCH</SelectItem>
                                    <SelectItem value="OPTIONS">OPTIONS</SelectItem>
                                    <SelectItem value="HEAD">HEAD</SelectItem>
                                </SelectContent>
                            </Select>
                        ) : inputSchema.type === 'json' || inputSchema.type === 'array' ? (
                            <Textarea
                                placeholder={inputSchema.type === 'json' ? '{}' : '[]'}
                                className="font-mono text-xs min-h-[60px] resize-none"
                                value={formData[key] || ''}
                                onChange={(e) => onInputChange(key, e.target.value)}
                            />
                        ) : inputSchema.type === 'boolean' ? (
                            <Select
                                value={formData[key] || 'true'}
                                onValueChange={(val) => onInputChange(key, val)}
                            >
                                <SelectTrigger className="h-9">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="true">True</SelectItem>
                                    <SelectItem value="false">False</SelectItem>
                                </SelectContent>
                            </Select>
                        ) : (
                            <Input
                                placeholder={`Enter ${key}`}
                                className="h-9"
                                type={inputSchema.type === 'number' ? 'number' : 'text'}
                                value={formData[key] || ''}
                                onChange={(e) => onInputChange(key, e.target.value)}
                            />
                        )}
                    </div>
                ))}

                <Button className="w-full" onClick={onExecute}>Execute</Button>
            </div>
        </ScrollArea>
    )
}
