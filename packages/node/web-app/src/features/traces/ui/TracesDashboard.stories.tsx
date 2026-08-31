import type { Meta, StoryObj } from '@storybook/react';
import { TracesDashboardUI } from './TracesDashboardUI';

const meta: Meta<typeof TracesDashboardUI> = {
  title: 'Features/Traces/TracesDashboardUI',
  component: TracesDashboardUI,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
  },
};

export default meta;
type Story = StoryObj<typeof TracesDashboardUI>;

export const LoadedWithMetrics: Story = {
  args: {
    traces: [
      { id: "trc_8401a", root_span_name: "chat.completion", service: "inference-gateway", model: "gpt-4o", duration_ms: 320, total_tokens: 450, cost_usd: 0.014, status: "success", timestamp: new Date().toISOString() },
      { id: "trc_8402b", root_span_name: "embedding.generate", service: "vector-service", model: "text-embedding-3-small", duration_ms: 45, total_tokens: 120, cost_usd: 0.0002, status: "success", timestamp: new Date(Date.now() - 120000).toISOString() },
      { id: "trc_8403c", root_span_name: "agent.tool_call", service: "agent-engine", model: "claude-3-5-sonnet", duration_ms: 1250, total_tokens: 1800, cost_usd: 0.038, status: "error", timestamp: new Date(Date.now() - 300000).toISOString() },
    ],
    loading: false,
    error: null,
  },
};

export const SkeletonLoading: Story = {
  args: {
    traces: [],
    loading: true,
    error: null,
  },
};

export const EmptyState: Story = {
  args: {
    traces: [],
    loading: false,
    error: null,
  },
};

export const ErrorState: Story = {
  args: {
    traces: [],
    loading: false,
    error: "Failed to query OpenTelemetry trace store (HTTP 500 Internal Server Error)",
  },
};
