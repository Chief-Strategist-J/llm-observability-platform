import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Switch } from "@/components/ui/switch"
import { Badge } from "@/components/ui/badge"
import { Type, Hash, Braces, List, ToggleLeft, AlignLeft, Play } from "lucide-react"
import { activitySchemas, type ActivitySchema } from "./activity-data"

interface ActivityFormProps {
    activityId: string
    formData: Record<string, string>
    onInputChange: (key: string, value: string) => void
    onExecute: () => void
    schema?: ActivitySchema
}

export function ActivityForm({ activityId, formData, onInputChange, onExecute, schema: propSchema }: ActivityFormProps) {
    const schema = propSchema || activitySchemas[activityId]

    if (!schema) {
        return (
            <div className="flex flex-col items-center justify-center h-32 text-slate-500">
                <p className="text-xs">No configuration needed</p>
            </div>
        )
    }

    const getTypeIcon = (type: string) => {
        switch (type) {
            case 'string': return <Type className="h-3 w-3" />;
            case 'number': return <Hash className="h-3 w-3" />;
            case 'json': return <Braces className="h-3 w-3" />;
            case 'array': return <List className="h-3 w-3" />;
            case 'boolean': return <ToggleLeft className="h-3 w-3" />;
            default: return <AlignLeft className="h-3 w-3" />;
        }
    }

    return (
        <ScrollArea className="h-full">
            <div className="p-4 space-y-5">
                {Object.entries(schema.inputs).map(([key, inputSchema]) => (
                    <div key={key} className="space-y-2 group">
                        <div className="flex items-center justify-between">
                            <Label className="text-xs font-medium text-slate-300 flex items-center gap-2 capitalize">
                                <div className="p-1 rounded bg-slate-800 text-slate-400 group-hover:text-emerald-400 group-hover:bg-emerald-500/10 transition-colors">
                                    {getTypeIcon(inputSchema.type)}
                                </div>
                                {key.replace(/([A-Z])/g, ' $1').trim()}
                            </Label>
                            {inputSchema.required && (
                                <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-4 border-slate-700 text-slate-500">Required</Badge>
                            )}
                        </div>

                        <div className="relative">
                            {inputSchema.type === 'select' && key === 'method' ? (
                                <Select
                                    value={formData[key] || 'GET'}
                                    onValueChange={(val) => onInputChange(key, val)}
                                >
                                    <SelectTrigger className="h-9 bg-slate-950 border-slate-800 text-white text-xs focus:ring-emerald-500/50">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent className="bg-slate-900 border-slate-800">
                                        {['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'].map(m => (
                                            <SelectItem key={m} value={m} className="text-slate-300 text-xs focus:bg-slate-800 focus:text-white">{m}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            ) : inputSchema.type === 'json' || inputSchema.type === 'array' ? (
                                <Textarea
                                    placeholder={inputSchema.type === 'json' ? '{\n  "key": "value"\n}' : '[\n  "item1",\n  "item2"\n]'}
                                    className="font-mono text-xs min-h-[80px] bg-slate-950 border-slate-800 text-emerald-300 resize-y focus-visible:ring-emerald-500/50 placeholder:text-slate-700"
                                    value={formData[key] || ''}
                                    onChange={(e) => onInputChange(key, e.target.value)}
                                    spellCheck={false}
                                />
                            ) : inputSchema.type === 'boolean' ? (
                                <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950 border border-slate-800">
                                    <span className="text-xs text-slate-400">{formData[key] === 'true' ? 'Enabled' : 'Disabled'}</span>
                                    <Switch
                                        checked={formData[key] === 'true'}
                                        onCheckedChange={(checked) => onInputChange(key, String(checked))}
                                        className="data-[state=checked]:bg-emerald-500"
                                    />
                                </div>
                            ) : (
                                <Input
                                    placeholder={`Enter ${key}...`}
                                    className="h-9 bg-slate-950 border-slate-800 text-white text-xs focus-visible:ring-emerald-500/50 placeholder:text-slate-600"
                                    type={inputSchema.type === 'number' ? 'number' : 'text'}
                                    value={formData[key] || ''}
                                    onChange={(e) => onInputChange(key, e.target.value)}
                                />
                            )}
                        </div>
                        {inputSchema.description && (
                            <p className="text-[10px] text-slate-500 leading-relaxed px-1">{inputSchema.description}</p>
                        )}
                    </div>
                ))}

                <div className="pt-2">
                    <Button
                        className="w-full h-8 bg-emerald-600 hover:bg-emerald-700 text-white text-xs shadow-sm shadow-emerald-900/20"
                        onClick={onExecute}
                    >
                        <Play className="h-3.5 w-3.5 mr-2" /> Run Activity
                    </Button>
                </div>
            </div>
        </ScrollArea>
    )
}
