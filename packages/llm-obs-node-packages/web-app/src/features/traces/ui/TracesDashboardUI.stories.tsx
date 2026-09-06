import type { Meta, StoryObj } from '@storybook/react';
import { TracesDashboardUI } from './TracesDashboardUI';
import type { TraceSummary } from '../types';

const mockTraces: TraceSummary[] = [
  {
    id: 'trc_9a8b7c6d',
    root_span_name: 'POST /api/v1/chat/completions',
    service: 'web-app',
    model: 'gpt-4o',
    duration_ms: 420,
    total_tokens: 1450,
    cost_usd: 0.0145,
    status: 'success',
    timestamp: '2026-09-01T12:00:00Z',
  },
  {
    id: 'trc_1e2f3g4h',
    root_span_name: 'POST /api/v1/embeddings',
    service: 'queue-embedding-worker',
    model: 'text-embedding-3-small',
    duration_ms: 120,
    total_tokens: 820,
    cost_usd: 0.0004,
    status: 'success',
    timestamp: '2026-09-01T12:01:10Z',
  },
  {
    id: 'trc_5i6j7k8l',
    root_span_name: 'POST /api/v1/quality/score',
    service: 'quality-engine',
    model: 'cross-encoder/ms-marco',
    duration_ms: 1850,
    total_tokens: 3100,
    cost_usd: 0.0310,
    status: 'error',
    timestamp: '2026-09-01T12:02:30Z',
  },
  {
    id: 'trc_9m0n1o2p',
    root_span_name: 'POST /api/v1/faithfulness/evaluate',
    service: 'faithfulness',
    model: 'claude-3-5-sonnet',
    duration_ms: 950,
    total_tokens: 2100,
    cost_usd: 0.0210,
    status: 'success',
    timestamp: '2026-09-01T12:03:45Z',
  },
];

const meta: Meta<typeof TracesDashboardUI> = {
  title: 'Features/Traces/TracesDashboardUI',
  component: TracesDashboardUI,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof TracesDashboardUI>;

export const Default: Story = {
  args: {
    traces: mockTraces,
    loading: false,
    error: null,
  },
};

export const FilteredResults: Story = {
  args: {
    traces: mockTraces,
    filters: {
      searchQuery: 'completions',
      selectedService: 'web-app',
      selectedStatus: 'success',
      selectedModel: 'gpt-4o',
      minDurationMs: 200,
    },
    loading: false,
  },
};

export const EmptyState: Story = {
  args: {
    traces: [],
    loading: false,
  },
};

export const LoadingState: Story = {
  args: {
    traces: [],
    loading: true,
  },
};

export const ErrorState: Story = {
  args: {
    traces: [],
    error: 'Failed to connect to ClickHouse telemetry query engine on port 31421.',
    loading: false,
  },
};
