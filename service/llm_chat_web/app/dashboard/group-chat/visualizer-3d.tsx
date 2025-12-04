'use client'

import React from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Network } from 'lucide-react'
import type { Comment } from '@/utils/api/group-chat-client'

export default function GroupChat3DTree({
  discussions,
}: {
  discussions: Comment[]
}) {
  const router = useRouter()

  const handleOpenVisualization = () => {
    router.push('/dashboard/group-chat/visualization')
  }

  return (
    <Button
      variant="default"
      size="sm"
      onClick={handleOpenVisualization}
    >
      <Network className="w-4 h-4 mr-2" />
      3D Visualization
    </Button>
  )
}
