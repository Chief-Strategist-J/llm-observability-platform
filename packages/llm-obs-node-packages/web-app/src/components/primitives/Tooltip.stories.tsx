import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { TooltipProvider, Tooltip, TooltipTrigger, TooltipContent } from './Tooltip';
import { Button } from './Button';

const meta = {
  title: 'Primitives/Tooltip',
  component: Tooltip,
  parameters: { layout: 'centered' },
} satisfies Meta<typeof Tooltip>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="outline">Hover Me</Button>
        </TooltipTrigger>
        <TooltipContent>Full Precision: $0.000850 USD</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  ),
};
