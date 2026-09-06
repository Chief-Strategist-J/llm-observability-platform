import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import { HeaderBar } from './HeaderBar';

const meta: Meta<typeof HeaderBar> = {
  title: 'Shell/HeaderBar',
  component: HeaderBar,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <div className="w-full bg-[hsl(var(--background))] text-[hsl(var(--foreground))]">
      <HeaderBar />
    </div>
  ),
};
