'use client';

import React, { useState, useMemo } from 'react';
import Link from 'next/link';
import { Layers, Search, ExternalLink, Filter, Clock, Activity, DollarSign, Cpu, AlertTriangle, ArrowUpDown } from 'lucide-react';
import type { TraceSummary } from '../types';

export interface TracesDashboardUIProps {
  traces: TraceSummary[];
  loading?: boolean;
  error?: string | null;
}

export function TracesDashboardUI({
  traces,
  loading = false,
  error = null,
}: TracesDashboardUIProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedService, setSelectedService] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedModel, setSelectedModel] = useState<string>('all');
  const [minDurationMs, setMinDurationMs] = useState<number>(0);

  // Extract unique services and models for filter dropdowns
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

  // Filter traces
  const filteredTraces = useMemo(() => {
    return traces.filter((t) => {
      const matchesSearch = searchQuery === '' ||
        t.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.root_span_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.service.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesService = selectedService === 'all' || t.service === selectedService;
      const matchesStatus = selectedStatus === 'all' || t.status === selectedStatus;
      const matchesModel = selectedModel === 'all' || t.model === selectedModel;
      const matchesDuration = t.duration_ms >= minDurationMs;

      return matchesSearch && matchesService && matchesStatus && matchesModel && matchesDuration;
    });
  }, [traces, searchQuery, selectedService, selectedStatus, selectedModel, minDurationMs]);

  if (loading) {
    return (
      <div className="flex flex-col gap-6" role="status" aria-label="Loading traces explorer">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-3 animate-pulse">
              <div className="h-3 w-1/2 rounded bg-[hsl(var(--muted))]" />
              <div className="h-8 w-3/4 rounded bg-[hsl(var(--muted))]" />
            </div>
          ))}
        </div>
        <div className="p-5 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm space-y-4 animate-pulse">
          <div className="h-4 w-1/4 bg-[hsl(var(--muted))] rounded" />
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-10 w-full bg-[hsl(var(--muted)/0.3)] rounded" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {error && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-500 text-xs font-medium">
          {error}
        </div>
      )}

      {/* Summary KPI Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-1">
          <div className="flex items-center justify-between text-xs text-[hsl(var(--muted-foreground))]">
            <span>Total Traces</span>
            <Layers className="w-4 h-4 text-primary" />
          </div>
          <div className="text-2xl font-bold">{stats.total.toLocaleString()}</div>
          <div className="text-[10px] text-[hsl(var(--muted-foreground))] mt-1">Recorded execution streams</div>
        </div>

        <div className="p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-1">
          <div className="flex items-center justify-between text-xs text-[hsl(var(--muted-foreground))]">
            <span>Avg Latency</span>
            <Clock className="w-4 h-4 text-blue-500" />
          </div>
          <div className="text-2xl font-bold">{stats.avgDuration} ms</div>
          <div className="text-[10px] text-[hsl(var(--muted-foreground))] mt-1">Average trace duration</div>
        </div>

        <div className="p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-1">
          <div className="flex items-center justify-between text-xs text-[hsl(var(--muted-foreground))]">
            <span>Error Rate</span>
            <AlertTriangle className="w-4 h-4 text-rose-500" />
          </div>
          <div className={`text-2xl font-bold ${stats.errorPct > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
            {stats.errorPct}%
          </div>
          <div className="text-[10px] text-[hsl(var(--muted-foreground))] mt-1">Trace failures ratio</div>
        </div>

        <div className="p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-1">
          <div className="flex items-center justify-between text-xs text-[hsl(var(--muted-foreground))]">
            <span>Total Tokens</span>
            <Cpu className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="text-2xl font-bold font-mono">{stats.totalTokens.toLocaleString()}</div>
          <div className="text-[10px] text-[hsl(var(--muted-foreground))] mt-1">${stats.totalCost} total spend</div>
        </div>
      </div>

      {/* Main Traces Table Container */}
      <div className="p-5 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-4">
        {/* Header & Filter Controls Bar */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-[hsl(var(--border))] pb-4">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <Layers className="w-4 h-4 text-primary" />
            <span>Distributed Spans & Execution Traces</span>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Search Input */}
            <div className="relative flex-1 min-w-[200px]">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[hsl(var(--muted-foreground))]" />
              <input
                type="text"
                placeholder="Search trace ID, operation..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--muted)/0.3)] text-xs placeholder:text-[hsl(var(--muted-foreground))] focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>

            {/* Service Dropdown */}
            <select
              value={selectedService}
              onChange={(e) => setSelectedService(e.target.value)}
              className="py-1.5 px-2.5 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--muted)/0.3)] text-xs focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="all">All Services</option>
              {availableServices.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>

            {/* Status Dropdown */}
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="py-1.5 px-2.5 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--muted)/0.3)] text-xs focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="all">All Statuses</option>
              <option value="success">Success</option>
              <option value="error">Error</option>
            </select>

            {/* Model Dropdown */}
            {availableModels.length > 0 && (
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="py-1.5 px-2.5 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--muted)/0.3)] text-xs focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="all">All Models</option>
                {availableModels.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            )}

            {/* Min Duration Threshold Filter */}
            <div className="flex items-center gap-1.5 border border-[hsl(var(--border))] bg-[hsl(var(--muted)/0.3)] py-1 px-2.5 rounded-lg text-xs">
              <span className="text-[10px] text-[hsl(var(--muted-foreground))]">Min:</span>
              <input
                type="number"
                min="0"
                step="50"
                value={minDurationMs || ''}
                onChange={(e) => setMinDurationMs(Number(e.target.value) || 0)}
                placeholder="0 ms"
                className="w-16 bg-transparent text-xs text-primary font-mono focus:outline-none"
              />
            </div>
          </div>
        </div>

        {/* Traces Table View */}
        <div className="overflow-x-auto">
          {filteredTraces.length === 0 ? (
            <div className="text-xs text-[hsl(var(--muted-foreground))] py-10 text-center flex flex-col items-center gap-2">
              <Filter className="w-6 h-6 opacity-40 text-primary" />
              <span>No distributed traces recorded matching your filter parameters.</span>
              <button
                onClick={() => { setSearchQuery(''); setSelectedService('all'); setSelectedStatus('all'); setSelectedModel('all'); setMinDurationMs(0); }}
                className="text-xs text-primary hover:underline mt-1 font-medium"
              >
                Reset All Filters
              </button>
            </div>
          ) : (
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="border-b border-[hsl(var(--border))] text-[10px] font-bold uppercase tracking-wider text-[hsl(var(--muted-foreground))] bg-[hsl(var(--muted)/0.2)]">
                  <th className="py-2.5 px-3">Trace ID</th>
                  <th className="py-2.5 px-3">Root Operation</th>
                  <th className="py-2.5 px-3">Service</th>
                  <th className="py-2.5 px-3">Model</th>
                  <th className="py-2.5 px-3">Duration</th>
                  <th className="py-2.5 px-3">Tokens</th>
                  <th className="py-2.5 px-3">Est. Cost</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Waterfall</th>
                </tr>
              </thead>
              <tbody>
                {filteredTraces.map((trc) => {
                  const isSlow = trc.duration_ms > 1000;
                  return (
                    <tr key={trc.id} className="border-b border-[hsl(var(--border)/0.4)] hover:bg-[hsl(var(--muted)/0.2)] transition-colors">
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
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                          trc.status === 'success' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                        }`}>
                          {trc.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <Link
                          href={`/traces/${trc.id}`}
                          className="inline-flex items-center gap-1.5 text-[11px] font-medium text-primary hover:text-indigo-400 transition-colors"
                        >
                          <span>Flame Graph</span>
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
