import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { Icon } from './Icon';

const meta = {
  title: 'Primitives/Icon',
  component: Icon,
  parameters: { layout: 'centered' },
} satisfies Meta<typeof Icon>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: { name: 'Activity', size: 24 },
};

export const CustomSize: Story = {
  args: { name: 'Zap', size: 48, className: 'text-[hsl(var(--primary))]' },
};

export const AccessibleLabel: Story = {
  args: { name: 'CircleCheck', size: 24, label: 'Success indicator' },
};
