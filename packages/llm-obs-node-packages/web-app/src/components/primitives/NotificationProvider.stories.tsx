import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { NotificationProvider, useNotify } from './NotificationProvider';
import { Button } from './Button';

function ToastDemo() {
  const { notify } = useNotify();

  return (
    <div className="flex flex-wrap gap-2">
      <Button onClick={() => notify('Info', 'Span details updated.', 'info')}>
        Info Toast
      </Button>
      <Button variant="secondary" onClick={() => notify('Success', 'Budget saved successfully.', 'success')}>
        Success Toast
      </Button>
      <Button variant="outline" onClick={() => notify('Warning', 'Latency p95 approaching SLO threshold.', 'warning')}>
        Warning Toast
      </Button>
      <Button variant="destructive" onClick={() => notify('Error', 'Failed to connect to ClickHouse cluster.', 'error')}>
        Error Toast
      </Button>
    </div>
  );
}

const meta = {
  title: 'Primitives/Toast',
  component: NotificationProvider,
  parameters: { layout: 'centered' },
  args: { children: null },
} satisfies Meta<typeof NotificationProvider>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <NotificationProvider>
      <ToastDemo />
    </NotificationProvider>
  ),
};
