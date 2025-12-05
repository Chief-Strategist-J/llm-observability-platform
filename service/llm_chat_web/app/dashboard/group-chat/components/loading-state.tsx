import { Loader2 } from "lucide-react"

interface LoadingStateProps {
    message?: string
}

export function LoadingState({ message = "Loading..." }: LoadingStateProps) {
    return (
        <div className="flex items-center justify-center py-16">
            <div className="flex flex-col items-center gap-3">
                <Loader2 className="h-8 w-8 animate-spin text-violet-400" />
                <p className="text-sm text-slate-400">{message}</p>
            </div>
        </div>
    )
}

