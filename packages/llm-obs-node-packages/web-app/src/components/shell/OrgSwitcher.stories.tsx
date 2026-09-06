import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { OrgSwitcher } from './OrgSwitcher';
import { authReducer } from '../../features/auth/auth.slice';

const store = configureStore({
  reducer: {
    auth: authReducer,
  },
  preloadedState: {
    auth: {
      status: 'idle' as const,
      user: { id: 'usr-1', name: 'Jaydeep Admin', email: 'jaydeep@scaibu.com', org_id: 'org-1', org_name: 'Scaibu Primary' },
      organization: { id: 'org-1', name: 'Scaibu Primary' },
      userOrganizations: [
        { id: 'org-1', name: 'Scaibu Primary', slug: 'scaibu-primary' },
        { id: 'org-2', name: 'Secondary Enterprise', slug: 'secondary-enterprise' },
      ],
      members: [],
      apiKeys: [],
      auditLogs: [],
      error: null,
    },
  },
});

const meta: Meta<typeof OrgSwitcher> = {
  title: 'Shell/OrgSwitcher',
  component: OrgSwitcher,
  decorators: [
    (Story) => (
      <Provider store={store}>
        <div className="w-64 p-4 bg-[hsl(var(--card))] border border-[hsl(var(--border))] rounded-[var(--radius-md)] text-[hsl(var(--foreground))]">
          <Story />
        </div>
      </Provider>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof meta>;

export const MultiOrgView: Story = {};
