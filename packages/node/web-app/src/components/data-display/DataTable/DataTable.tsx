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
  if (align === 'right') return 'text-right';
  if (align === 'center') return 'text-center';
  return 'text-left';
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
    <div className={cn('overflow-hidden rounded-[var(--radius-lg)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] text-[hsl(var(--card-foreground))] shadow-sm', className)}>
      <div ref={parentRef} className="relative overflow-auto" style={{ height: `${height}px` }}>
        <table className="w-full border-collapse text-left">
          <thead className="sticky top-0 z-20 block border-b border-[hsl(var(--border))] bg-[hsl(var(--muted)/.75)] text-[11px] font-bold uppercase tracking-wider text-[hsl(var(--muted-foreground))] backdrop-blur-md shadow-sm">
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
                        'select-none px-4 py-3 font-bold text-[11px] tracking-wider text-[hsl(var(--muted-foreground))] shrink-0 truncate',
                        canSort && 'cursor-pointer transition-colors hover:bg-[hsl(var(--muted))] hover:text-[hsl(var(--foreground))]',
                        sortDir !== false && 'text-[hsl(var(--primary))] bg-[hsl(var(--primary)/.08)]'
                      )}
                      onClick={header.column.getToggleSortingHandler()}
                    >
                      <div className={cn('flex w-full items-center gap-1.5', alignClass)}>
                        <span className="truncate">{flexRender(header.column.columnDef.header, header.getContext())}</span>
                        {canSort && (
                          <span className={cn('shrink-0 text-[hsl(var(--muted-foreground)/.7)]', sortDir !== false && 'text-[hsl(var(--primary))]')}>
                            {sortDir === 'desc' && <ArrowDown size={13} aria-label="Sorted descending" className="stroke-[2.5]" />}
                            {sortDir === 'asc' && <ArrowUp size={13} aria-label="Sorted ascending" className="stroke-[2.5]" />}
                            {sortDir === false && <ChevronsUpDown size={13} aria-label="Not sorted" className="opacity-60" />}
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
                  className={cn(
                    'flex w-full items-center border-b border-[hsl(var(--border)/.4)] transition-colors hover:bg-[hsl(var(--muted)/.4)]',
                    isOdd ? 'bg-[hsl(var(--muted)/.2)]' : 'bg-transparent'
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
                          'px-4 py-2 align-middle font-mono text-xs text-[hsl(var(--foreground))] shrink-0 truncate',
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

        {data.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center p-8 text-center text-[hsl(var(--muted-foreground))]">
            No records found.
          </div>
        )}
      </div>
    </div>
  );
}
