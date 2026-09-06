'use client';

import React from 'react';
import { Filter, RotateCcw, Calendar, Cpu, Server, Layers } from 'lucide-react';
import type { DashboardFilters, TimeRangeOption } from '../../hooks/useDashboardFilters';

export interface DashboardFilterBarProps {
  filters: DashboardFilters;
  onFilterChange: (key: keyof DashboardFilters, value: string | null) => void;
  onReset: () => void;
  hasActiveFilters: boolean;
  modelOptions?: Array<{ label: string; value: string }>;
  serviceOptions?: Array<{ label: string; value: string }>;
  environmentOptions?: Array<{ label: string; value: string }>;
}

const DEFAULT_MODELS = [
  { label: 'All Models', value: 'all' },
  { label: 'GPT-4o', value: 'gpt-4o' },
  { label: 'GPT-4o Mini', value: 'gpt-4o-mini' },
  { label: 'Claude 3.5 Sonnet', value: 'claude-3-5-sonnet' },
  { label: 'Gemini 1.5 Pro', value: 'gemini-1.5-pro' },
];

const DEFAULT_SERVICES = [
  { label: 'All Services', value: 'all' },
  { label: 'Checkout Service', value: 'checkout-service' },
  { label: 'Recommendation API', value: 'recommendation-api' },
  { label: 'Customer Support Bot', value: 'customer-support-bot' },
  { label: 'Latency Pipeline', value: 'latency-pipeline' },
];

const DEFAULT_ENVIRONMENTS = [
  { label: 'All Environments', value: 'all' },
  { label: 'Production', value: 'production' },
  { label: 'Staging', value: 'staging' },
  { label: 'Development', value: 'development' },
];

export function DashboardFilterBar({
  filters,
  onFilterChange,
  onReset,
  hasActiveFilters,
  modelOptions = DEFAULT_MODELS,
  serviceOptions = DEFAULT_SERVICES,
  environmentOptions = DEFAULT_ENVIRONMENTS,
}: DashboardFilterBarProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card)/0.6)] backdrop-blur-md shadow-sm">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))] pr-2 border-r border-[hsl(var(--border))]">
          <Filter className="w-3.5 h-3.5" />
          <span>Filters</span>
        </div>

        <div className="flex items-center gap-1.5">
          <Calendar className="w-3.5 h-3.5 text-[hsl(var(--muted-foreground))]" />
          <select
            value={filters.timeRange}
            onChange={(e) => onFilterChange('timeRange', e.target.value as TimeRangeOption)}
            className="h-8 rounded-lg border border-[hsl(var(--input))] bg-[hsl(var(--background))] px-2.5 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
          >
            <option value="1h">Last 1 Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="custom">Custom Range</option>
          </select>
        </div>

        {filters.timeRange === 'custom' && (
          <div className="flex items-center gap-2">
            <input
              type="datetime-local"
              value={filters.from ? filters.from.substring(0, 16) : ''}
              onChange={(e) => onFilterChange('from', e.target.value ? new Date(e.target.value).toISOString() : null)}
              className="h-8 rounded-lg border border-[hsl(var(--input))] bg-[hsl(var(--background))] px-2 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
            />
            <span className="text-xs text-[hsl(var(--muted-foreground))]">to</span>
            <input
              type="datetime-local"
              value={filters.to ? filters.to.substring(0, 16) : ''}
              onChange={(e) => onFilterChange('to', e.target.value ? new Date(e.target.value).toISOString() : null)}
              className="h-8 rounded-lg border border-[hsl(var(--input))] bg-[hsl(var(--background))] px-2 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
            />
          </div>
        )}

        <div className="flex items-center gap-1.5">
          <Cpu className="w-3.5 h-3.5 text-[hsl(var(--muted-foreground))]" />
          <select
            value={filters.model}
            onChange={(e) => onFilterChange('model', e.target.value === 'all' ? null : e.target.value)}
            className="h-8 rounded-lg border border-[hsl(var(--input))] bg-[hsl(var(--background))] px-2.5 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
          >
            {modelOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-1.5">
          <Server className="w-3.5 h-3.5 text-[hsl(var(--muted-foreground))]" />
          <select
            value={filters.service}
            onChange={(e) => onFilterChange('service', e.target.value === 'all' ? null : e.target.value)}
            className="h-8 rounded-lg border border-[hsl(var(--input))] bg-[hsl(var(--background))] px-2.5 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
          >
            {serviceOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-[hsl(var(--muted-foreground))]" />
          <select
            value={filters.environment}
            onChange={(e) => onFilterChange('environment', e.target.value === 'all' ? null : e.target.value)}
            className="h-8 rounded-lg border border-[hsl(var(--input))] bg-[hsl(var(--background))] px-2.5 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
          >
            {environmentOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {hasActiveFilters && (
        <button
          onClick={onReset}
          className="flex items-center gap-1.5 h-8 px-3 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--muted)/0.3)] hover:bg-[hsl(var(--muted)/0.6)] text-xs font-medium transition-colors"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Reset Filters</span>
        </button>
      )}
    </div>
  );
}
