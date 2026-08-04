import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { ErrorState } from './ErrorState';

const meta = {
  title: 'States/ErrorState',
  component: ErrorState,
  parameters: { layout: 'centered' },
  decorators: [(Story) => <div style={{ width: 500 }}><Story /></div>],
} satisfies Meta<typeof ErrorState>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    message: 'An unexpected error occurred while loading span data.',
  },
};

export const WithRetry: Story = {
  args: {
    message: 'ClickHouse query timed out after 30 seconds.',
    onRetry: () => {},
  },
};

export const CustomTitle: Story = {
  args: {
    title: 'Connection failed',
    message: 'Could not establish a WebSocket connection to the real-time event stream.',
    onRetry: () => {},
  },
};
