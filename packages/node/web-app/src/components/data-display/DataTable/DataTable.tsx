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
}

export function DataTable<TData = Record<string, unknown>>({
  columns,
  data,
  height = 400,
  className,
  estimateRowHeight = 40,
}: DataTableProps<TData>) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const parentRef = useRef<HTMLDivElement>(null);

  const table = useReactTable({
    data: data as TData[],
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
    <div className={cn('overflow-hidden rounded-[var(--radius-lg)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] text-[hsl(var(--card-foreground))]', className)}>
      <div ref={parentRef} className="relative overflow-auto" style={{ height: `${height}px` }}>
        <table className="w-full border-collapse text-left">
          <thead className="sticky top-0 z-10 border-b border-[hsl(var(--border))] bg-[hsl(var(--muted)/.9)] text-xs font-semibold uppercase text-[hsl(var(--muted-foreground))] backdrop-blur-sm">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  const canSort = header.column.getCanSort();
                  const sortDir = header.column.getIsSorted();
                  return (
                    <th
                      key={header.id}
                      className={cn('select-none px-4 py-3', canSort && 'cursor-pointer transition-colors hover:text-[hsl(var(--foreground))]')}
                      onClick={header.column.getToggleSortingHandler()}
                    >
                      <div className="flex items-center gap-1.5">
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {canSort && (
                          <span className="text-[hsl(var(--muted-foreground)/.6)]">
                            {sortDir === 'desc' && <ArrowDown size={12} aria-label="Sorted descending" />}
                            {sortDir === 'asc' && <ArrowUp size={12} aria-label="Sorted ascending" />}
                            {sortDir === false && <ChevronsUpDown size={12} aria-label="Not sorted" />}
                          </span>
                        )}
                      </div>
                    </th>
                  );
                })}
              </tr>
            ))}
          </thead>

          <tbody className="text-sm font-medium" style={{ height: `${rowVirtualizer.getTotalSize()}px`, position: 'relative' }}>
            {rowVirtualizer.getVirtualItems().map((virtualRow) => {
              const row = rows[virtualRow.index];
              if (row === undefined) return null;
              return (
                <tr
                  key={row.id}
                  className="border-b border-[hsl(var(--border)/.4)] transition-colors hover:bg-[hsl(var(--muted)/.3)]"
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: `${virtualRow.size}px`,
                    transform: `translateY(${virtualRow.start}px)`,
                  }}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-2 align-middle">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>

        {data.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center p-8 text-center text-[hsl(var(--muted-foreground))]">
            No records found.
          </div>
        )}
      </div>
    </div>
  );
}
