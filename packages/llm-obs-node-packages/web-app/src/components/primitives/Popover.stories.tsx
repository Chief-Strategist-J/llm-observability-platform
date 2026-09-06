import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { Popover, PopoverTrigger, PopoverContent } from './Popover';
import { Button } from './Button';

const meta = {
  title: 'Primitives/Popover',
  component: Popover,
  parameters: { layout: 'centered' },
} satisfies Meta<typeof Popover>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="secondary">Filter Options</Button>
      </PopoverTrigger>
      <PopoverContent>
        <h4 className="font-semibold text-sm mb-2">Filter Spans</h4>
        <p className="text-xs text-[hsl(var(--muted-foreground))]">Configure span filters dynamically.</p>
      </PopoverContent>
    </Popover>
  ),
};
