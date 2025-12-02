'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import * as THREE from 'three'
import { Button } from '@/components/ui/button'
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { Comment } from '@/utils/api/group-chat-client'

type VisualNode = {
    id: number
    parentId?: number
    author: string
    content: string
    time: string
    depth: number
    upvotes: number
    downvotes: number
}

const flattenDiscussions = (comments: Comment[], depth = 0, parentId?: number): VisualNode[] => {
    return comments.flatMap(comment => {
        const current: VisualNode = {
            id: comment.id,
            parentId,
            author: comment.author,
            content: comment.content,
            time: comment.time,
            depth,
            upvotes: comment.upvotes,
            downvotes: comment.downvotes
        }
        const children = comment.replies ? flattenDiscussions(comment.replies, depth + 1, comment.id) : []
        return [current, ...children]
    })
}

export function GroupChat3DVisualizer({ discussions }: { discussions: Comment[] }) {
    const [open, setOpen] = useState(false)
    const [selectedNode, setSelectedNode] = useState<VisualNode | null>(null)
    const [hoveredId, setHoveredId] = useState<number | null>(null)

    const containerRef = useRef<HTMLDivElement | null>(null)
    const sceneRef = useRef<THREE.Scene | null>(null)
    const cameraRef = useRef<THREE.PerspectiveCamera | null>(null)
    const rendererRef = useRef<THREE.WebGLRenderer | null>(null)
    const animationFrameRef = useRef<number>()
    const raycasterRef = useRef(new THREE.Raycaster())
    const mouseRef = useRef(new THREE.Vector2())
    const isDraggingRef = useRef(false)
    const previousMousePositionRef = useRef({ x: 0, y: 0 })
    const rotationRef = useRef({ x: 0, y: 0 })
    const nodesRef = useRef<THREE.Mesh[]>([])
    const linesRef = useRef<THREE.Line[]>([])
    const hoveredIdRef = useRef<number | null>(null)

    const visualNodes = useMemo(() => flattenDiscussions(discussions), [discussions])

    useEffect(() => {
        if (!open || !containerRef.current) {
            return
        }

        const container = containerRef.current
        const width = container.clientWidth
        const height = container.clientHeight

        const scene = new THREE.Scene()
        scene.background = new THREE.Color(0x030712)
        scene.fog = new THREE.Fog(0x030712, 10, 60)
        sceneRef.current = scene

        const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000)
        camera.position.set(0, 6, 14)
        cameraRef.current = camera

        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
        renderer.setPixelRatio(window.devicePixelRatio)
        renderer.setSize(width, height)
        container.appendChild(renderer.domElement)
        rendererRef.current = renderer

        const ambientLight = new THREE.AmbientLight(0x7dd3fc, 0.4)
        const warmLight = new THREE.PointLight(0xfb923c, 1.2, 60)
        warmLight.position.set(12, 12, 8)
        const coolLight = new THREE.PointLight(0x38bdf8, 1, 50)
        coolLight.position.set(-10, 5, -12)
        scene.add(ambientLight, warmLight, coolLight)

        const particlesGeometry = new THREE.BufferGeometry()
        const particlesCount = 800
        const positions = new Float32Array(particlesCount * 3)
        for (let i = 0; i < particlesCount * 3; i += 3) {
            positions[i] = (Math.random() - 0.5) * 80
            positions[i + 1] = (Math.random() - 0.5) * 60
            positions[i + 2] = (Math.random() - 0.5) * 80
        }
        particlesGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
        const particlesMaterial = new THREE.PointsMaterial({
            size: 0.08,
            color: 0x38bdf8,
            transparent: true,
            opacity: 0.35
        })
        const particlesMesh = new THREE.Points(particlesGeometry, particlesMaterial)
        scene.add(particlesMesh)

        const onMouseDown = (event: MouseEvent) => {
            isDraggingRef.current = true
            previousMousePositionRef.current = { x: event.clientX, y: event.clientY }
        }

        const onMouseMove = (event: MouseEvent) => {
            if (!rendererRef.current) return
            const rect = rendererRef.current.domElement.getBoundingClientRect()
            mouseRef.current.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
            mouseRef.current.y = -((event.clientY - rect.top) / rect.height) * 2 + 1

            if (!isDraggingRef.current) return

            const deltaX = event.clientX - previousMousePositionRef.current.x
            const deltaY = event.clientY - previousMousePositionRef.current.y

            rotationRef.current.y += deltaX * 0.005
            rotationRef.current.x = Math.min(Math.max(rotationRef.current.x + deltaY * 0.003, -Math.PI / 3), Math.PI / 3)

            previousMousePositionRef.current = { x: event.clientX, y: event.clientY }
        }

        const onMouseUp = () => {
            isDraggingRef.current = false
        }

        const onWheel = (event: WheelEvent) => {
            event.preventDefault()
            if (!cameraRef.current) return
            cameraRef.current.position.z = Math.min(Math.max(cameraRef.current.position.z + event.deltaY * 0.01, 6), 26)
        }

        const onClick = () => {
            if (!sceneRef.current || !cameraRef.current || !rendererRef.current || isDraggingRef.current) return
            raycasterRef.current.setFromCamera(mouseRef.current, cameraRef.current)
            const intersects = raycasterRef.current.intersectObjects(nodesRef.current)

            if (intersects.length > 0) {
                const nodeId = intersects[0].object.userData.nodeId as number
                const node = visualNodes.find(item => item.id === nodeId) || null
                setSelectedNode(node)
            }
        }

        const handleResize = () => {
            if (!rendererRef.current || !cameraRef.current || !containerRef.current) return
            const { clientWidth, clientHeight } = containerRef.current
            cameraRef.current.aspect = clientWidth / clientHeight
            cameraRef.current.updateProjectionMatrix()
            rendererRef.current.setSize(clientWidth, clientHeight)
        }

        const animate = () => {
            animationFrameRef.current = requestAnimationFrame(animate)
            if (!cameraRef.current || !rendererRef.current || !sceneRef.current) return

            const rotation = rotationRef.current
            const camera = cameraRef.current
            const distance = Math.sqrt(camera.position.x ** 2 + camera.position.z ** 2)
            camera.position.x = Math.sin(rotation.y) * distance
            camera.position.z = Math.cos(rotation.y) * distance
            camera.position.y = 4 + Math.sin(rotation.x) * 6
            camera.lookAt(0, 0, 0)

            raycasterRef.current.setFromCamera(mouseRef.current, camera)
            const intersects = raycasterRef.current.intersectObjects(nodesRef.current)
            if (intersects.length > 0) {
                const nodeId = intersects[0].object.userData.nodeId as number
                if (hoveredIdRef.current !== nodeId) {
                    hoveredIdRef.current = nodeId
                    setHoveredId(nodeId)
                }
            } else if (hoveredIdRef.current !== null) {
                hoveredIdRef.current = null
                setHoveredId(null)
            }

            nodesRef.current.forEach((mesh, index) => {
                mesh.position.y = (mesh.userData.baseY as number) + Math.sin(Date.now() * 0.001 + index) * 0.1
                mesh.rotation.y += 0.002
            })

            particlesMesh.rotation.y += 0.0002

            rendererRef.current.render(sceneRef.current, camera)
        }

        renderer.domElement.addEventListener('mousedown', onMouseDown)
        renderer.domElement.addEventListener('mousemove', onMouseMove)
        renderer.domElement.addEventListener('mouseup', onMouseUp)
        renderer.domElement.addEventListener('wheel', onWheel)
        renderer.domElement.addEventListener('click', onClick)
        window.addEventListener('resize', handleResize)
        animate()

        return () => {
            cancelAnimationFrame(animationFrameRef.current ?? 0)
            window.removeEventListener('resize', handleResize)
            renderer.domElement.removeEventListener('mousedown', onMouseDown)
            renderer.domElement.removeEventListener('mousemove', onMouseMove)
            renderer.domElement.removeEventListener('mouseup', onMouseUp)
            renderer.domElement.removeEventListener('wheel', onWheel)
            renderer.domElement.removeEventListener('click', onClick)
            renderer.dispose()
            container.removeChild(renderer.domElement)
            scene.clear()
            nodesRef.current = []
            linesRef.current = []
            setHoveredId(null)
            hoveredIdRef.current = null
        }
    }, [open, visualNodes])

    useEffect(() => {
        if (!open || !sceneRef.current) return

        nodesRef.current.forEach(node => sceneRef.current?.remove(node))
        linesRef.current.forEach(line => sceneRef.current?.remove(line))
        nodesRef.current = []
        linesRef.current = []

        const maxDepth = visualNodes.reduce((acc, node) => Math.max(acc, node.depth), 0)
        const depthGroupCounts = visualNodes.reduce<Record<number, number>>((acc, node) => {
            acc[node.depth] = (acc[node.depth] || 0) + 1
            return acc
        }, {})
        const depthCurrentIndex: Record<number, number> = {}
        const positions = new Map<number, THREE.Vector3>()

        visualNodes.forEach(node => {
            const groupCount = depthGroupCounts[node.depth] || 1
            const indexWithinGroup = depthCurrentIndex[node.depth] || 0
            depthCurrentIndex[node.depth] = indexWithinGroup + 1

            const angle = (indexWithinGroup / groupCount) * Math.PI * 2
            const radius = 4 + node.depth * 1.5
            const heightOffset = (node.depth - maxDepth / 2) * 1.4

            const position = new THREE.Vector3(
                Math.cos(angle) * radius,
                heightOffset,
                Math.sin(angle) * radius
            )
            positions.set(node.id, position)

            const isHovered = hoveredId === node.id
            const isRoot = !node.parentId
            const geometry = new THREE.SphereGeometry(isRoot ? 0.6 : 0.45, 32, 32)
            const material = new THREE.MeshStandardMaterial({
                color: isRoot ? 0xf97316 : 0x0ea5e9,
                transparent: true,
                opacity: isHovered ? 1 : 0.85,
                roughness: 0.25,
                metalness: 0.35,
                emissive: isHovered ? (isRoot ? 0xf97316 : 0x0ea5e9) : 0x000000,
                emissiveIntensity: isHovered ? 0.5 : 0
            })
            const mesh = new THREE.Mesh(geometry, material)
            mesh.position.copy(position)
            mesh.userData = {
                nodeId: node.id,
                baseY: position.y
            }

            const haloGeometry = new THREE.SphereGeometry(isRoot ? 0.72 : 0.55, 32, 32)
            const haloMaterial = new THREE.MeshBasicMaterial({
                color: isRoot ? 0xf97316 : 0x0ea5e9,
                transparent: true,
                opacity: isHovered ? 0.28 : 0.12,
                side: THREE.BackSide
            })
            const halo = new THREE.Mesh(haloGeometry, haloMaterial)
            mesh.add(halo)

            sceneRef.current?.add(mesh)
            nodesRef.current.push(mesh)
        })

        visualNodes.forEach(node => {
            if (!node.parentId) return
            const start = positions.get(node.parentId)
            const end = positions.get(node.id)
            if (!start || !end) return

            const curve = new THREE.CatmullRomCurve3([
                start,
                new THREE.Vector3(
                    (start.x + end.x) / 2,
                    (start.y + end.y) / 2 + 0.4,
                    (start.z + end.z) / 2
                ),
                end
            ])

            const points = curve.getPoints(24)
            const geometry = new THREE.BufferGeometry().setFromPoints(points)
            const material = new THREE.LineBasicMaterial({
                color: 0x14b8a6,
                transparent: true,
                opacity: 0.5
            })
            const line = new THREE.Line(geometry, material)
            sceneRef.current?.add(line)
            linesRef.current.push(line)
        })
    }, [hoveredId, open, visualNodes])

    const totalMessages = visualNodes.length
    const rootConversations = visualNodes.filter(node => !node.parentId).length

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button variant="outline" size="sm">
                    Visualize in 3D
                </Button>
            </DialogTrigger>
            <DialogContent className="max-w-6xl w-[90vw] h-[80vh] p-0 overflow-hidden">
                <DialogHeader className="px-6 pt-4 pb-0">
                    <DialogTitle>3D Conversation Graph</DialogTitle>
                </DialogHeader>
                <div className="flex h-full gap-4 p-6 pt-4">
                    <div className="flex-1 rounded-2xl bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 border border-slate-800 shadow-inner relative overflow-hidden">
                        <div ref={containerRef} className="w-full h-full" />
                        <div className="absolute top-6 left-6 bg-black/40 backdrop-blur-md rounded-xl border border-white/10 p-4 text-white space-y-2 max-w-xs">
                            <div className="flex items-center justify-between text-sm">
                                <span className="text-white/70">Messages</span>
                                <span className="font-semibold">{totalMessages}</span>
                            </div>
                            <div className="flex items-center justify-between text-sm">
                                <span className="text-white/70">Conversations</span>
                                <span className="font-semibold">{rootConversations}</span>
                            </div>
                            <div className="flex flex-wrap gap-2 pt-2">
                                <Badge variant="outline" className="border-white/30 text-white/80">
                                    Drag to rotate
                                </Badge>
                                <Badge variant="outline" className="border-white/30 text-white/80">
                                    Scroll to zoom
                                </Badge>
                            </div>
                        </div>
                    </div>
                    <aside className="w-80 border border-slate-200 dark:border-slate-800 rounded-2xl bg-white/70 dark:bg-slate-900/60 backdrop-blur p-4 flex flex-col">
                        <div>
                            <p className="text-sm text-muted-foreground">Selected message</p>
                            <h3 className="text-lg font-semibold">{selectedNode ? selectedNode.author : 'None'}</h3>
                        </div>
                        <ScrollArea className="mt-4 flex-1 rounded-xl border border-slate-200 dark:border-slate-800 p-3">
                            {selectedNode ? (
                                <div className="space-y-3 text-sm">
                                    <div>
                                        <p className="text-muted-foreground text-xs uppercase tracking-wide">Author</p>
                                        <p className="font-medium">{selectedNode.author}</p>
                                    </div>
                                    <div>
                                        <p className="text-muted-foreground text-xs uppercase tracking-wide">Time</p>
                                        <p>{selectedNode.time}</p>
                                    </div>
                                    <div>
                                        <p className="text-muted-foreground text-xs uppercase tracking-wide">Message</p>
                                        <p className="leading-relaxed whitespace-pre-wrap">{selectedNode.content}</p>
                                    </div>
                                    <div className="flex gap-4 text-xs text-muted-foreground">
                                        <span>▲ {selectedNode.upvotes}</span>
                                        <span>▼ {selectedNode.downvotes}</span>
                                        <span>Depth {selectedNode.depth}</span>
                                    </div>
                                </div>
                            ) : (
                                <p className="text-sm text-muted-foreground">
                                    Hover or click any bubble to inspect a message.
                                </p>
                            )}
                        </ScrollArea>
                        <Button
                            variant="secondary"
                            className="mt-4"
                            onClick={() => setSelectedNode(null)}
                            disabled={!selectedNode}
                        >
                            Clear selection
                        </Button>
                    </aside>
                </div>
            </DialogContent>
        </Dialog>
    )
}

