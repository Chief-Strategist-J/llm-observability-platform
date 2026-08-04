import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { PercentileBandChart } from './PercentileBandChart';
import { SkeletonState } from '../../states/SkeletonState';
import { EmptyState } from '../../states/EmptyState';
import { ErrorState } from '../../states/ErrorState';
import {
  FIXTURE_TIMESERIES_TIMESTAMPS,
  FIXTURE_LATENCY_P50,
  FIXTURE_LATENCY_P95,
  FIXTURE_LATENCY_P99,
} from '../../../lib/fixtures';

const meta = {
  title: 'Data Display/Charts/PercentileBandChart',
  component: PercentileBandChart,
  tags: ['data'],
  args: {
    data: [
      FIXTURE_TIMESERIES_TIMESTAMPS,
      FIXTURE_LATENCY_P50,
      FIXTURE_LATENCY_P95,
      FIXTURE_LATENCY_P99,
    ],
  },
} satisfies Meta<typeof PercentileBandChart>;

export default meta;
type Story = StoryObj<typeof meta>;

/** Default: realistic DDSketch-shaped fixture data. */
export const Default: Story = {
  args: {
    data: [
      FIXTURE_TIMESERIES_TIMESTAMPS,
      FIXTURE_LATENCY_P50,
      FIXTURE_LATENCY_P95,
      FIXTURE_LATENCY_P99,
    ],
    width: 700,
    height: 300,
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
      title="No latency data"
      description="Latency percentile data will appear here once your application starts processing requests."
    />
  ),
};

/** Error: ErrorState with retry. */
export const Error: Story = {
  render: () => (
    <ErrorState
      message="Failed to load DDSketch data from ClickHouse. Connection timed out."
      onRetry={() => {}}
    />
  ),
};

/** EC-FE1-02: Inverted bands from low-sample-size buckets. */
export const DenseCompact: Story = {
  args: {
    data: [
      FIXTURE_TIMESERIES_TIMESTAMPS.slice(0, 10),
      // Intentionally inverted: P50 > P95 on some buckets
      [300, 250, 280, 400, 200, 350, 270, 310, 290, 260],
      [280, 260, 270, 380, 220, 330, 260, 300, 280, 250],
      [500, 450, 480, 600, 400, 550, 470, 510, 490, 460],
    ],
    width: 500,
    height: 200,
    sampleSizes: [3, 5, 2, 8, 4, 6, 3, 7, 5, 2],
    minSampleSize: 10,
    testMode: true,
  },
};
