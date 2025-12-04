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
        <Card className="p-12 border-dashed bg-gradient-to-br from-muted/30 to-background">
            <div className="flex flex-col items-center text-center max-w-md mx-auto">
                <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mb-4 ring-4 ring-primary/5">
                    <Icon className="h-8 w-8 text-primary" />
                </div>
                <h3 className="font-semibold text-xl mb-2">{title}</h3>
                <p className="text-muted-foreground mb-6">
                    {description}
                </p>
                {actionLabel && onAction && (
                    <Button onClick={onAction} className="shadow-sm">
                        {actionLabel}
                    </Button>
                )}
            </div>
        </Card>
    )
}
