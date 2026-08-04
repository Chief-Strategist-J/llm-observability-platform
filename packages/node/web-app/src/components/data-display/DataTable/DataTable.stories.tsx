import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import type { ColumnDef } from '@tanstack/react-table';
import type { Span } from '@observability/api-types';
import { DataTable, columnFormatters } from './DataTable';
import { SeverityBadge } from '../SeverityBadge/SeverityBadge';
import { FIXTURE_SPANS } from '../../../lib/fixtures';
import { SkeletonState } from '../../states/SkeletonState';
import { EmptyState } from '../../states/EmptyState';
import { ErrorState } from '../../states/ErrorState';

const spanColumns: ColumnDef<any, any>[] = [
  { accessorKey: 'name', header: 'Span Name' },
  { accessorKey: 'model', header: 'Model' },
  {
    accessorKey: 'latency_ms',
    header: 'Latency',
    cell: ({ getValue }) => columnFormatters.latency_ms(getValue() as number),
  },
  {
    accessorKey: 'cost_usd_micro',
    header: 'Cost',
    cell: ({ getValue }) => columnFormatters.cost_usd_micro(getValue() as number),
  },
  {
    accessorKey: 'tokens_input',
    header: 'Input Tokens',
    cell: ({ getValue }) => {
      const v = getValue();
      return v !== null && v !== undefined ? columnFormatters.tokens(v as number) : '—';
    },
  },
  {
    accessorKey: 'status',
    header: 'Status',
    cell: ({ getValue }) => {
      const status = getValue() as string;
      return (
        <span className={status === 'success' ? 'text-[hsl(var(--severity-good))]' : 'text-[hsl(var(--severity-bad))]'}>
          {status}
        </span>
      );
    },
  },
  {
    accessorKey: 'quality_score',
    header: 'Quality',
    cell: ({ getValue }) => {
      const v = getValue();
      if (v === null || v === undefined) return '—';
      return <SeverityBadge type="quality" value={v as number} />;
    },
  },
];

// Generate 10,000 rows for the Dense test (TEST-FE1-05)
function generateLargeDataset(count: number): Span[] {
  return Array.from({ length: count }, (_, i) => ({
    trace_id: `trace-${i.toString().padStart(5, '0')}`,
    span_id: `span-${i.toString().padStart(5, '0')}`,
    name: `llm.completion.${i % 10}`,
    start_time_ms: 1722700000000 + i * 100,
    end_time_ms: 1722700000000 + i * 100 + 100 + Math.floor(Math.random() * 500),
    latency_ms: 50 + Math.floor(Math.random() * 550),
    status: Math.random() > 0.05 ? 'success' as const : 'error' as const,
    cost_usd_micro: 100 + Math.floor(Math.random() * 5000),
    model: ['gpt-4o', 'gpt-4o-mini', 'claude-3-opus', 'claude-3-sonnet'][i % 4],
    quality_score: 0.5 + Math.random() * 0.5,
    tokens_input: 200 + Math.floor(Math.random() * 4000),
    tokens_output: 50 + Math.floor(Math.random() * 1500),
  }));
}

const meta = {
  title: 'Data Display/DataTable',
  component: DataTable,
  tags: ['data'],
  args: {
    columns: spanColumns as any,
    data: FIXTURE_SPANS as any,
  },
} satisfies Meta<typeof DataTable>;

export default meta;
type Story = StoryObj<typeof meta>;

/** Default: realistic fixture data, typical case. */
export const Default: Story = {
  args: {
    columns: spanColumns,
    data: FIXTURE_SPANS,
    height: 300,
  },
};

/** Loading: SkeletonState composed in, not a bare spinner. */
export const Loading: Story = {
  render: () => (
    <div className="rounded-[var(--radius-lg)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-6">
      <SkeletonState lines={8} />
    </div>
  ),
};

/** Empty: EmptyState composed in, with a clear explanation. */
export const Empty: Story = {
  render: () => (
    <DataTable columns={spanColumns} data={[]} height={300} />
  ),
};

/** Error: ErrorState composed in, with a retry affordance. */
export const Error: Story = {
  render: () => (
    <ErrorState
      message="Failed to query span data. ClickHouse returned a timeout after 30s."
      onRetry={() => {}}
    />
  ),
};

/** Dense/Compact: 10,000 rows to verify virtualization (TEST-FE1-05). */
export const DenseCompact: Story = {
  args: {
    columns: spanColumns,
    data: generateLargeDataset(10_000),
    height: 500,
  },
};

/** Single row — edge case (TEST-FE1-05). */
export const SingleRow: Story = {
  args: {
    columns: spanColumns,
    data: [FIXTURE_SPANS[0]],
    height: 200,
  },
};
