import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import { TiltCard } from './TiltCard';
import { Activity } from 'lucide-react';

const meta: Meta<typeof TiltCard> = {
  title: 'UI/TiltCard',
  component: TiltCard,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

export const DefaultTiltCard: Story = {
  render: () => (
    <TiltCard className="w-80 p-6 text-left">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-purple-600 text-white">
          <Activity size={20} />
        </div>
        <div>
          <h3 className="font-bold text-sm text-[hsl(var(--foreground))]">3D Interactive Perspective</h3>
          <p className="text-xs text-[hsl(var(--muted-foreground))]">Hover over this card to inspect specular 3D tilt effects.</p>
        </div>
      </div>
    </TiltCard>
  ),
};
