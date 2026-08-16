import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { UserMenu } from './UserMenu';
import { authReducer } from '../../features/auth/auth.slice';

const store = configureStore({
  reducer: {
    auth: authReducer,
  },
  preloadedState: {
    auth: {
      status: 'idle' as const,
      user: { id: 'usr-1', name: 'Jaydeep Scaibu', email: 'jaydeep@gmail.com', org_id: 'org-1', org_name: 'Scaibu Primary' },
      organization: { id: 'org-1', name: 'Scaibu Primary' },
      userOrganizations: [],
      members: [],
      apiKeys: [],
      auditLogs: [],
      error: null,
    },
  },
});

const meta: Meta<typeof UserMenu> = {
  title: 'Shell/UserMenu',
  component: UserMenu,
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

export const DefaultUserMenu: Story = {
  args: {
    user: {
      name: 'Jaydeep',
      email: 'jaydeep@gmail.com',
    },
    impersonating: false,
  },
};

export const SupportImpersonationView: Story = {
  args: {
    user: {
      name: 'Support Agent',
      email: 'support@observability.io',
    },
    impersonating: true,
  },
};
