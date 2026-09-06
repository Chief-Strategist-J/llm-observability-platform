import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './Tabs';

const meta = {
  title: 'Primitives/Tabs',
  component: Tabs,
  parameters: { layout: 'centered' },
  decorators: [(Story) => <div style={{ width: 400 }}><Story /></div>],
} satisfies Meta<typeof Tabs>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Tabs defaultValue="spans">
      <TabsList className="w-full">
        <TabsTrigger value="spans" className="flex-1">Spans</TabsTrigger>
        <TabsTrigger value="metrics" className="flex-1">Metrics</TabsTrigger>
        <TabsTrigger value="logs" className="flex-1">Logs</TabsTrigger>
      </TabsList>
      <TabsContent value="spans" className="p-4 border rounded-md mt-2">Spans list view</TabsContent>
      <TabsContent value="metrics" className="p-4 border rounded-md mt-2">Metrics aggregated view</TabsContent>
      <TabsContent value="logs" className="p-4 border rounded-md mt-2">System logs view</TabsContent>
    </Tabs>
  ),
};
