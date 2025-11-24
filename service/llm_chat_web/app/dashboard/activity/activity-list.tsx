import { ScrollArea } from "@/components/ui/scroll-area"
import { activityComponents, categoryColors, type ActivityComponent } from "./activity-data"

interface ActivityListProps {
    onDragStart: (event: React.DragEvent, component: ActivityComponent) => void
}

export function ActivityList({ onDragStart }: ActivityListProps) {
    const categoryGroups = activityComponents.reduce((acc, component) => {
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
        <div className="h-full flex flex-col bg-background border-r">
            <div className="p-4 border-b">
                <h2 className="font-semibold mb-2">Activities</h2>
                <p className="text-xs text-muted-foreground">{activityComponents.length} available</p>
            </div>
            <ScrollArea className="flex-1">
                <div className="p-2 space-y-4">
                    {Object.entries(categoryGroups).map(([category, components]) => (
                        <div key={category}>
                            <h3 className="text-xs font-semibold uppercase text-muted-foreground mb-2 px-2">
                                {category}
                            </h3>
                            <div className="space-y-1">
                                {components.map((component) => {
                                    const Icon = component.icon
                                    return (
                                        <div
                                            key={component.id}
                                            className="flex items-center gap-2 p-2 rounded-md hover:bg-accent cursor-move transition-colors"
                                            draggable
                                            onDragStart={(e) => onDragStart(e, component)}
                                        >
                                            <div className={`p-1.5 rounded ${getCategoryColor(component.category)} shadow-sm`}>
                                                <Icon className="h-4 w-4 text-white" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium truncate">{component.name}</p>
                                                <p className="text-xs text-muted-foreground truncate">{component.description}</p>
                                            </div>
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
