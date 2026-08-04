import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { TimeSeriesChart } from './TimeSeriesChart';
import { SkeletonState } from '../../states/SkeletonState';
import { EmptyState } from '../../states/EmptyState';
import { ErrorState } from '../../states/ErrorState';
import { FIXTURE_TIMESERIES_TIMESTAMPS, FIXTURE_LATENCY_P50 } from '../../../lib/fixtures';

const meta = {
  title: 'Data Display/Charts/TimeSeriesChart',
  component: TimeSeriesChart,
  tags: ['data'],
  args: {
    data: [FIXTURE_TIMESERIES_TIMESTAMPS, FIXTURE_LATENCY_P50],
    series: [{ label: 'P50', stroke: 'hsl(263 70% 50%)' }],
  },
} satisfies Meta<typeof TimeSeriesChart>;

export default meta;
type Story = StoryObj<typeof meta>;

/** Default: realistic fixture data. */
export const Default: Story = {
  args: {
    data: [FIXTURE_TIMESERIES_TIMESTAMPS, FIXTURE_LATENCY_P50],
    series: [{ label: 'P50 Latency (ms)', stroke: 'hsl(263 70% 50%)' }],
    width: 700,
    height: 300,
    title: 'Latency Over Time',
    testMode: true,
  },
};

/** Loading: SkeletonState composed in. */
export const Loading: Story = {
  render: () => (
    <div className="rounded-[var(--radius-lg)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-6" style={{ width: 700, height: 300 }}>
      <SkeletonState lines={6} />
    </div>
  ),
};

/** Empty: EmptyState with explanation. */
export const Empty: Story = {
  render: () => (
    <EmptyState
      title="No time series data"
      description="Time series data will appear here once your application starts generating spans."
    />
  ),
};

/** Error: ErrorState with retry. */
export const Error: Story = {
  render: () => (
    <ErrorState
      message="Failed to stream time series data. WebSocket connection was refused."
      onRetry={() => {}}
    />
  ),
};

/** Dense/Compact: smaller dimensions for dashboard cards. */
export const DenseCompact: Story = {
  args: {
    data: [FIXTURE_TIMESERIES_TIMESTAMPS.slice(0, 20), FIXTURE_LATENCY_P50.slice(0, 20)],
    series: [{ label: 'P50', stroke: 'hsl(263 70% 50%)' }],
    width: 300,
    height: 150,
    testMode: true,
  },
};
