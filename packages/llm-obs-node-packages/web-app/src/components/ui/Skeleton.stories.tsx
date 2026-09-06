import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import { Skeleton, SkeletonCard, SkeletonTable } from './Skeleton';

const meta: Meta<typeof Skeleton> = {
  title: 'UI/Skeleton',
  component: Skeleton,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

export const DefaultSkeleton: Story = {
  render: () => <Skeleton className="h-6 w-64" />,
};

export const CardSkeleton: Story = {
  render: () => (
    <div className="w-96">
      <SkeletonCard />
    </div>
  ),
};

export const TableSkeleton: Story = {
  render: () => (
    <div className="w-[600px]">
      <SkeletonTable rows={4} cols={3} />
    </div>
  ),
};
