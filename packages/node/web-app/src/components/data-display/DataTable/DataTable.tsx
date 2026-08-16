'use client';

import React, { useRef, useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
} from '@tanstack/react-table';
import { useVirtualizer } from '@tanstack/react-virtual';
import { ArrowDown, ArrowUp, ChevronsUpDown } from 'lucide-react';
import { cn } from '../../../lib/cn';
import { formatCostUsdMicro, formatLatencyMs, formatTokens } from '../../../lib/formatters';

export const columnFormatters = {
  cost_usd_micro: (value: number) => formatCostUsdMicro(value).compact,
  latency_ms: (value: number) => formatLatencyMs(value),
  tokens: (value: number) => formatTokens(value),
} as const;

interface DataTableProps<TData> {
  readonly columns: ColumnDef<TData, unknown>[];
  readonly data: readonly TData[];
  readonly height?: number;
  readonly className?: string;
  readonly estimateRowHeight?: number;
  readonly searchable?: boolean;
  readonly searchPlaceholder?: string;
  readonly title?: string;
  readonly onRowClick?: (row: TData) => void;
}

type ColumnAlignment = 'left' | 'center' | 'right';

function getColumnAlignment<TData>(columnDef: ColumnDef<TData, unknown>): ColumnAlignment {
  const meta = columnDef.meta as { align?: ColumnAlignment } | undefined;
  return meta?.align ?? 'left';
}

function getHeaderAlignmentClass(align: ColumnAlignment): string {
  if (align === 'right') return 'text-right justify-end';
  if (align === 'center') return 'text-center justify-center';
  return 'text-left justify-start';
}

function getCellAlignmentClass(align: ColumnAlignment): string {
  if (align === 'right') return 'text-right tabular-nums';
  if (align === 'center') return 'text-center';
  return 'text-left';
}

interface TableToolbarProps {
  readonly title?: string;
  readonly count: number;
  readonly searchable: boolean;
  readonly searchQuery: string;
  readonly searchPlaceholder: string;
  readonly onSearchChange: (q: string) => void;
}

function TableToolbar({
  title,
  count,
  searchable,
  searchQuery,
  searchPlaceholder,
  onSearchChange,
}: TableToolbarProps) {
  if (!searchable && !title) return null;
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[hsl(var(--border))] bg-[hsl(var(--card))] px-4 py-3">
      <div className="flex items-center gap-2">
        {title && <span className="font-semibold text-sm tracking-tight text-[hsl(var(--foreground))]">{title}</span>}
        <span className="rounded-full bg-[hsl(var(--muted))] px-2.5 py-0.5 font-mono text-[11px] font-medium text-[hsl(var(--muted-foreground))]">
          {count.toLocaleString()} {count === 1 ? 'entry' : 'entries'}
        </span>
      </div>

      {searchable && (
        <div className="relative flex items-center">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder={searchPlaceholder}
            className="h-8 w-64 rounded-[var(--radius-md)] border border-[hsl(var(--border))] bg-[hsl(var(--background))] px-3 text-xs text-[hsl(var(--foreground))] placeholder-[hsl(var(--muted-foreground))] outline-none transition-colors focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => onSearchChange('')}
              className="absolute right-2 text-xs text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]"
            >
              ✕
            </button>
          )}
        </div>
      )}
    </div>
  );
}

function TableFooter({ visibleCount, totalCount }: { readonly visibleCount: number; readonly totalCount: number }) {
  return (
    <div className="flex items-center justify-between border-t border-[hsl(var(--border))] bg-[hsl(var(--card))] px-4 py-2 text-xs text-[hsl(var(--muted-foreground))]">
      <span>Showing {visibleCount.toLocaleString()} of {totalCount.toLocaleString()} rows</span>
      <span className="font-mono text-[11px]">Virtual Scroll Active</span>
    </div>
  );
}

export function DataTable<TData = Record<string, unknown>>({
  columns,
  data,
  height = 400,
  className,
  estimateRowHeight = 40,
  searchable = false,
  searchPlaceholder = 'Filter records...',
  title,
  onRowClick,
}: DataTableProps<TData>) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const parentRef = useRef<HTMLDivElement>(null);

  const filteredData = React.useMemo(() => {
    if (!searchQuery.trim()) return data as TData[];
    const q = searchQuery.toLowerCase();
    return (data as TData[]).filter((row) =>
      Object.values(row as Record<string, unknown>).some(
        (val) => val !== null && val !== undefined && String(val).toLowerCase().includes(q)
      )
    );
  }, [data, searchQuery]);

  const table = useReactTable({
    data: filteredData,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  const { rows } = table.getRowModel();

  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => estimateRowHeight,
    overscan: 10,
  });

  return (
    <div className={cn('flex flex-col overflow-hidden rounded-[var(--radius-lg)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] text-[hsl(var(--card-foreground))] shadow-md', className)}>
      <TableToolbar
        title={title}
        count={filteredData.length}
        searchable={searchable}
        searchQuery={searchQuery}
        searchPlaceholder={searchPlaceholder}
        onSearchChange={setSearchQuery}
      />

      <div ref={parentRef} className="relative overflow-auto" style={{ height: `${height}px` }}>
        <table className="w-full border-collapse text-left">
          <thead className="sticky top-0 z-20 block border-b border-[hsl(var(--border))] bg-[hsl(var(--muted)/.85)] text-[11px] font-bold uppercase tracking-wider text-[hsl(var(--muted-foreground))] backdrop-blur-md">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} className="flex w-full min-w-full items-center">
                {headerGroup.headers.map((header) => {
                  const canSort = header.column.getCanSort();
                  const sortDir = header.column.getIsSorted();
                  const align = getColumnAlignment(header.column.columnDef);
                  const alignClass = getHeaderAlignmentClass(align);
                  const colSize = header.getSize();
                  const flexStyle = header.column.columnDef.size ? `0 0 ${colSize}px` : '1 1 0%';

                  return (
                    <th
                      key={header.id}
                      style={{ width: `${colSize}px`, flex: flexStyle }}
                      className={cn(
                        'select-none border-r border-[hsl(var(--border)/.25)] px-4 py-2.5 font-bold text-[11px] tracking-wider text-[hsl(var(--muted-foreground))] last:border-r-0 shrink-0 truncate',
                        canSort && 'cursor-pointer transition-colors hover:bg-[hsl(var(--muted))] hover:text-[hsl(var(--foreground))]',
                        sortDir !== false && 'text-[hsl(var(--primary))] bg-[hsl(var(--primary)/.08)] font-extrabold'
                      )}
                      onClick={header.column.getToggleSortingHandler()}
                    >
                      <div className={cn('flex w-full items-center gap-1.5', alignClass)}>
                        <span className="truncate">{flexRender(header.column.columnDef.header, header.getContext())}</span>
                        {canSort && (
                          <span className={cn('shrink-0 text-[hsl(var(--muted-foreground)/.7)]', sortDir !== false && 'text-[hsl(var(--primary))]')}>
                            {sortDir === 'desc' && <ArrowDown size={13} aria-label="Sorted descending" className="stroke-[2.5]" />}
                            {sortDir === 'asc' && <ArrowUp size={13} aria-label="Sorted ascending" className="stroke-[2.5]" />}
                            {sortDir === false && <ChevronsUpDown size={13} aria-label="Not sorted" className="opacity-50" />}
                          </span>
                        )}
                      </div>
                    </th>
                  );
                })}
              </tr>
            ))}
          </thead>

          <tbody className="block text-sm font-medium" style={{ height: `${rowVirtualizer.getTotalSize()}px`, position: 'relative' }}>
            {rowVirtualizer.getVirtualItems().map((virtualRow) => {
              const row = rows[virtualRow.index];
              if (row === undefined) return null;
              const isOdd = virtualRow.index % 2 !== 0;
              return (
                <tr
                  key={row.id}
                  onClick={() => onRowClick?.(row.original)}
                  className={cn(
                    'flex w-full items-center border-b border-[hsl(var(--border)/.3)] transition-colors hover:bg-[hsl(var(--accent)/.15)]',
                    isOdd ? 'bg-[hsl(var(--muted)/.15)]' : 'bg-transparent',
                    onRowClick && 'cursor-pointer'
                  )}
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: `${virtualRow.size}px`,
                    transform: `translateY(${virtualRow.start}px)`,
                  }}
                >
                  {row.getVisibleCells().map((cell) => {
                    const align = getColumnAlignment(cell.column.columnDef);
                    const cellAlignClass = getCellAlignmentClass(align);
                    const colSize = cell.column.getSize();
                    const flexStyle = cell.column.columnDef.size ? `0 0 ${colSize}px` : '1 1 0%';
                    return (
                      <td
                        key={cell.id}
                        style={{ width: `${colSize}px`, flex: flexStyle }}
                        className={cn(
                          'border-r border-[hsl(var(--border)/.15)] px-4 py-2 align-middle font-mono text-xs text-[hsl(var(--foreground))] last:border-r-0 shrink-0 truncate',
                          cellAlignClass
                        )}
                      >
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>

        {filteredData.length === 0 && (
          <div className="absolute inset-0 flex flex-col items-center justify-center p-8 text-center text-[hsl(var(--muted-foreground))]">
            <span className="font-semibold text-sm">No records found</span>
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="mt-2 text-xs text-[hsl(var(--primary))] hover:underline"
              >
                Clear filter search
              </button>
            )}
          </div>
        )}
      </div>

      <TableFooter visibleCount={rows.length} totalCount={data.length} />
    </div>
  );
}
