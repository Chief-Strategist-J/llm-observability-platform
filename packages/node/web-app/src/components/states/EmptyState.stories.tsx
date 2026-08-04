import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { EmptyState } from './EmptyState';
import { Button } from '../primitives/Button';

const meta = {
  title: 'States/EmptyState',
  component: EmptyState,
  parameters: { layout: 'centered' },
  decorators: [(Story) => <div style={{ width: 500 }}><Story /></div>],
} satisfies Meta<typeof EmptyState>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    description: 'No spans have been recorded yet. Start your application to generate telemetry data.',
  },
};

export const WithAction: Story = {
  args: {
    title: 'No budgets configured',
    description: 'Set up a budget to track your LLM spending and receive alerts when thresholds are reached.',
    action: <Button size="sm">Create Budget</Button>,
  },
};
