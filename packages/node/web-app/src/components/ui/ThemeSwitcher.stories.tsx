import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import { ThemeSwitcher } from './ThemeSwitcher';

const meta: Meta<typeof ThemeSwitcher> = {
  title: 'UI/ThemeSwitcher',
  component: ThemeSwitcher,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <div className="w-[450px] p-4 bg-[hsl(var(--background))] text-[hsl(var(--foreground))] rounded-[var(--radius-lg)]">
      <ThemeSwitcher />
    </div>
  ),
};
