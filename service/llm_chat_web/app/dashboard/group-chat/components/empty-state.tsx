import { LucideIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"

interface EmptyStateProps {
    icon: LucideIcon
    title: string
    description: string
    actionLabel?: string
    onAction?: () => void
}

export function EmptyState({
    icon: Icon,
    title,
    description,
    actionLabel,
    onAction
}: EmptyStateProps) {
    return (
        <Card className="p-12 border-dashed border-slate-700 bg-slate-900/30">
            <div className="flex flex-col items-center text-center max-w-md mx-auto">
                <div className="h-16 w-16 rounded-full bg-violet-500/20 flex items-center justify-center mb-4 ring-4 ring-violet-500/10">
                    <Icon className="h-8 w-8 text-violet-400" />
                </div>
                <h3 className="font-semibold text-xl mb-2 text-white">{title}</h3>
                <p className="text-slate-400 mb-6">
                    {description}
                </p>
                {actionLabel && onAction && (
                    <Button onClick={onAction} className="bg-violet-600 hover:bg-violet-700 text-white font-medium shadow-lg shadow-violet-500/20">
                        {actionLabel}
                    </Button>
                )}
            </div>
        </Card>
    )
}

