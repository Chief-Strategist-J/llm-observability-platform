import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import { GlobalSearch } from './GlobalSearch';

const meta: Meta<typeof GlobalSearch> = {
  title: 'Shell/GlobalSearch',
  component: GlobalSearch,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <div className="w-64 p-4 bg-[hsl(var(--card))] border border-[hsl(var(--border))] rounded-[var(--radius-md)] text-[hsl(var(--foreground))]">
      <GlobalSearch />
    </div>
  ),
};
