"use client"

import { GitCommit, Merge, Bot, User } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

export interface GraphMessage {
    id: string
    text: string
    sender: "me" | "friend" | "ai" | "user"
    time: string
    timestamp: number
    branchId: string
    type?: 'text' | 'merge'
    mergeSourceId?: string
    role?: 'user' | 'ai' // For AI messages
}

export interface GraphBranch {
    id: string
    title: string
    color: string
    status: 'active' | 'merged'
    mergedInto?: string
}

interface GitGraphViewProps {
    branches: GraphBranch[]
    messages: GraphMessage[]
    selectedBranchId?: string
    onSelectBranch: (id: string) => void
    friendAvatar?: string
    friendName?: string
}

export function GitGraphView({
    branches,
    messages,
    selectedBranchId,
    onSelectBranch,
    friendAvatar,
    friendName
}: GitGraphViewProps) {
    // 1. Prepare Data
    const activeBranches = branches.filter(b => b.status === 'active')
    const mergedBranches = branches.filter(b => b.status === 'merged')

    // Assign columns: Active first, then merged
    const getColumnIndex = (branchId: string) => {
        const activeIdx = activeBranches.findIndex(b => b.id === branchId)
        if (activeIdx !== -1) return activeIdx
        return activeBranches.length + mergedBranches.findIndex(b => b.id === branchId)
    }

    const sortedMessages = [...messages].sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0))

    const ROW_HEIGHT = 80
    const COL_WIDTH = 34
    const LEFT_PAD = 20
    const TOP_PAD = 20

    return (
        <div className="relative" style={{ height: sortedMessages.length * ROW_HEIGHT + 100 }}>
            {/* SVG Layer for Lines */}
            <svg className="absolute top-0 left-0 w-full h-full pointer-events-none overflow-visible">
                {/* Vertical Branch Lines */}
                {branches.map((branch) => {
                    const colIdx = getColumnIndex(branch.id)
                    const x = LEFT_PAD + (colIdx * COL_WIDTH)

                    // Find start and end Y for this branch
                    const branchMsgs = sortedMessages.filter(m => m.branchId === branch.id)
                    if (branchMsgs.length === 0) return null

                    const firstMsgIdx = sortedMessages.indexOf(branchMsgs[0]) // Topmost (newest)
                    const lastMsgIdx = sortedMessages.indexOf(branchMsgs[branchMsgs.length - 1]) // Bottommost (oldest)

                    const y1 = TOP_PAD + (firstMsgIdx * ROW_HEIGHT)
                    const y2 = TOP_PAD + (lastMsgIdx * ROW_HEIGHT)

                    return (
                        <line
                            key={branch.id}
                            x1={x} y1={y1}
                            x2={x} y2={y2 + ROW_HEIGHT} // Extend a bit down
                            stroke={branch.color}
                            strokeWidth="2"
                            strokeOpacity="0.2"
                        />
                    )
                })}

                {/* Merge Curves */}
                {sortedMessages.filter(m => m.type === 'merge').map(mergeMsg => {
                    const mergeIdx = sortedMessages.indexOf(mergeMsg)
                    const targetColIdx = getColumnIndex(mergeMsg.branchId)

                    // Find the source branch
                    const sourceBranch = branches.find(b => b.id === mergeMsg.mergeSourceId)

                    if (sourceBranch) {
                        const sourceColIdx = getColumnIndex(sourceBranch.id)

                        // Coordinates
                        const targetX = LEFT_PAD + (targetColIdx * COL_WIDTH)
                        const sourceX = LEFT_PAD + (sourceColIdx * COL_WIDTH)
                        const y = TOP_PAD + (mergeIdx * ROW_HEIGHT)

                        // Find the newest message of the source branch
                        const sourceMsgs = sortedMessages.filter(m => m.branchId === sourceBranch.id)
                        if (sourceMsgs.length > 0) {
                            const lastSourceMsgIdx = sortedMessages.indexOf(sourceMsgs[0]) // Newest of source

                            const sourceY = TOP_PAD + (lastSourceMsgIdx * ROW_HEIGHT)

                            // Bezier curve
                            const path = `M ${sourceX} ${sourceY} C ${sourceX} ${y - (ROW_HEIGHT / 2)}, ${targetX} ${sourceY + (ROW_HEIGHT / 2)}, ${targetX} ${y}`

                            return (
                                <path
                                    key={mergeMsg.id}
                                    d={path}
                                    fill="none"
                                    stroke={sourceBranch.color}
                                    strokeWidth="2"
                                    strokeOpacity="0.5"
                                    strokeDasharray="4 4"
                                />
                            )
                        }
                    }
                    return null
                })}
            </svg>

            {/* Commit Nodes */}
            {sortedMessages.map((message, idx) => {
                const branch = branches.find(b => b.id === message.branchId)
                if (!branch) return null

                const colIdx = getColumnIndex(message.branchId)
                const x = LEFT_PAD + (colIdx * COL_WIDTH)
                const y = TOP_PAD + (idx * ROW_HEIGHT)
                const isMerge = message.type === 'merge'
                const isMe = message.sender === 'me' || message.role === 'user'

                return (
                    <div
                        key={message.id}
                        className="absolute w-full flex items-center group"
                        style={{ top: y, height: ROW_HEIGHT }}
                    >
                        {/* Dot */}
                        <div
                            className={`absolute w-3 h-3 rounded-full border-2 z-10 transition-transform group-hover:scale-125 cursor-pointer ${isMerge ? 'bg-white' : 'bg-slate-950'}`}
                            style={{
                                left: x - 5,
                                borderColor: branch.color,
                                backgroundColor: !isMe && !isMerge ? branch.color : (isMerge ? branch.color : '#0f172a')
                            }}
                            onClick={() => onSelectBranch(message.branchId)}
                        />

                        {/* Card */}
                        <div
                            className={`absolute left-[200px] right-8 p-3 rounded-lg border transition-all cursor-pointer
                                ${!isMe && !isMerge ? 'bg-opacity-20' : 'bg-slate-900/40 hover:bg-slate-800/60'}
                            `}
                            style={{
                                borderColor: `${branch.color}30`,
                                backgroundColor: !isMe && !isMerge ? branch.color : undefined
                            }}
                            onClick={() => onSelectBranch(message.branchId)}
                        >
                            <div className="flex items-center gap-2 mb-1">
                                {isMerge ? <Merge className="h-3 w-3" style={{ color: branch.color }} /> : <GitCommit className="h-3 w-3 opacity-50" style={{ color: !isMe ? 'white' : branch.color }} />}
                                <span className={`text-[10px] font-mono ${!isMe && !isMerge ? 'text-white/70' : 'text-slate-500'}`}>{message.id.substring(0, 7)}</span>
                                <span className={`text-[10px] ${!isMe && !isMerge ? 'text-white/70' : 'text-slate-400'}`}>• {message.time}</span>
                                <Badge variant="outline" className={`ml-auto text-[10px] h-5 ${!isMe && !isMerge ? 'border-white/20 text-white' : 'border-slate-800 text-slate-400'}`}>
                                    {branch.title}
                                </Badge>
                            </div>
                            <div className="flex items-start gap-2">
                                {friendName ? (
                                    <Avatar className="h-5 w-5 mt-0.5">
                                        <AvatarImage src={isMe ? undefined : friendAvatar} />
                                        <AvatarFallback className={`text-[10px] ${!isMe && !isMerge ? 'bg-white/20 text-white' : 'bg-slate-800 text-slate-400'}`}>
                                            {isMe ? 'Me' : friendName[0]}
                                        </AvatarFallback>
                                    </Avatar>
                                ) : (
                                    // AI Icon
                                    message.role === 'ai' ? <Bot className="h-4 w-4 mt-0.5 text-slate-400" /> : <User className="h-4 w-4 mt-0.5 text-slate-400" />
                                )}
                                <p className={`text-sm font-mono line-clamp-2 ${!isMe && !isMerge ? 'text-white' : 'text-slate-300'}`}>
                                    {message.text}
                                </p>
                            </div>
                        </div>

                        {/* Connector Line (Horizontal) */}
                        <div
                            className="absolute h-px"
                            style={{
                                left: x + 6,
                                width: 200 - (x + 6),
                                background: `linear-gradient(90deg, ${branch.color}40, transparent)`
                            }}
                        />
                    </div>
                )
            })}
        </div>
    )
}
