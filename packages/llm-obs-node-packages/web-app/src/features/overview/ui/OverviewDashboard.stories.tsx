import type { Meta, StoryObj } from '@storybook/react';
import { OverviewDashboardUI } from './OverviewDashboardUI';

const meta: Meta<typeof OverviewDashboardUI> = {
  title: 'Features/Overview/OverviewDashboardUI',
  component: OverviewDashboardUI,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
  },
};

export default meta;
type Story = StoryObj<typeof OverviewDashboardUI>;

export const LoadedWithMetrics: Story = {
  args: {
    kpi: {
      p95_latency_ms: 340,
      quality_avg_score: 0.94,
      total_spend_usd: 1420.50,
      active_spans_count: 84200,
      p95_latency_delta_pct: -4.2,
      quality_delta_pct: 2.1,
      spend_delta_pct: 5.8,
    },
    health: {
      status: "healthy",
      fast_burn_active: false,
      medium_burn_active: false,
      active_alerts_count: 0,
      message: "All services operating within standard SLO error budget thresholds.",
    },
    recentTraces: [
      { id: "trc_8401a", span_name: "chat.completion", service: "inference-gateway", model: "gpt-4o", duration_ms: 320, cost_usd: 0.014, status: "success", timestamp: new Date().toISOString() },
      { id: "trc_8402b", span_name: "embedding.generate", service: "vector-service", model: "text-embedding-3-small", duration_ms: 45, cost_usd: 0.0002, status: "success", timestamp: new Date(Date.now() - 120000).toISOString() },
    ],
    loading: false,
    error: null,
  },
};

export const SkeletonLoading: Story = {
  args: {
    kpi: null,
    health: null,
    recentTraces: [],
    loading: true,
    error: null,
  },
};

export const EmptyState: Story = {
  args: {
    kpi: null,
    health: null,
    recentTraces: [],
    loading: false,
    error: null,
  },
};

export const ErrorState: Story = {
  args: {
    kpi: null,
    health: null,
    recentTraces: [],
    loading: false,
    error: "Failed to connect to Overview Aggregation REST Service (HTTP 503 Service Unavailable)",
  },
};
