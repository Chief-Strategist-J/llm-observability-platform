import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { MetricCard, MetricCardLoading, MetricCardEmpty, MetricCardError } from './MetricCard';
import { FIXTURE_SPARKLINE_LATENCY, FIXTURE_SPARKLINE_COST } from '../../../lib/fixtures/fixtures';
import { formatCostUsdMicro, formatLatencyMs } from '../../../lib/utils/formatters';

const meta = {
  title: 'Data Display/MetricCard',
  component: MetricCard,
  tags: ['data'],
  parameters: { layout: 'centered' },
  args: {
    label: 'Default Metric',
    value: '0',
  },
  decorators: [
    (Story) => (
      <div style={{ width: 320 }}>
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof MetricCard>;

export default meta;
type Story = StoryObj<typeof meta>;

/** Default: realistic fixture data, typical case. */
export const Default: Story = {
  args: {
    label: 'P50 Latency',
    value: formatLatencyMs(180),
    delta: { value: '+12%', direction: 'up' },
    sparklineData: [...FIXTURE_SPARKLINE_LATENCY],
    severity: 'good',
  },
};

/** Loading: SkeletonState composed in, not a bare spinner. */
export const Loading: Story = {
  render: () => <MetricCardLoading />,
};

/** Empty: EmptyState with a clear explanation. */
export const Empty: Story = {
  render: () => <MetricCardEmpty />,
};

/** Error: ErrorState with retry affordance. */
export const Error: Story = {
  render: () => (
    <MetricCardError
      message="Failed to fetch latency metrics. The upstream service returned a 503."
      onRetry={() => {}}
    />
  ),
};

/** Dense/Compact: used inside a DataTable or small card. */
export const DenseCompact: Story = {
  args: {
    label: 'Avg Cost',
    value: formatCostUsdMicro(850).compact,
    fullPrecisionValue: formatCostUsdMicro(850).full,
    sparklineData: [...FIXTURE_SPARKLINE_COST],
    severity: 'good',
    dense: true,
  },
};

/** Warning severity card. */
export const WarningSeverity: Story = {
  args: {
    label: 'P95 Latency',
    value: formatLatencyMs(450),
    delta: { value: '+25%', direction: 'up' },
    sparklineData: [...FIXTURE_SPARKLINE_LATENCY],
    severity: 'warn',
  },
};

/** Bad severity card. */
export const BadSeverity: Story = {
  args: {
    label: 'P99 Latency',
    value: formatLatencyMs(620),
    delta: { value: '+40%', direction: 'up' },
    sparklineData: [...FIXTURE_SPARKLINE_LATENCY],
    severity: 'bad',
  },
};

/** EC-FE1-01: Long numeric value truncated with tooltip. */
export const LongValue: Story = {
  args: {
    label: 'Total Cost',
    value: formatCostUsdMicro(32_450_000).compact,
    fullPrecisionValue: formatCostUsdMicro(32_450_000).full,
    severity: 'warn',
  },
};
