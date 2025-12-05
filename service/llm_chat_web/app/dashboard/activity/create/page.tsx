"use client"

import { useState, useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ArrowLeft, Plus, Trash2, Save, Play, Code2, FileInput, FileOutput, Sparkles } from "lucide-react"

interface InputField {
    name: string
    type: string
    description: string
    required: boolean
}

interface OutputField {
    name: string
    type: string
    description: string
}

const FIELD_TYPES = ["string", "number", "boolean", "json", "array"]
const CATEGORIES = ["general", "configuration", "deployment", "logs", "metrics", "tracing", "testing", "custom"]

export default function CreateActivityPage() {
    const router = useRouter()
    const [activityName, setActivityName] = useState("")
    const [activityId, setActivityId] = useState("")
    const [description, setDescription] = useState("")
    const [category, setCategory] = useState("custom")
    const [inputs, setInputs] = useState<InputField[]>([{ name: "", type: "string", description: "", required: false }])
    const [outputs, setOutputs] = useState<OutputField[]>([{ name: "", type: "string", description: "" }])
    const [code, setCode] = useState(`async function process(inputs) {
  // Your activity logic here
  // Access inputs: inputs.fieldName
  
  // Example:
  // const result = await fetch(inputs.url);
  // const data = await result.json();
  
  return {
    // Return your outputs here
    success: true,
    message: "Activity completed"
  };
}`)
    const [testOutput, setTestOutput] = useState("")
    const [isTesting, setIsTesting] = useState(false)
    const searchParams = useSearchParams()
    const editId = searchParams.get('edit')

    useEffect(() => {
        if (editId) {
            const stored = localStorage.getItem('customActivities')
            if (stored) {
                const activities = JSON.parse(stored)
                const activity = activities.find((a: any) => a.id === editId)
                if (activity) {
                    setActivityName(activity.name)
                    setActivityId(activity.id)
                    setDescription(activity.description)
                    setCategory(activity.category)
                    setInputs(activity.inputs)
                    setOutputs(activity.outputs)
                    setCode(activity.code)
                }
            }
        }
    }, [editId])

    const loadDemo = () => {
        setActivityName("Demo: Fetch User")
        setActivityId("demo-fetch-user")
        setDescription("Fetches user data from a public API.")
        setCategory("testing")
        setInputs([{ name: "userId", type: "number", description: "User ID (1-10)", required: true }])
        setOutputs([{ name: "name", type: "string", description: "User Name" }, { name: "email", type: "string", description: "User Email" }])
        setCode(`async function process(inputs) {
  console.log("Fetching user:", inputs.userId);
  const res = await fetch(\`https://jsonplaceholder.typicode.com/users/\${inputs.userId}\`);
  const data = await res.json();
  return {
    name: data.name,
    email: data.email,
    fullData: data
  };
}`)
    }

    const generateId = (name: string) => {
        return name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
    }

    const handleNameChange = (name: string) => {
        setActivityName(name)
        setActivityId(generateId(name))
    }

    const addInput = () => {
        setInputs([...inputs, { name: "", type: "string", description: "", required: false }])
    }

    const updateInput = (index: number, field: keyof InputField, value: string | boolean) => {
        const updated = [...inputs]
        updated[index] = { ...updated[index], [field]: value }
        setInputs(updated)
    }

    const removeInput = (index: number) => {
        if (inputs.length > 1) setInputs(inputs.filter((_, i) => i !== index))
    }

    const addOutput = () => {
        setOutputs([...outputs, { name: "", type: "string", description: "" }])
    }

    const updateOutput = (index: number, field: keyof OutputField, value: string) => {
        const updated = [...outputs]
        updated[index] = { ...updated[index], [field]: value }
        setOutputs(updated)
    }

    const removeOutput = (index: number) => {
        if (outputs.length > 1) setOutputs(outputs.filter((_, i) => i !== index))
    }

    const handleTest = () => {
        setIsTesting(true)
        const mockInputs: Record<string, unknown> = {}
        inputs.forEach(inp => {
            switch (inp.type) {
                case 'string': mockInputs[inp.name] = `test-${inp.name}`; break
                case 'number': mockInputs[inp.name] = 42; break
                case 'boolean': mockInputs[inp.name] = true; break
                case 'json': mockInputs[inp.name] = { key: 'value' }; break
                case 'array': mockInputs[inp.name] = ['item1', 'item2']; break
            }
        })
        setTimeout(() => {
            const result = {
                status: "success",
                inputs: mockInputs,
                outputs: outputs.reduce((acc, out) => {
                    switch (out.type) {
                        case 'string': acc[out.name] = `result-${out.name}`; break
                        case 'number': acc[out.name] = 100; break
                        case 'boolean': acc[out.name] = true; break
                        case 'json': acc[out.name] = { result: 'data' }; break
                        case 'array': acc[out.name] = ['result1', 'result2']; break
                    }
                    return acc
                }, {} as Record<string, unknown>),
                executedAt: new Date().toISOString()
            }
            setTestOutput(JSON.stringify(result, null, 2))
            setIsTesting(false)
        }, 1000)
    }

    const handleSave = () => {
        const activity = {
            id: activityId,
            name: activityName,
            description,
            category,
            inputs: inputs.filter(i => i.name),
            outputs: outputs.filter(o => o.name),
            code,
            createdAt: new Date().toISOString()
        }
        const existing = JSON.parse(localStorage.getItem('customActivities') || '[]')
        if (editId) {
            const updated = existing.map((a: any) => a.id === editId ? activity : a)
            localStorage.setItem('customActivities', JSON.stringify(updated))
        } else {
            localStorage.setItem('customActivities', JSON.stringify([...existing, activity]))
        }
        router.push('/dashboard/activity')
    }

    const isValid = activityName && activityId && description && inputs.some(i => i.name) && outputs.some(o => o.name)

    return (
        <div className="flex flex-col h-screen bg-slate-950">
            <header className="flex h-14 shrink-0 items-center gap-3 border-b border-slate-800 px-4 bg-slate-900">
                <Button onClick={() => router.back()} size="sm" variant="ghost" className="h-8 w-8 p-0 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg">
                    <ArrowLeft className="h-4 w-4" />
                </Button>
                <Separator orientation="vertical" className="h-5 bg-slate-700" />
                <div className="flex items-center gap-2">
                    <div className="h-8 w-8 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                        <Sparkles className="h-4 w-4 text-emerald-400" />
                    </div>
                    <div>
                        <h1 className="text-sm font-semibold text-white tracking-tight">{editId ? 'Edit Activity' : 'Create Custom Activity'}</h1>
                        <p className="text-[10px] text-slate-500">{editId ? 'Modify existing activity logic' : 'Define inputs, outputs, and processing logic'}</p>
                    </div>
                </div>
                <div className="ml-auto flex items-center gap-2">
                    {!editId && (
                        <Button onClick={loadDemo} size="sm" variant="outline" className="h-8 px-3 bg-slate-800 border-slate-700 hover:bg-slate-700 text-slate-300 hover:text-white rounded-lg">
                            <Code2 className="h-3.5 w-3.5 mr-1.5" /> Load Demo
                        </Button>
                    )}
                    <Button onClick={handleTest} disabled={!isValid || isTesting} size="sm" className="h-8 px-3 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-lg border border-slate-700">
                        <Play className="h-3.5 w-3.5 mr-1.5" /> {isTesting ? "Testing..." : "Test Run"}
                    </Button>
                    <Button onClick={handleSave} disabled={!isValid} size="sm" className="h-8 px-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg shadow-sm shadow-emerald-900/20">
                        <Save className="h-3.5 w-3.5 mr-1.5" /> Save Activity
                    </Button>
                </div>
            </header>

            <div className="flex-1 flex overflow-hidden">
                <aside className="w-[400px] border-r border-slate-800 bg-slate-900/50 flex flex-col">
                    <ScrollArea className="flex-1">
                        <div className="p-6 space-y-8">
                            {/* Basic Info Section */}
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <Label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Activity Details</Label>
                                    <Badge variant="outline" className="text-[10px] border-slate-700 text-slate-500 bg-slate-800/50 font-mono">
                                        {activityId || 'ID: auto-generated'}
                                    </Badge>
                                </div>
                                <div className="space-y-3">
                                    <div className="space-y-1.5">
                                        <Label className="text-xs text-slate-300">Name</Label>
                                        <Input
                                            placeholder="e.g. Process Order"
                                            value={activityName}
                                            onChange={(e) => handleNameChange(e.target.value)}
                                            className="h-9 bg-slate-950 border-slate-800 text-white text-sm rounded-lg focus-visible:ring-emerald-500/50"
                                        />
                                    </div>
                                    <div className="space-y-1.5">
                                        <Label className="text-xs text-slate-300">Description</Label>
                                        <Textarea
                                            placeholder="What does this activity do?"
                                            value={description}
                                            onChange={(e) => setDescription(e.target.value)}
                                            className="min-h-[80px] bg-slate-950 border-slate-800 text-slate-300 text-sm rounded-lg resize-none focus-visible:ring-emerald-500/50"
                                        />
                                    </div>
                                    <div className="space-y-1.5">
                                        <Label className="text-xs text-slate-300">Category</Label>
                                        <Select value={category} onValueChange={setCategory}>
                                            <SelectTrigger className="h-9 bg-slate-950 border-slate-800 text-white text-sm rounded-lg focus:ring-emerald-500/50">
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent className="bg-slate-900 border-slate-800 rounded-lg">
                                                {CATEGORIES.map(cat => (
                                                    <SelectItem key={cat} value={cat} className="text-slate-300 focus:bg-slate-800 focus:text-white rounded-md capitalize">{cat}</SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>
                                </div>
                            </div>

                            <Separator className="bg-slate-800" />

                            {/* Inputs Section */}
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <Label className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                                        <FileInput className="h-3.5 w-3.5" /> Inputs
                                    </Label>
                                    <Button onClick={addInput} size="sm" variant="outline" className="h-6 px-2 text-[10px] bg-slate-800 border-slate-700 hover:bg-slate-700 text-slate-300 rounded">
                                        <Plus className="h-3 w-3 mr-1" /> Add Field
                                    </Button>
                                </div>
                                <div className="space-y-3">
                                    {inputs.map((inp, idx) => (
                                        <div key={idx} className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-3 hover:border-slate-700 transition-colors group">
                                            <div className="flex gap-2">
                                                <div className="flex-1 space-y-1">
                                                    <Input
                                                        placeholder="Field Name"
                                                        value={inp.name}
                                                        onChange={(e) => updateInput(idx, 'name', e.target.value)}
                                                        className="h-7 bg-slate-900 border-slate-800 text-white text-xs rounded focus-visible:ring-emerald-500/50"
                                                    />
                                                    {inp.name && (
                                                        <p className="text-[10px] text-slate-500 font-mono px-0.5 flex items-center gap-1">
                                                            Use: <span className="text-emerald-400 bg-emerald-500/10 px-1 rounded">inputs.{inp.name}</span>
                                                        </p>
                                                    )}
                                                </div>
                                                <Select value={inp.type} onValueChange={(v) => updateInput(idx, 'type', v)}>
                                                    <SelectTrigger className="h-7 w-24 bg-slate-900 border-slate-800 text-slate-300 text-xs rounded focus:ring-emerald-500/50">
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent className="bg-slate-900 border-slate-800 rounded-lg">
                                                        {FIELD_TYPES.map(t => (<SelectItem key={t} value={t} className="text-slate-300 text-xs focus:bg-slate-800 rounded-md">{t}</SelectItem>))}
                                                    </SelectContent>
                                                </Select>
                                                <Button onClick={() => removeInput(idx)} size="sm" className="h-7 w-7 p-0 bg-transparent hover:bg-red-500/10 text-slate-600 hover:text-red-400 rounded transition-colors">
                                                    <Trash2 className="h-3.5 w-3.5" />
                                                </Button>
                                            </div>
                                            <div className="flex items-center gap-3">
                                                <Input
                                                    placeholder="Description"
                                                    value={inp.description}
                                                    onChange={(e) => updateInput(idx, 'description', e.target.value)}
                                                    className="h-6 flex-1 bg-transparent border-0 border-b border-slate-800 rounded-none px-0 text-slate-400 text-[10px] focus-visible:ring-0 focus-visible:border-slate-600 placeholder:text-slate-600"
                                                />
                                                <label className="flex items-center gap-1.5 text-[10px] text-slate-400 cursor-pointer select-none hover:text-slate-300">
                                                    <input
                                                        type="checkbox"
                                                        checked={inp.required}
                                                        onChange={(e) => updateInput(idx, 'required', e.target.checked)}
                                                        className="rounded border-slate-700 bg-slate-900 text-emerald-500 focus:ring-emerald-500/20 h-3 w-3"
                                                    />
                                                    Required
                                                </label>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <Separator className="bg-slate-800" />

                            {/* Outputs Section */}
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <Label className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                                        <FileOutput className="h-3.5 w-3.5" /> Outputs
                                    </Label>
                                    <Button onClick={addOutput} size="sm" variant="outline" className="h-6 px-2 text-[10px] bg-slate-800 border-slate-700 hover:bg-slate-700 text-slate-300 rounded">
                                        <Plus className="h-3 w-3 mr-1" /> Add Field
                                    </Button>
                                </div>
                                <div className="space-y-3">
                                    {outputs.map((out, idx) => (
                                        <div key={idx} className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-3 hover:border-slate-700 transition-colors group">
                                            <div className="flex gap-2">
                                                <div className="flex-1 space-y-1">
                                                    <Input
                                                        placeholder="Field Name"
                                                        value={out.name}
                                                        onChange={(e) => updateOutput(idx, 'name', e.target.value)}
                                                        className="h-7 bg-slate-900 border-slate-800 text-white text-xs rounded focus-visible:ring-emerald-500/50"
                                                    />
                                                </div>
                                                <Select value={out.type} onValueChange={(v) => updateOutput(idx, 'type', v)}>
                                                    <SelectTrigger className="h-7 w-24 bg-slate-900 border-slate-800 text-slate-300 text-xs rounded focus:ring-emerald-500/50">
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent className="bg-slate-900 border-slate-800 rounded-lg">
                                                        {FIELD_TYPES.map(t => (<SelectItem key={t} value={t} className="text-slate-300 text-xs focus:bg-slate-800 rounded-md">{t}</SelectItem>))}
                                                    </SelectContent>
                                                </Select>
                                                <Button onClick={() => removeOutput(idx)} size="sm" className="h-7 w-7 p-0 bg-transparent hover:bg-red-500/10 text-slate-600 hover:text-red-400 rounded transition-colors">
                                                    <Trash2 className="h-3.5 w-3.5" />
                                                </Button>
                                            </div>
                                            <Input
                                                placeholder="Description"
                                                value={out.description}
                                                onChange={(e) => updateOutput(idx, 'description', e.target.value)}
                                                className="h-6 w-full bg-transparent border-0 border-b border-slate-800 rounded-none px-0 text-slate-400 text-[10px] focus-visible:ring-0 focus-visible:border-slate-600 placeholder:text-slate-600"
                                            />
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </ScrollArea>
                </aside>

                <main className="flex-1 flex flex-col bg-slate-950 relative">
                    <div className="flex items-center justify-between px-4 py-2 border-b border-slate-800 bg-slate-900/50">
                        <div className="flex items-center gap-2">
                            <Code2 className="h-4 w-4 text-emerald-500" />
                            <span className="text-xs font-medium text-slate-300">Implementation Logic</span>
                        </div>
                        <Badge variant="outline" className="text-[10px] border-slate-700 text-slate-500 bg-slate-800/50">JavaScript (Async)</Badge>
                    </div>

                    <div className="flex-1 flex relative">
                        <div className="flex-1 flex flex-col">
                            <Textarea
                                value={code}
                                onChange={(e) => setCode(e.target.value)}
                                className="flex-1 font-mono text-sm bg-slate-950 border-0 text-emerald-300 resize-none p-6 focus-visible:ring-0 rounded-none leading-relaxed"
                                spellCheck={false}
                                style={{ tabSize: 2 }}
                            />
                        </div>

                        {testOutput && (
                            <div className="w-96 border-l border-slate-800 bg-slate-900/95 backdrop-blur absolute right-0 top-0 bottom-0 shadow-2xl flex flex-col animate-in slide-in-from-right duration-200">
                                <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between bg-slate-900">
                                    <div className="flex items-center gap-2">
                                        <div className={`h-2 w-2 rounded-full ${JSON.parse(testOutput).status === 'success' ? 'bg-emerald-500' : 'bg-red-500'}`} />
                                        <span className="text-xs font-medium text-slate-300">Execution Result</span>
                                    </div>
                                    <Button onClick={() => setTestOutput("")} size="sm" variant="ghost" className="h-6 px-2 text-[10px] text-slate-500 hover:text-white hover:bg-slate-800 rounded">
                                        Close
                                    </Button>
                                </div>
                                <ScrollArea className="flex-1 p-4">
                                    <pre className="text-xs font-mono text-cyan-300 whitespace-pre-wrap leading-relaxed">{testOutput}</pre>
                                </ScrollArea>
                            </div>
                        )}
                    </div>
                </main>
            </div>
        </div>
    )
}
