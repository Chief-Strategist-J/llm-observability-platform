import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { Button } from './Button';

const meta = {
  title: 'Primitives/Button',
  component: Button,
  parameters: { layout: 'centered' },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: { children: 'Button' } };
export const Secondary: Story = { args: { variant: 'secondary', children: 'Secondary' } };
export const Outline: Story = { args: { variant: 'outline', children: 'Outline' } };
export const Destructive: Story = { args: { variant: 'destructive', children: 'Delete' } };
export const Ghost: Story = { args: { variant: 'ghost', children: 'Ghost' } };
export const Small: Story = { args: { size: 'sm', children: 'Small' } };
export const Large: Story = { args: { size: 'lg', children: 'Large' } };
export const Disabled: Story = { args: { disabled: true, children: 'Disabled' } };
