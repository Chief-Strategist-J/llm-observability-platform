import { ScrollArea } from "@/components/ui/scroll-area"
import { activityComponents, categoryColors, type ActivityComponent } from "./activity-data"
import { GripVertical } from "lucide-react"

import { Sparkles } from "lucide-react"

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

interface ActivityListProps {
    onDragStart: (event: React.DragEvent, component: ActivityComponent) => void
    customActivities?: CustomActivity[]
}

export function ActivityList({ onDragStart, customActivities = [] }: ActivityListProps) {
    const allComponents = [
        ...activityComponents,
        ...customActivities.map(ca => ({
            id: ca.id,
            name: ca.name,
            icon: Sparkles,
            category: "custom",
            description: ca.description
        }))
    ]

    const categoryGroups = allComponents.reduce((acc, component) => {
        if (!acc[component.category]) {
            acc[component.category] = []
        }
        acc[component.category].push(component)
        return acc
    }, {} as Record<string, typeof activityComponents>)

    const getCategoryColor = (category: string) => {
        return categoryColors[category] || "bg-gray-500"
    }

    return (
        <div className="h-full min-h-0 flex flex-col bg-slate-900 border-r border-slate-800 overflow-hidden">
            <div className="p-4 border-b border-slate-800 shrink-0">
                <h2 className="text-sm font-semibold text-white tracking-tight">Activities</h2>
                <p className="text-xs text-slate-500 mt-0.5">{allComponents.length} available • Drag to canvas</p>
            </div>
            <ScrollArea className="flex-1 min-h-0">
                <div className="p-3 space-y-5">
                    {Object.entries(categoryGroups).map(([category, components]) => (
                        <div key={category}>
                            <h3 className="text-[10px] font-semibold uppercase text-slate-500 mb-2 px-1 tracking-wider">
                                {category}
                            </h3>
                            <div className="space-y-1">
                                {components.map((component) => {
                                    const Icon = component.icon
                                    return (
                                        <div
                                            key={component.id}
                                            className="flex items-center gap-2.5 p-2.5 rounded-lg bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 hover:border-slate-600 cursor-grab active:cursor-grabbing transition-all group"
                                            draggable
                                            onDragStart={(e) => onDragStart(e, component)}
                                        >
                                            <div className={`p-1.5 rounded-md ${getCategoryColor(component.category)} shadow-sm`}>
                                                <Icon className="h-3.5 w-3.5 text-white" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-xs font-medium text-white truncate leading-tight">{component.name}</p>
                                                <p className="text-[10px] text-slate-500 truncate leading-tight mt-0.5">{component.description}</p>
                                            </div>
                                            <GripVertical className="h-3.5 w-3.5 text-slate-600 opacity-0 group-hover:opacity-100 transition-opacity" />
                                        </div>
                                    )
                                })}
                            </div>
                        </div>
                    ))}
                </div>
            </ScrollArea>
        </div>
    )
}
