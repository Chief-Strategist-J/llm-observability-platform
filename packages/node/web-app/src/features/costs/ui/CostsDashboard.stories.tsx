import type { Meta, StoryObj } from '@storybook/react';
import { CostsDashboardUI } from './CostsDashboardUI';

const meta: Meta<typeof CostsDashboardUI> = {
  title: 'Features/Costs/CostsDashboardUI',
  component: CostsDashboardUI,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
  },
};

export default meta;
type Story = StoryObj<typeof CostsDashboardUI>;

export const LoadedWithMetrics: Story = {
  args: {
    summary: {
      total_cost_usd: 1420.50,
      daily_avg_usd: 47.35,
      cost_delta_pct: 5.8,
      projected_monthly_usd: 1450.00,
    },
    providers: [
      { provider: "OpenAI", model: "gpt-4o", cost_usd: 850.40, token_count: 14200000, pct_of_total: 59.8 },
      { provider: "Anthropic", model: "claude-3-5-sonnet", cost_usd: 420.10, token_count: 8900000, pct_of_total: 29.5 },
      { provider: "OpenAI", model: "text-embedding-3-small", cost_usd: 150.00, token_count: 45000000, pct_of_total: 10.7 },
    ],
    loading: false,
    error: null,
  },
};

export const SkeletonLoading: Story = {
  args: {
    summary: null,
    providers: [],
    loading: true,
    error: null,
  },
};

export const EmptyState: Story = {
  args: {
    summary: null,
    providers: [],
    loading: false,
    error: null,
  },
};

export const ErrorState: Story = {
  args: {
    summary: null,
    providers: [],
    loading: false,
    error: "Failed to connect to Cost Analytics Engine (HTTP 500 Internal Server Error)",
  },
};
