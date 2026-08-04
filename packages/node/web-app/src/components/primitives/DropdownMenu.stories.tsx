import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator } from './DropdownMenu';
import { Button } from './Button';

const meta = {
  title: 'Primitives/DropdownMenu',
  component: DropdownMenu,
  parameters: { layout: 'centered' },
} satisfies Meta<typeof DropdownMenu>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline">Options</Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        <DropdownMenuItem>View Details</DropdownMenuItem>
        <DropdownMenuItem>Export CSV</DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem className="text-[hsl(var(--destructive))]">Delete Trace</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  ),
};
