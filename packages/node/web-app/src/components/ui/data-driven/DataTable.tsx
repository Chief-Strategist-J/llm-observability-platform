"use client";

import React, { useMemo, useState } from "react";
import { transformList } from "../../../core/data-driven/list-transform";
import type { ListOp } from "../../../core/data-driven/transform.types";

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
    <div className="space-y-4 rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {title && <h3 className="text-lg font-semibold text-slate-100">{title}</h3>}
        {searchFields.length > 0 && (
          <input
            type="text"
            placeholder="Search records..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full sm:w-64 rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-1.5 text-sm text-slate-100 placeholder-slate-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 transition-all"
          />
        )}
      </div>

      <div className="overflow-x-auto rounded-lg border border-slate-800">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-950/80 text-xs uppercase text-slate-400 font-semibold border-b border-slate-800">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  className="px-4 py-3 cursor-pointer hover:text-slate-100 transition-colors"
                >
                  <div className="flex items-center space-x-1">
                    <span>{col.label}</span>
                    {sortField === col.key && (
                      <span className="text-cyan-400">{sortDir === "asc" ? "↑" : "↓"}</span>
                    )}
                  </div>
                </th>
              ))}
              {actions && <th className="px-4 py-3 text-right">Actions</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 bg-slate-900/30">
            {visibleRows.length === 0 ? (
              <tr>
                <td colSpan={columns.length + (actions ? 1 : 0)} className="px-4 py-8 text-center text-slate-500">
                  No records found
                </td>
              </tr>
            ) : (
              visibleRows.map((row, idx) => (
                <tr key={row.id || idx} className="hover:bg-slate-800/40 transition-colors">
                  {columns.map((col) => (
                    <td key={col.key} className="px-4 py-3 font-mono text-xs">
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
