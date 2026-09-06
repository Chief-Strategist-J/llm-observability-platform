import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { AppShell } from './AppShell';
import { SignUpForm } from '../../features/auth/ui/SignUpForm';
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
      userOrganizations: [],
      members: [],
      apiKeys: [],
      auditLogs: [],
      error: null,
    },
  },
});

const meta: Meta<typeof AppShell> = {
  title: 'Shell/AppShell',
  component: AppShell,
  decorators: [
    (Story) => (
      <Provider store={store}>
        <Story />
      </Provider>
    ),
  ],
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

export const AuthRouteCleanView: Story = {
  parameters: {
    nextjs: {
      navigation: {
        pathname: '/auth/sign-up',
      },
    },
  },
  render: () => (
    <div className="auth-container">
      <SignUpForm
        initialName="Jaydeep"
        initialOrgName="Scaibu"
        initialEmail="jaydeep@gmail.com"
        initialPassword="password12345"
        onSubmit={() => {}}
      />
    </div>
  ),
};

export const DashboardRouteView: Story = {
  parameters: {
    nextjs: {
      navigation: {
        pathname: '/',
      },
    },
  },
  render: () => (
    <AppShell>
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">System Overview Dashboard</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Grafana-grade real-time latency, cost, and quality monitoring for LLM operations.
        </p>
      </div>
    </AppShell>
  ),
};
