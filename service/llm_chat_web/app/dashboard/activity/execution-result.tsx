import { CheckCircle2, XCircle, Clock, Terminal, ArrowRight, Activity } from "lucide-react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

interface ExecutionResultProps {
    output: string | null
}

export function ExecutionResult({ output }: ExecutionResultProps) {
    if (!output) return null

    let data
    try {
        data = JSON.parse(output)
    } catch (e) {
        return <div className="p-4 text-red-400 text-xs">Failed to parse output</div>
    }

    const isSuccess = data.status === 'success'

    return (
        <div className="flex flex-col h-full bg-slate-950 border-l border-slate-800">
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/50">
                <div className="flex items-center gap-2">
                    {isSuccess ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                    ) : (
                        <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    <span className={`text-sm font-medium ${isSuccess ? 'text-emerald-400' : 'text-red-400'}`}>
                        {isSuccess ? 'Execution Successful' : 'Execution Failed'}
                    </span>
                </div>
                <Badge variant="outline" className="text-[10px] border-slate-700 text-slate-500 font-mono">
                    {data.duration || '0ms'}
                </Badge>
            </div>

            <Tabs defaultValue="output" className="flex-1 flex flex-col overflow-hidden">
                <div className="px-4 pt-2">
                    <TabsList className="bg-slate-900 border border-slate-800 h-8 w-full justify-start p-0.5">
                        <TabsTrigger value="output" className="h-7 text-[10px] data-[state=active]:bg-slate-800 data-[state=active]:text-emerald-400">Output</TabsTrigger>
                        <TabsTrigger value="inputs" className="h-7 text-[10px] data-[state=active]:bg-slate-800 data-[state=active]:text-blue-400">Inputs</TabsTrigger>
                        <TabsTrigger value="logs" className="h-7 text-[10px] data-[state=active]:bg-slate-800 data-[state=active]:text-yellow-400">Logs</TabsTrigger>
                        <TabsTrigger value="raw" className="h-7 text-[10px] data-[state=active]:bg-slate-800 data-[state=active]:text-slate-400">Raw JSON</TabsTrigger>
                    </TabsList>
                </div>

                <div className="flex-1 overflow-hidden p-4">
                    <TabsContent value="output" className="h-full m-0">
                        <ScrollArea className="h-full rounded-lg border border-slate-800 bg-slate-900/50 p-3">
                            {data.outputs || data.response ? (
                                <div className="space-y-2">
                                    {Object.entries(data.outputs || data.response).map(([key, value]) => (
                                        <div key={key} className="group">
                                            <div className="flex items-center gap-2 mb-1">
                                                <ArrowRight className="h-3 w-3 text-slate-600" />
                                                <span className="text-xs font-medium text-slate-300">{key}</span>
                                            </div>
                                            <pre className="ml-5 text-[10px] font-mono text-emerald-300/90 whitespace-pre-wrap break-all">
                                                {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                                            </pre>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-xs text-slate-500 italic">No output data</div>
                            )}
                        </ScrollArea>
                    </TabsContent>

                    <TabsContent value="inputs" className="h-full m-0">
                        <ScrollArea className="h-full rounded-lg border border-slate-800 bg-slate-900/50 p-3">
                            <div className="space-y-2">
                                {Object.entries(data.inputs || {}).map(([key, value]) => (
                                    <div key={key} className="group">
                                        <div className="flex items-center gap-2 mb-1">
                                            <div className="h-1.5 w-1.5 rounded-full bg-blue-500/50" />
                                            <span className="text-xs font-medium text-slate-300">{key}</span>
                                        </div>
                                        <div className="ml-3.5 px-2 py-1.5 rounded bg-slate-950 border border-slate-800/50 text-[10px] font-mono text-blue-200/80 break-all">
                                            {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </ScrollArea>
                    </TabsContent>

                    <TabsContent value="logs" className="h-full m-0">
                        <ScrollArea className="h-full rounded-lg border border-slate-800 bg-slate-950 p-3">
                            {data.logs && data.logs.length > 0 ? (
                                <div className="space-y-1">
                                    {data.logs.map((log: string, i: number) => (
                                        <div key={i} className="flex gap-2 text-[10px] font-mono border-b border-slate-800/50 last:border-0 pb-1 last:pb-0">
                                            <span className="text-slate-600 shrink-0">[{new Date().toLocaleTimeString()}]</span>
                                            <span className={log.includes('[ERROR]') ? 'text-red-400' : log.includes('[WARN]') ? 'text-yellow-400' : 'text-slate-300'}>
                                                {log}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="flex flex-col items-center justify-center h-full text-slate-600 gap-2">
                                    <Terminal className="h-8 w-8 opacity-20" />
                                    <span className="text-xs">No logs captured</span>
                                </div>
                            )}
                        </ScrollArea>
                    </TabsContent>

                    <TabsContent value="raw" className="h-full m-0">
                        <ScrollArea className="h-full rounded-lg border border-slate-800 bg-slate-950 p-3">
                            <pre className="text-[10px] font-mono text-slate-400 whitespace-pre-wrap">
                                {JSON.stringify(data, null, 2)}
                            </pre>
                        </ScrollArea>
                    </TabsContent>
                </div>
            </Tabs>
        </div>
    )
}
