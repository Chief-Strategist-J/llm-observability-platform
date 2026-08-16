import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import type { ColumnDef } from '@tanstack/react-table';
import type { Span } from '@observability/api-types';
import { DataTable, columnFormatters } from './DataTable';
import { SeverityBadge } from '../SeverityBadge/SeverityBadge';
import { FIXTURE_SPANS } from '../../../lib/fixtures';
import { SkeletonState } from '../../states/SkeletonState';
import { ErrorState } from '../../states/ErrorState';

const spanColumns: ColumnDef<Span, unknown>[] = [
  { accessorKey: 'name', header: 'Span Name', size: 180, meta: { align: 'left' } },
  { accessorKey: 'model', header: 'Model', size: 160, meta: { align: 'left' } },
  {
    accessorKey: 'latency_ms',
    header: 'Latency',
    size: 110,
    meta: { align: 'right' },
    cell: ({ getValue }) => columnFormatters.latency_ms(getValue() as number),
  },
  {
    accessorKey: 'cost_usd_micro',
    header: 'Cost',
    size: 110,
    meta: { align: 'right' },
    cell: ({ getValue }) => columnFormatters.cost_usd_micro(getValue() as number),
  },
  {
    accessorKey: 'tokens_input',
    header: 'Input Tokens',
    size: 140,
    meta: { align: 'right' },
    cell: ({ getValue }) => {
      const v = getValue();
      return v !== null && v !== undefined ? columnFormatters.tokens(v as number) : '—';
    },
  },
  {
    accessorKey: 'status',
    header: 'Status',
    size: 120,
    meta: { align: 'center' },
    cell: ({ getValue }) => {
      const status = getValue() as string;
      return (
        <span className={status === 'success' ? 'font-semibold text-[hsl(var(--severity-good))]' : 'font-semibold text-[hsl(var(--severity-bad))]'}>
          {status}
        </span>
      );
    },
  },
  {
    accessorKey: 'quality_score',
    header: 'Quality',
    size: 120,
    meta: { align: 'center' },
    cell: ({ getValue }) => {
      const v = getValue();
      if (v === null || v === undefined) return '—';
      return <SeverityBadge type="quality" value={v as number} />;
    },
  },
];

function generateLargeDataset(count: number): Span[] {
  return Array.from({ length: count }, (_, i) => ({
    trace_id: `trace-${i.toString().padStart(5, '0')}`,
    span_id: `span-${i.toString().padStart(5, '0')}`,
    name: `llm.completion.${i % 10}`,
    start_time_ms: 1722700000000 + i * 100,
    end_time_ms: 1722700000000 + i * 100 + 100 + Math.floor(Math.random() * 500),
    latency_ms: 50 + Math.floor(Math.random() * 550),
    status: Math.random() > 0.05 ? ('success' as const) : ('error' as const),
    cost_usd_micro: 100 + Math.floor(Math.random() * 5000),
    model: ['gpt-4o', 'gpt-4o-mini', 'claude-3-opus', 'claude-3-sonnet'][i % 4] ?? 'gpt-4o',
    quality_score: 0.5 + Math.random() * 0.5,
    tokens_input: 200 + Math.floor(Math.random() * 4000),
    tokens_output: 50 + Math.floor(Math.random() * 1500),
  }));
}

type TableProps = {
  columns: ColumnDef<Span, unknown>[];
  data: readonly Span[];
  height?: number;
};

const meta = {
  title: 'Data Display/DataTable',
  component: DataTable as unknown as React.ComponentType<TableProps>,
  tags: ['data'],
  args: {
    columns: spanColumns,
    data: FIXTURE_SPANS,
  },
} satisfies Meta<React.ComponentType<TableProps>>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    columns: spanColumns,
    data: FIXTURE_SPANS,
    height: 300,
  },
};

export const SearchableEnterprise: Story = {
  render: () => (
    <DataTable
      columns={spanColumns as unknown as ColumnDef<Record<string, unknown>, unknown>[]}
      data={FIXTURE_SPANS as unknown as Record<string, unknown>[]}
      height={350}
      title="Trace Spans Explorer"
      searchable
      searchPlaceholder="Filter spans by model, name, or status..."
      onRowClick={(row) => {
        alert(`Selected span: ${String(row.name)} (${String(row.span_id)})`);
      }}
    />
  ),
};

export const Loading: Story = {
  render: () => (
    <div className="rounded-[var(--radius-lg)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-6">
      <SkeletonState lines={8} />
    </div>
  ),
};

export const Empty: Story = {
  render: () => (
    <DataTable columns={spanColumns as unknown as ColumnDef<Record<string, unknown>, unknown>[]} data={[]} height={300} />
  ),
};

export const Error: Story = {
  render: () => (
    <ErrorState
      message="Failed to query span data. ClickHouse returned a timeout after 30s."
      onRetry={() => {}}
    />
  ),
};

export const DenseCompact: Story = {
  args: {
    columns: spanColumns,
    data: generateLargeDataset(10_000),
    height: 500,
  },
};

export const SingleRow: Story = {
  args: {
    columns: spanColumns,
    data: [FIXTURE_SPANS[0] as Span],
    height: 200,
  },
};
