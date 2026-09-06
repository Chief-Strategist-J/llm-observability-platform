import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { SkeletonState } from './SkeletonState';

const meta = {
  title: 'States/SkeletonState',
  component: SkeletonState,
  parameters: { layout: 'centered' },
  decorators: [(Story) => <div style={{ width: 400 }}><Story /></div>],
} satisfies Meta<typeof SkeletonState>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: { lines: 3 } };
export const SingleLine: Story = { args: { lines: 1 } };
export const ManyLines: Story = { args: { lines: 8 } };
