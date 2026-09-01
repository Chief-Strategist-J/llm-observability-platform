'use client';

import React, { useMemo } from 'react';
import Link from 'next/link';
import { Layers, Search, ExternalLink, Filter, Clock, Cpu, AlertTriangle } from 'lucide-react';
import type { TraceSummary } from '../types';
import type { TracesFilterState } from '../traces.slice';
import { TRACES_TEXT } from '../constants';

export interface TracesDashboardUIProps {
  traces: TraceSummary[];
  filters?: TracesFilterState;
  loading?: boolean;
  error?: string | null;
  onSearchChange?: (query: string) => void;
  onServiceChange?: (service: string) => void;
  onStatusChange?: (status: string) => void;
  onModelChange?: (model: string) => void;
  onMinDurationChange?: (durationMs: number) => void;
  onResetFilters?: () => void;
}

const defaultFilters: TracesFilterState = {
  searchQuery: '',
  selectedService: 'all',
  selectedStatus: 'all',
  selectedModel: 'all',
  minDurationMs: 0,
};

export function TracesDashboardUI({
  traces,
  filters = defaultFilters,
  loading = false,
  error = null,
  onSearchChange,
  onServiceChange,
  onStatusChange,
  onModelChange,
  onMinDurationChange,
  onResetFilters,
}: TracesDashboardUIProps) {
  // Extract available filter options
  const availableServices = useMemo(() => {
    const services = new Set<string>();
    traces.forEach((t) => { if (t.service) services.add(t.service); });
    return Array.from(services);
  }, [traces]);

  const availableModels = useMemo(() => {
    const models = new Set<string>();
    traces.forEach((t) => { if (t.model) models.add(t.model); });
    return Array.from(models);
  }, [traces]);

  // Compute summary stats
  const stats = useMemo(() => {
    if (traces.length === 0) return { total: 0, errorPct: 0, avgDuration: 0, totalTokens: 0, totalCost: 0 };
    const total = traces.length;
    const errors = traces.filter((t) => t.status === 'error').length;
    const totalDur = traces.reduce((acc, t) => acc + t.duration_ms, 0);
    const tokens = traces.reduce((acc, t) => acc + t.total_tokens, 0);
    const cost = traces.reduce((acc, t) => acc + t.cost_usd, 0);

    return {
      total,
      errorPct: parseFloat(((errors / total) * 100).toFixed(1)),
      avgDuration: Math.round(totalDur / total),
      totalTokens: tokens,
      totalCost: parseFloat(cost.toFixed(4)),
    };
  }, [traces]);

  // Pure filtering based on props filters
  const filteredTraces = useMemo(() => {
    const q = (filters.searchQuery || '').toLowerCase();
    return traces.filter((t) => {
      const matchesSearch = q === '' ||
        t.id.toLowerCase().includes(q) ||
        t.root_span_name.toLowerCase().includes(q) ||
        t.service.toLowerCase().includes(q);

      const matchesService = filters.selectedService === 'all' || t.service === filters.selectedService;
      const matchesStatus = filters.selectedStatus === 'all' || t.status === filters.selectedStatus;
      const matchesModel = filters.selectedModel === 'all' || t.model === filters.selectedModel;
      const matchesDuration = t.duration_ms >= (filters.minDurationMs || 0);

      return matchesSearch && matchesService && matchesStatus && matchesModel && matchesDuration;
    });
  }, [traces, filters]);

  if (loading) {
    return (
      <div className="traces-container" role="status" aria-label="Loading traces explorer">
        <div className="traces-kpi-grid">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="traces-kpi-card animate-pulse">
              <div className="h-3 w-1/2 rounded bg-[hsl(var(--muted))]" />
              <div className="h-8 w-3/4 rounded bg-[hsl(var(--muted))]" />
            </div>
          ))}
        </div>
        <div className="traces-card-panel space-y-4 animate-pulse">
          <div className="h-4 w-1/4 bg-[hsl(var(--muted))] rounded" />
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-10 w-full bg-[hsl(var(--muted)/0.3)] rounded" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="traces-container">
      {error && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-500 text-xs font-medium">
          {error}
        </div>
      )}

      {/* Summary KPI Bar */}
      <div className="traces-kpi-grid">
        <div className="traces-kpi-card">
          <div className="traces-kpi-header">
            <span>{TRACES_TEXT.KPI_TOTAL_TRACES}</span>
            <Layers className="w-4 h-4 text-primary" />
          </div>
          <div className="traces-kpi-value">{stats.total.toLocaleString()}</div>
          <div className="traces-kpi-desc">{TRACES_TEXT.KPI_TOTAL_TRACES_DESC}</div>
        </div>

        <div className="traces-kpi-card">
          <div className="traces-kpi-header">
            <span>{TRACES_TEXT.KPI_AVG_LATENCY}</span>
            <Clock className="w-4 h-4 text-blue-500" />
          </div>
          <div className="traces-kpi-value">{stats.avgDuration} ms</div>
          <div className="traces-kpi-desc">{TRACES_TEXT.KPI_AVG_LATENCY_DESC}</div>
        </div>

        <div className="traces-kpi-card">
          <div className="traces-kpi-header">
            <span>{TRACES_TEXT.KPI_ERROR_RATE}</span>
            <AlertTriangle className="w-4 h-4 text-rose-500" />
          </div>
          <div className={`traces-kpi-value ${stats.errorPct > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
            {stats.errorPct}%
          </div>
          <div className="traces-kpi-desc">{TRACES_TEXT.KPI_ERROR_RATE_DESC}</div>
        </div>

        <div className="traces-kpi-card">
          <div className="traces-kpi-header">
            <span>{TRACES_TEXT.KPI_TOTAL_TOKENS}</span>
            <Cpu className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="traces-kpi-value font-mono">{stats.totalTokens.toLocaleString()}</div>
          <div className="traces-kpi-desc">${stats.totalCost} {TRACES_TEXT.KPI_TOTAL_TOKENS_DESC}</div>
        </div>
      </div>

      {/* Main Traces Table Container */}
      <div className="traces-card-panel">
        {/* Header & Filter Controls Bar */}
        <div className="traces-filter-bar">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <Layers className="w-4 h-4 text-primary" />
            <span>{TRACES_TEXT.HEADER_TITLE}</span>
          </div>

          <div className="traces-filter-controls">
            {/* Search Input */}
            <div className="traces-search-wrapper">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[hsl(var(--muted-foreground))]" />
              <input
                type="text"
                placeholder={TRACES_TEXT.SEARCH_PLACEHOLDER}
                value={filters.searchQuery || ''}
                onChange={(e) => onSearchChange?.(e.target.value)}
                className="traces-search-input"
              />
            </div>

            {/* Service Dropdown */}
            <select
              value={filters.selectedService || 'all'}
              onChange={(e) => onServiceChange?.(e.target.value)}
              className="traces-select"
            >
              <option value="all">{TRACES_TEXT.FILTER_ALL_SERVICES}</option>
              {availableServices.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>

            {/* Status Dropdown */}
            <select
              value={filters.selectedStatus || 'all'}
              onChange={(e) => onStatusChange?.(e.target.value)}
              className="traces-select"
            >
              <option value="all">{TRACES_TEXT.FILTER_ALL_STATUSES}</option>
              <option value="success">{TRACES_TEXT.FILTER_STATUS_SUCCESS}</option>
              <option value="error">{TRACES_TEXT.FILTER_STATUS_ERROR}</option>
            </select>

            {/* Model Dropdown */}
            {availableModels.length > 0 && (
              <select
                value={filters.selectedModel || 'all'}
                onChange={(e) => onModelChange?.(e.target.value)}
                className="traces-select"
              >
                <option value="all">{TRACES_TEXT.FILTER_ALL_MODELS}</option>
                {availableModels.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            )}

            {/* Min Duration Threshold Filter */}
            <div className="flex items-center gap-1.5 border border-[hsl(var(--border))] bg-[hsl(var(--muted)/0.3)] py-1 px-2.5 rounded-lg text-xs">
              <span className="text-[10px] text-[hsl(var(--muted-foreground))]">{TRACES_TEXT.FILTER_MIN_DURATION_PREFIX}</span>
              <input
                type="number"
                min="0"
                step="50"
                value={filters.minDurationMs || ''}
                onChange={(e) => onMinDurationChange?.(Number(e.target.value) || 0)}
                placeholder={TRACES_TEXT.FILTER_MIN_DURATION_PLACEHOLDER}
                className="w-16 bg-transparent text-xs text-primary font-mono focus:outline-none"
              />
            </div>
          </div>
        </div>

        {/* Traces Table View */}
        <div className="traces-table-wrapper">
          {filteredTraces.length === 0 ? (
            <div className="text-xs text-[hsl(var(--muted-foreground))] py-10 text-center flex flex-col items-center gap-2">
              <Filter className="w-6 h-6 opacity-40 text-primary" />
              <span>{TRACES_TEXT.NO_TRACES_MATCH}</span>
              {onResetFilters && (
                <button
                  onClick={onResetFilters}
                  className="text-xs text-primary hover:underline mt-1 font-medium"
                >
                  {TRACES_TEXT.FILTER_RESET_BUTTON}
                </button>
              )}
            </div>
          ) : (
            <table className="traces-table">
              <thead>
                <tr className="traces-table-head">
                  <th className="py-2.5 px-3">{TRACES_TEXT.TABLE_TRACE_ID}</th>
                  <th className="py-2.5 px-3">{TRACES_TEXT.TABLE_ROOT_OPERATION}</th>
                  <th className="py-2.5 px-3">{TRACES_TEXT.TABLE_SERVICE}</th>
                  <th className="py-2.5 px-3">{TRACES_TEXT.TABLE_MODEL}</th>
                  <th className="py-2.5 px-3">{TRACES_TEXT.TABLE_DURATION}</th>
                  <th className="py-2.5 px-3">{TRACES_TEXT.TABLE_TOKENS}</th>
                  <th className="py-2.5 px-3">{TRACES_TEXT.TABLE_EST_COST}</th>
                  <th className="py-2.5 px-3">{TRACES_TEXT.TABLE_STATUS}</th>
                  <th className="py-2.5 px-3 text-right">{TRACES_TEXT.TABLE_ACTION_FLAME}</th>
                </tr>
              </thead>
              <tbody>
                {filteredTraces.map((trc) => {
                  const isSlow = trc.duration_ms > 1000;
                  return (
                    <tr key={trc.id} className="traces-table-row">
                      <td className="py-2.5 px-3 font-mono font-medium text-primary">{trc.id}</td>
                      <td className="py-2.5 px-3 font-semibold text-[hsl(var(--foreground))]">{trc.root_span_name}</td>
                      <td className="py-2.5 px-3 text-[hsl(var(--muted-foreground))]">
                        <span className="px-2 py-0.5 rounded bg-[hsl(var(--muted)/0.5)] font-mono text-[10px]">
                          {trc.service}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-mono text-amber-400">{trc.model}</td>
                      <td className="py-2.5 px-3 font-mono">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                          isSlow ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'text-[hsl(var(--foreground))]'
                        }`}>
                          {trc.duration_ms} ms
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-mono text-[hsl(var(--foreground))]">{trc.total_tokens.toLocaleString()}</td>
                      <td className="py-2.5 px-3 font-mono text-emerald-400">${trc.cost_usd.toFixed(4)}</td>
                      <td className="py-2.5 px-3">
                        <span className={trc.status === 'success' ? 'traces-badge-success' : 'traces-badge-error'}>
                          {trc.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <Link
                          href={`/traces/${trc.id}`}
                          className="inline-flex items-center gap-1.5 text-[11px] font-medium text-primary hover:text-indigo-400 transition-colors"
                        >
                          <span>{TRACES_TEXT.TABLE_ACTION_FLAME}</span>
                          <ExternalLink size={12} />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
