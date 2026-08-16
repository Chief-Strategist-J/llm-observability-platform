import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import { OrgSwitcher } from './OrgSwitcher';

const meta: Meta<typeof OrgSwitcher> = {
  title: 'Shell/OrgSwitcher',
  component: OrgSwitcher,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

export const DefaultOrgView: Story = {
  render: () => (
    <div className="w-64 p-4 bg-[hsl(var(--card))] border border-[hsl(var(--border))] rounded-[var(--radius-md)]">
      <OrgSwitcher />
    </div>
  ),
};
