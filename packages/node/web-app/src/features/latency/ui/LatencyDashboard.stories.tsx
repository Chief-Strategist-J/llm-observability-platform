import type { Meta, StoryObj } from '@storybook/react';
import { LatencyDashboardUI } from './LatencyDashboardUI';

const meta: Meta<typeof LatencyDashboardUI> = {
  title: 'Features/Latency/LatencyDashboardUI',
  component: LatencyDashboardUI,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
  },
};

export default meta;
type Story = StoryObj<typeof LatencyDashboardUI>;

export const LoadedWithMetrics: Story = {
  args: {
    percentiles: { p50: 120, p95: 340, p99: 890, sample_count: 1420 },
    slo: { burn_fast: 0.2, burn_medium: 0.1, burn_slow: 0.05, budget_remaining_pct: 98.5, slo_threshold_ms: 1000 },
    attribution: { dns: 12, tcp: 24, queue: 45, inference: 680 },
    baseline: [
      { date: "2026-08-23", p99_ttft_ms: 110, p99_total_ms: 850 },
      { date: "2026-08-24", p99_ttft_ms: 115, p99_total_ms: 870 },
      { date: "2026-08-25", p99_ttft_ms: 108, p99_total_ms: 840 },
      { date: "2026-08-26", p99_ttft_ms: 122, p99_total_ms: 910 },
      { date: "2026-08-27", p99_ttft_ms: 118, p99_total_ms: 880 },
      { date: "2026-08-28", p99_ttft_ms: 112, p99_total_ms: 860 },
      { date: "2026-08-29", p99_ttft_ms: 120, p99_total_ms: 890 },
    ],
    loading: false,
    error: null,
  },
};

export const SkeletonLoading: Story = {
  args: {
    percentiles: null,
    slo: null,
    attribution: null,
    baseline: [],
    loading: true,
    error: null,
  },
};

export const EmptyState: Story = {
  args: {
    percentiles: null,
    slo: null,
    attribution: null,
    baseline: [],
    loading: false,
    error: null,
  },
};

export const ErrorState: Story = {
  args: {
    percentiles: null,
    slo: null,
    attribution: null,
    baseline: [],
    loading: false,
    error: "Failed to connect to Latency Engine REST service (HTTP 503 Service Unavailable)",
  },
};
