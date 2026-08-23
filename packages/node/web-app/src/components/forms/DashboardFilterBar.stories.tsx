import type { Meta, StoryObj } from '@storybook/react';
import { DashboardFilterBar } from './DashboardFilterBar';
import { DEFAULT_DASHBOARD_FILTERS } from '../../hooks/useDashboardFilters';

const meta: Meta<typeof DashboardFilterBar> = {
  title: 'Forms/DashboardFilterBar',
  component: DashboardFilterBar,
  tags: ['autodocs'],
  argTypes: {
    onFilterChange: { action: 'filterChanged' },
    onReset: { action: 'resetFilters' },
  },
};

export default meta;
type Story = StoryObj<typeof DashboardFilterBar>;

export const Default: Story = {
  args: {
    filters: DEFAULT_DASHBOARD_FILTERS,
    hasActiveFilters: false,
  },
};

export const Filtered: Story = {
  args: {
    filters: {
      timeRange: '7d',
      model: 'gpt-4o',
      service: 'checkout-service',
      environment: 'production',
    },
    hasActiveFilters: true,
  },
};

export const CustomRange: Story = {
  args: {
    filters: {
      timeRange: 'custom',
      from: '2026-08-01T00:00:00.000Z',
      to: '2026-08-23T23:59:59.000Z',
      model: 'claude-3-5-sonnet',
      service: 'recommendation-api',
      environment: 'staging',
    },
    hasActiveFilters: true,
  },
};
