'use client'

import React, { useMemo, useState } from 'react'
import { GraphCanvas, GraphNode, GraphEdge, lightTheme } from 'reagraph'
import { groupChatApi, type Comment } from '@/utils/api/group-chat-client'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Textarea } from '@/components/ui/textarea'
import { Empty, EmptyHeader, EmptyTitle, EmptyDescription, EmptyMedia } from '@/components/ui/empty'
import { X, ThumbsUp, ThumbsDown, MessageSquare, Network, Loader2, Send } from 'lucide-react'

// Galaxy star colors with shade variations (light, normal, dark)
const STAR_COLOR_PALETTES = [
    {
        light: '#ffb366',
        normal: '#fb923c',
        dark: '#ea580c',
        name: 'Orange'
    },
    {
        light: '#60a5fa',
        normal: '#3b82f6',
        dark: '#1d4ed8',
        name: 'Blue'
    },
    {
        light: '#4ade80',
        normal: '#22c55e',
        dark: '#15803d',
        name: 'Green'
    },
    {
        light: '#c084fc',
        normal: '#a855f7',
        dark: '#7e22ce',
        name: 'Purple'
    },
    {
        light: '#22d3ee',
        normal: '#06b6d4',
        dark: '#0e7490',
        name: 'Cyan'
    },
    {
        light: '#f472b6',
        normal: '#ec4899',
        dark: '#be185d',
        name: 'Pink'
    },
    {
        light: '#fbbf24',
        normal: '#eab308',
        dark: '#ca8a04',
        name: 'Yellow'
    },
    {
        light: '#fb923c',
        normal: '#f97316',
        dark: '#c2410c',
        name: 'Deep Orange'
    }
]

// Helper to get random shade variation
const getRandomShade = (palette: typeof STAR_COLOR_PALETTES[0]) => {
    const shades = [palette.light, palette.normal, palette.dark]
    const weights = [0.3, 0.5, 0.2] // 30% light, 50% normal, 20% dark
    const rand = Math.random()
    if (rand < weights[0]) return { color: palette.light, brightness: 'light' }
    if (rand < weights[0] + weights[1]) return { color: palette.normal, brightness: 'normal' }
    return { color: palette.dark, brightness: 'dark' }
}

// Neural network galaxy theme - realistic glowing neurons
const galaxyTheme = {
    ...lightTheme,
    canvas: {
        background: '#0a0015', // Deep space purple-black
        fog: '#0a0015'
    },
    node: {
        fill: '#ff9500',
        activeFill: '#ffb84d',
        opacity: 1,
        selectedOpacity: 1,
        inactiveOpacity: 1.0,
        label: {
            color: '#ffffff',
            stroke: '#0a0015',
            activeColor: '#fff5e6',
            fontSize: 12,
            fontWeight: 600
        }
    },
    edge: {
        fill: '#a78bfa', // Brighter purple for better visibility
        activeFill: '#c4b5fd',
        opacity: 0.85, // Good visibility without being overwhelming
        selectedOpacity: 1,
        inactiveOpacity: 0.5,
        label: {
            stroke: '#0a0015',
            color: '#c4b5fd',
            activeColor: '#e9d5ff',
            fontSize: 0 // Hide edge labels for cleaner look
        }
    },
    cluster: {
        stroke: '#7c3aed',
        opacity: 0.5,
        selectedOpacity: 0.7,
        inactiveOpacity: 0.2,
        label: {
            stroke: '#0a0015',
            color: '#c4b5fd',
            fontSize: 12
        }
    }
}

interface GraphVisualizationProps {
    discussions: Comment[]
    onRefresh?: () => Promise<void>
    static?: boolean
}

export function GraphVisualization({ discussions, onRefresh, static: isStatic = false }: GraphVisualizationProps) {
    const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
    const [replyText, setReplyText] = useState("")
    const [isReplying, setIsReplying] = useState(false)
    const [showReplyInput, setShowReplyInput] = useState(false)

    // Transform discussions into galaxy nodes (stars) and edges (cosmic connections)
    const { nodes, edges } = useMemo(() => {
        const graphNodes: GraphNode[] = []
        const graphEdges: GraphEdge[] = []
        const processedIds = new Set<string>()
        const conversationColors = new Map<string, typeof STAR_COLOR_PALETTES[0]>()
        let colorIndex = 0

        const processComment = (comment: Comment, parentId?: string, rootId?: string) => {
            // Validate required fields to prevent NaN errors
            if (!comment || (!comment._id && !comment.id)) {
                console.warn('Skipping invalid comment:', comment)
                return
            }

            const nodeId = comment._id || comment.id.toString()

            // Avoid duplicates
            if (processedIds.has(nodeId)) return
            processedIds.add(nodeId)

            // Validate content to prevent NaN errors
            const content = comment.content || 'No content'
            const author = comment.author || 'Anonymous'

            // Assign color palette based on root conversation
            const conversationRootId = rootId || nodeId
            if (!conversationColors.has(conversationRootId)) {
                conversationColors.set(
                    conversationRootId,
                    STAR_COLOR_PALETTES[colorIndex % STAR_COLOR_PALETTES.length]
                )
                colorIndex++
            }
            const palette = conversationColors.get(conversationRootId)!

            // Get random shade variation for this specific star
            const { color: starColor, brightness } = getRandomShade(palette)

            // Calculate dynamic node size based on engagement (reduced scaling for smaller bubbles)
            // More upvotes, replies, and activity = larger node
            const engagement = (comment.upvotes || 0) + (comment.replies?.length || 0) * 2 + (comment.downvotes || 0) * 0.5
            const nodeSize = Math.min(Math.max(8 + engagement * 1.2, 8), 25)

            // Create label with content preview
            const contentPreview = content.length > 40
                ? content.substring(0, 40) + '...'
                : content

            const nodeLabel = `${author}: ${contentPreview}`

            graphNodes.push({
                id: nodeId,
                label: nodeLabel,
                fill: starColor, // Each star gets a unique shade
                size: nodeSize, // Dynamic size based on engagement
                data: {
                    id: comment.id, // Keep numeric ID for API calls if needed, though we use _id mostly
                    _id: comment._id,
                    content: content,
                    author: author,
                    avatar: comment.avatar,
                    time: comment.time,
                    upvotes: comment.upvotes || 0,
                    downvotes: comment.downvotes || 0,
                    userVote: comment.userVote,
                    replies: comment.replies?.length || 0,
                    starColor: starColor,
                    brightness: brightness,
                    palette: palette.name,
                    engagement: engagement
                }
            })

            // Create edge from parent to this node
            if (parentId && nodeId !== parentId) {
                graphEdges.push({
                    id: `${parentId}-${nodeId}`,
                    source: parentId,
                    target: nodeId,
                    label: ''
                })
            }

            // Process replies recursively
            if (comment.replies && comment.replies.length > 0) {
                comment.replies.forEach(reply => {
                    processComment(reply, nodeId, conversationRootId)
                })
            }
        }

        // Process all top-level discussions
        if (discussions && Array.isArray(discussions) && discussions.length > 0) {
            discussions.forEach(discussion => {
                processComment(discussion)
            })
        }

        // Prevent THREE.js NaN errors by ensuring valid data
        if (graphNodes.length === 0) {
            console.warn('No valid discussions to visualize')
        }

        return { nodes: graphNodes, edges: graphEdges }
    }, [discussions])

    const handleNodeClick = (node: any) => {
        setSelectedNode(node)
        setShowReplyInput(false)
        setReplyText("")
    }

    const handleCanvasClick = () => {
        setSelectedNode(null)
        setShowReplyInput(false)
        setReplyText("")
    }

    const handleReply = async () => {
        if (!selectedNode || !replyText.trim() || isReplying) return

        try {
            setIsReplying(true)
            const parentId = selectedNode.data._id

            if (!parentId) {
                console.error('No parent ID found for node:', selectedNode)
                return
            }

            const response = await groupChatApi.addReply(parentId, {
                author: 'You',
                avatar: '/avatars/shadcn.jpg',
                content: replyText
            })

            if (response.success) {
                setReplyText("")
                setShowReplyInput(false)
                await onRefresh?.() // Refresh data to show new node
            } else {
                console.error('Failed to reply:', response.error)
            }
        } catch (error) {
            console.error('Error replying:', error)
        } finally {
            setIsReplying(false)
        }
    }

    return (
        <div className="relative w-full h-full bg-gradient-to-br from-[#0a0015] via-[#1a0033] to-[#0a0015]">
            {/* Animations for edges and stars */}
            <style jsx>{`
        @keyframes edgeFlow {
          0%, 100% {
            opacity: 0.7;
          }
          50% {
            opacity: 1;
          }
        }
        
        @keyframes starTwinkle {
          0%, 100% {
            opacity: 0.9;
            transform: scale(1);
          }
          50% {
            opacity: 1;
            transform: scale(1.05);
          }
        }
      `}</style>

            {/* Graph Canvas - Neural Galaxy */}
            {nodes.length > 0 && (
                <div className="absolute inset-0 galaxy-canvas">
                    <GraphCanvas
                        layoutType={isStatic ? "hierarchicalTd" : "forceDirected3d"}
                        nodes={nodes}
                        edges={edges}
                        theme={galaxyTheme}
                        cameraMode={isStatic ? "rotate" : "pan"}
                        draggable
                        labelType="all"
                        edgeArrowPosition="none"
                        edgeInterpolation="curved"
                        defaultNodeSize={14}
                        minNodeSize={8}
                        maxNodeSize={28}
                        sizingType="centrality"
                        animated={true}
                        onNodeClick={isStatic ? undefined : handleNodeClick}
                        onCanvasClick={handleCanvasClick}
                    />

                    {/* Subtle flowing glow on edges only */}
                    <div
                        className="absolute inset-0 pointer-events-none"
                        style={{
                            background:
                                'radial-gradient(circle at 50% 50%, rgba(139, 92, 246, 0.08) 0%, transparent 60%)',
                            animation: 'edgeFlow 4s ease-in-out infinite'
                        }}
                    />
                </div>
            )}

            {/* Info Panel - Shows selected star details */}
            {selectedNode && selectedNode.data && (
                <Card className="absolute top-4 right-4 w-96 shadow-2xl max-h-[calc(100vh-8rem)] overflow-y-auto border-slate-700/50 bg-slate-950/95 backdrop-blur-md">
                    <CardHeader className="pb-3 border-b border-slate-800/50">
                        <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0 space-y-2">
                                <div className="flex items-center gap-2">
                                    {selectedNode.data.starColor && (
                                        <div
                                            className="w-3 h-3 rounded-full animate-pulse shadow-lg"
                                            style={{
                                                backgroundColor: selectedNode.data.starColor,
                                                boxShadow: `0 0 12px ${selectedNode.data.starColor}, 0 0 24px ${selectedNode.data.starColor}40`
                                            }}
                                        />
                                    )}
                                    <CardTitle className="text-base font-semibold text-white">
                                        {selectedNode.data.author}
                                    </CardTitle>
                                </div>
                                <p className="text-xs text-slate-400">
                                    {selectedNode.data.time}
                                </p>
                            </div>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setSelectedNode(null)}
                                className="h-8 w-8 p-0 shrink-0 text-slate-400 hover:text-white hover:bg-slate-800"
                            >
                                <X className="h-4 w-4" />
                            </Button>
                        </div>
                    </CardHeader>
                    <CardContent className="space-y-4 pt-4">
                        <div className="bg-slate-900/50 rounded-lg p-3 border border-slate-800/30">
                            <p className="text-sm leading-relaxed whitespace-pre-wrap break-words text-slate-200">
                                {selectedNode.data.content}
                            </p>
                        </div>

                        <Separator className="bg-slate-800/50" />

                        <div className="flex items-center gap-2 flex-wrap">
                            <Badge variant="secondary" className="gap-1.5 bg-slate-800/50 text-slate-200 border-slate-700/50">
                                <ThumbsUp className="h-3 w-3 text-green-400" />
                                <span className="font-medium">{selectedNode.data.upvotes}</span>
                            </Badge>
                            <Badge variant="secondary" className="gap-1.5 bg-slate-800/50 text-slate-200 border-slate-700/50">
                                <ThumbsDown className="h-3 w-3 text-red-400" />
                                <span className="font-medium">{selectedNode.data.downvotes}</span>
                            </Badge>
                            <Badge variant="secondary" className="gap-1.5 bg-slate-800/50 text-slate-200 border-slate-700/50">
                                <MessageSquare className="h-3 w-3 text-blue-400" />
                                <span className="font-medium">{selectedNode.data.replies}</span>
                            </Badge>
                        </div>

                        {/* Reply Section */}
                        <div className="pt-2">
                            {!showReplyInput ? (
                                <Button
                                    className="w-full bg-indigo-600 hover:bg-indigo-700 text-white"
                                    onClick={() => setShowReplyInput(true)}
                                >
                                    <MessageSquare className="h-4 w-4 mr-2" />
                                    Reply to this node
                                </Button>
                            ) : (
                                <div className="space-y-3 animate-in fade-in slide-in-from-top-2">
                                    <Textarea
                                        placeholder="Write your reply..."
                                        value={replyText}
                                        onChange={(e) => setReplyText(e.target.value)}
                                        className="bg-slate-900/50 border-slate-700 text-slate-200 min-h-[80px]"
                                    />
                                    <div className="flex gap-2">
                                        <Button
                                            className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white"
                                            onClick={handleReply}
                                            disabled={!replyText.trim() || isReplying}
                                        >
                                            {isReplying ? (
                                                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                            ) : (
                                                <Send className="h-4 w-4 mr-2" />
                                            )}
                                            Send Reply
                                        </Button>
                                        <Button
                                            variant="outline"
                                            className="border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white"
                                            onClick={() => {
                                                setShowReplyInput(false)
                                                setReplyText("")
                                            }}
                                        >
                                            Cancel
                                        </Button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Stats Panel - Galaxy Statistics */}
            <Card className="absolute bottom-4 left-4 shadow-2xl border-slate-700/50 bg-slate-950/95 backdrop-blur-md">
                <CardContent className="p-4 space-y-2">
                    <div className="flex items-center gap-2 text-sm font-medium text-white">
                        <Network className="h-4 w-4 text-cyan-400" />
                        <span>Galaxy Network</span>
                    </div>
                    <Separator className="bg-slate-800/50" />
                    <div className="space-y-1 text-sm">
                        <div className="flex justify-between gap-4">
                            <span className="text-slate-400">Stars</span>
                            <span className="font-mono font-medium text-slate-200">{nodes.length}</span>
                        </div>
                        <div className="flex justify-between gap-4">
                            <span className="text-slate-400">Connections</span>
                            <span className="font-mono font-medium text-slate-200">{edges.length}</span>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Instructions */}
            {!selectedNode && nodes.length > 0 && (
                <Card className="absolute top-4 right-4 shadow-2xl border-slate-700/50 bg-slate-950/95 backdrop-blur-md">
                    <CardContent className="p-3 space-y-1 text-xs text-slate-400">
                        <div>Drag to rotate galaxy • Scroll to zoom</div>
                        <div>Click stars to view messages</div>
                        <div>Drag stars to reposition</div>
                    </CardContent>
                </Card>
            )}

            {/* Empty State */}
            {nodes.length === 0 && (
                <div className="absolute inset-0 flex items-center justify-center p-4">
                    <Empty>
                        <EmptyHeader>
                            <EmptyMedia variant="icon">
                                <Network className="text-slate-600" />
                            </EmptyMedia>
                            <EmptyTitle className="text-slate-300">Empty Galaxy</EmptyTitle>
                            <EmptyDescription className="text-slate-500">
                                Start a conversation to see stars appear in your galaxy
                            </EmptyDescription>
                        </EmptyHeader>
                    </Empty>
                </div>
            )}
        </div>
    )
}
