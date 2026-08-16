import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import { UserMenu } from './UserMenu';

const meta: Meta<typeof UserMenu> = {
  title: 'Shell/UserMenu',
  component: UserMenu,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

export const DefaultUserMenu: Story = {
  args: {
    user: {
      name: 'Jaydeep',
      email: 'jaydeep@gmail.com',
    },
    impersonating: false,
  },
  render: (args) => (
    <div className="w-64 p-4 bg-[hsl(var(--card))] border border-[hsl(var(--border))] rounded-[var(--radius-md)]">
      <UserMenu {...args} />
    </div>
  ),
};

export const SupportImpersonationView: Story = {
  args: {
    user: {
      name: 'Support Agent',
      email: 'support@observability.io',
    },
    impersonating: true,
  },
  render: (args) => (
    <div className="w-64 p-4 bg-[hsl(var(--card))] border border-[hsl(var(--border))] rounded-[var(--radius-md)]">
      <UserMenu {...args} />
    </div>
  ),
};
