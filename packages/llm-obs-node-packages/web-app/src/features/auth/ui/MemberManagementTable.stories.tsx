import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { MemberManagementTable } from './MemberManagementTable';
import { authReducer } from '../auth.slice';

const store = configureStore({
  reducer: {
    auth: authReducer,
  },
});

const meta: Meta<typeof MemberManagementTable> = {
  title: 'Features/Auth/MemberManagementTable',
  component: MemberManagementTable,
  decorators: [
    (Story) => (
      <Provider store={store}>
        <div className="bg-[hsl(var(--background))] p-8 text-[hsl(var(--foreground))] min-h-screen">
          <Story />
        </div>
      </Provider>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof MemberManagementTable>;

export const Default: Story = {
  args: {
    members: [
      { id: 'usr-1', name: 'Jaydeep Scaibu', email: 'jaydeep@scaibu.com', role: 'owner', blocked: false },
      { id: 'usr-2', name: 'Sarah Tech Lead', email: 'sarah@observability.io', role: 'admin', blocked: false },
      { id: 'usr-3', name: 'Alex Developer', email: 'alex@observability.io', role: 'member', blocked: false },
      { id: 'usr-4', name: 'Blocked Contractor', email: 'contractor@external.com', role: 'viewer', blocked: true },
    ],
  },
};

export const Empty: Story = {
  args: {
    members: [],
  },
};
