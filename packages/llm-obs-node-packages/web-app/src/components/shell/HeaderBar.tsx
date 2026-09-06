'use client';

import React, { useState } from 'react';
import { RefreshCw, Layers, Clock } from 'lucide-react';
import { SearchableDropdown } from '../ui/SearchableDropdown';

const ENVIRONMENT_OPTIONS = [
  { id: 'prod-us-east', label: 'Production (us-east-1)', description: 'Primary AWS Region', icon: <Layers className="h-3.5 w-3.5" />, value: 'prod-us-east' },
  { id: 'prod-eu-west', label: 'Production (eu-west-1)', description: 'Frankfurt Cluster', icon: <Layers className="h-3.5 w-3.5" />, value: 'prod-eu-west' },
  { id: 'staging', label: 'Staging Sandbox', description: 'Dev Testing Cluster', icon: <Layers className="h-3.5 w-3.5" />, value: 'staging' },
];

const TIME_RANGE_OPTIONS = [
  { id: '15m', label: 'Last 15 minutes', icon: <Clock className="h-3.5 w-3.5" />, value: '15m' },
  { id: '1h', label: 'Last 1 hour', icon: <Clock className="h-3.5 w-3.5" />, value: '1h' },
  { id: '6h', label: 'Last 6 hours', icon: <Clock className="h-3.5 w-3.5" />, value: '6h' },
  { id: '24h', label: 'Last 24 hours', icon: <Clock className="h-3.5 w-3.5" />, value: '24h' },
  { id: '7d', label: 'Last 7 days', icon: <Clock className="h-3.5 w-3.5" />, value: '7d' },
];

const REFRESH_RATE_OPTIONS = [
  { id: 'off', label: 'Auto-Refresh: Off', value: 'off' },
  { id: '5s', label: 'Every 5 seconds', value: '5s' },
  { id: '10s', label: 'Every 10 seconds', value: '10s' },
  { id: '30s', label: 'Every 30 seconds', value: '30s' },
];

export function HeaderBar() {
  const [environment, setEnvironment] = useState('prod-us-east');
  const [timeRange, setTimeRange] = useState('1h');
  const [refreshRate, setRefreshRate] = useState('5s');
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefreshClick = () => {
    setIsRefreshing(true);
    setTimeout(() => setIsRefreshing(false), 700);
  };

  return (
    <header className="h-14 border-b border-[hsl(var(--border))] bg-[hsl(var(--card))] px-4 flex items-center justify-between text-xs text-[hsl(var(--foreground))] shrink-0 shadow-sm">
      {/* Left: Environment & Live Status */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1 rounded-full dark:bg-emerald-950/80 bg-emerald-100/90 dark:text-emerald-300 text-emerald-900 border border-emerald-500/50 font-bold text-[11px] shrink-0">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span>Live Ingestion Engine</span>
        </div>

        <div className="hidden sm:block w-56">
          <SearchableDropdown
            items={ENVIRONMENT_OPTIONS}
            value={environment}
            onChange={setEnvironment}
            placeholder="Search environment..."
          />
        </div>
      </div>

      {/* Right: Time Range, Refresh & Controls */}
      <div className="flex items-center gap-3">
        <div className="w-44">
          <SearchableDropdown
            items={TIME_RANGE_OPTIONS}
            value={timeRange}
            onChange={setTimeRange}
            placeholder="Select range..."
          />
        </div>

        {/* Auto Refresh Dropdown */}
        <div className="hidden md:flex items-center gap-2">
          <button
            onClick={handleRefreshClick}
            className="p-2 rounded-xl border border-[hsl(var(--input))] bg-[hsl(var(--card))] text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] transition-transform cursor-pointer shadow-xs"
            title="Refresh now"
          >
            <RefreshCw size={14} className={isRefreshing ? 'animate-spin text-purple-400' : ''} />
          </button>
          <div className="w-44">
            <SearchableDropdown
              items={REFRESH_RATE_OPTIONS}
              value={refreshRate}
              onChange={setRefreshRate}
              placeholder="Refresh rate..."
            />
          </div>
        </div>
      </div>
    </header>
  );
}
