import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { SeverityBadge } from './SeverityBadge';

const meta = {
  title: 'Data Display/SeverityBadge',
  component: SeverityBadge,
  tags: ['data'],
  parameters: { layout: 'centered' },
} satisfies Meta<typeof SeverityBadge>;

export default meta;
type Story = StoryObj<typeof meta>;

/** Default: realistic fixture data, typical case. */
export const Default: Story = {
  args: { type: 'latency', value: 180 },
};

/** Good severity — value within SLO threshold. */
export const Good: Story = {
  args: { type: 'latency', value: 120 },
};

/** Warning severity — approaching threshold. */
export const Warning: Story = {
  args: { type: 'cost', value: 3000 },
};

/** Bad severity — exceeds threshold. */
export const Bad: Story = {
  args: { type: 'cost', value: 8000 },
};

/** Quality metric — higher is better. */
export const QualityGood: Story = {
  args: { type: 'quality', value: 0.92 },
};

/** Quality metric — below warning threshold. */
export const QualityBad: Story = {
  args: { type: 'quality', value: 0.55 },
};

/** Dense/Compact: custom label for use inside DataTable cells. */
export const DenseCompact: Story = {
  args: { type: 'latency', value: 180, label: '180ms', className: 'text-[10px]' },
};
