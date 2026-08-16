import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { OrgSettingsForm } from './OrgSettingsForm';
import { authReducer } from '../auth.slice';

const store = configureStore({
  reducer: {
    auth: authReducer,
  },
});

const meta: Meta<typeof OrgSettingsForm> = {
  title: 'Features/Auth/OrgSettingsForm',
  component: OrgSettingsForm,
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
type Story = StoryObj<typeof OrgSettingsForm>;

export const Default: Story = {
  args: {
    orgName: 'Scaibu Enterprise',
    orgSlug: 'scaibu-enterprise',
    plan: 'ENTERPRISE PRO',
    complianceMode: 'SOC2 / HIPAA',
  },
};
