import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from './Select';

const meta = {
  title: 'Primitives/Select',
  component: Select,
  parameters: { layout: 'centered' },
  decorators: [(Story) => <div style={{ width: 250 }}><Story /></div>],
} satisfies Meta<typeof Select>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Select defaultValue="gpt-4o">
      <SelectTrigger>
        <SelectValue placeholder="Select model" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="gpt-4o">GPT-4o</SelectItem>
        <SelectItem value="gpt-4o-mini">GPT-4o Mini</SelectItem>
        <SelectItem value="claude-3-opus">Claude 3 Opus</SelectItem>
      </SelectContent>
    </Select>
  ),
};
