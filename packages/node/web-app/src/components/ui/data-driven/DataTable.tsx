"use client";

import React, { useMemo, useState } from "react";
import { transformList } from "../../../core/data-driven/list-transform";
import type { ListOp } from "../../../core/data-driven/transform.types";
import { Input } from "../../primitives/Input";

export interface ColumnConfig<T = any> {
  key: string;
  label: string;
  render?: (row: T) => React.ReactNode;
}

export function DataTable<T extends Record<string, any>>({
  columns,
  rows,
  searchFields = [],
  title,
  extraOps = [],
  actions,
}: {
  columns: ColumnConfig<T>[];
  rows: T[];
  searchFields?: string[];
  title?: string;
  extraOps?: ListOp[];
  actions?: (row: T) => React.ReactNode;
}) {
  const [query, setQuery] = useState("");
  const [sortField, setSortField] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");

  const visibleRows = useMemo(() => {
    const ops: ListOp[] = [...extraOps];
    if (query && searchFields.length > 0) {
      ops.push({ op: "search", fields: searchFields, query });
    }
    if (sortField) {
      ops.push({ op: "sort", field: sortField, dir: sortDir });
    }
    return transformList(rows, ops);
  }, [rows, query, searchFields, sortField, sortDir, extraOps]);

  const handleSort = (fieldKey: string) => {
    if (sortField === fieldKey) {
      setSortDir((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(fieldKey);
      setSortDir("asc");
    }
  };

  return (
    <div className="space-y-4 rounded-[var(--radius-xl)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-6 shadow-md text-[hsl(var(--card-foreground))]">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {title && <h3 className="text-lg font-bold tracking-tight text-[hsl(var(--foreground))]">{title}</h3>}
        {searchFields.length > 0 && (
          <div className="w-full sm:w-64">
            <Input
              type="text"
              placeholder="Search records..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
        )}
      </div>

      <div className="overflow-x-auto rounded-[var(--radius-md)] border border-[hsl(var(--border))]">
        <table className="w-full text-left text-sm">
          <thead className="bg-[hsl(var(--muted)/.4)] text-xs uppercase text-[hsl(var(--muted-foreground))] font-semibold border-b border-[hsl(var(--border))]">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  className="px-4 py-3 cursor-pointer hover:text-[hsl(var(--foreground))] transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>{col.label}</span>
                    {sortField === col.key && (
                      <span className="text-[hsl(var(--primary))]">{sortDir === "asc" ? "↑" : "↓"}</span>
                    )}
                  </div>
                </th>
              ))}
              {actions && <th className="px-4 py-3 text-right">Actions</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-[hsl(var(--border))] bg-[hsl(var(--card))]">
            {visibleRows.length === 0 ? (
              <tr>
                <td colSpan={columns.length + (actions ? 1 : 0)} className="px-4 py-8 text-center text-[hsl(var(--muted-foreground))]">
                  No records found
                </td>
              </tr>
            ) : (
              visibleRows.map((row, idx) => (
                <tr key={row.id || idx} className="hover:bg-[hsl(var(--muted)/.2)] transition-colors">
                  {columns.map((col) => (
                    <td key={col.key} className="px-4 py-3 font-mono text-xs text-[hsl(var(--foreground))]">
                      {col.render ? col.render(row) : String(row[col.key] ?? "-")}
                    </td>
                  ))}
                  {actions && <td className="px-4 py-3 text-right">{actions(row)}</td>}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
