'use client';

import React, { useState } from 'react';
import { Clock, RefreshCw, Layers } from 'lucide-react';

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
        <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-950/60 dark:bg-emerald-950/60 bg-emerald-100 text-emerald-700 dark:text-emerald-300 border border-emerald-500/50 font-bold text-[11px] shrink-0">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span>Live Ingestion Engine</span>
        </div>

        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-[var(--radius-md)] bg-[hsl(var(--background))] border border-[hsl(var(--border))] text-[hsl(var(--muted-foreground))]">
          <Layers size={13} className="text-purple-400" />
          <select
            value={environment}
            onChange={(e) => setEnvironment(e.target.value)}
            className="bg-transparent text-[hsl(var(--foreground))] font-semibold outline-none cursor-pointer text-xs"
          >
            <option value="prod-us-east">Production (us-east-1)</option>
            <option value="prod-eu-west">Production (eu-west-1)</option>
            <option value="staging">Staging Sandbox</option>
          </select>
        </div>
      </div>

      {/* Right: Time Range, Refresh & Controls */}
      <div className="flex items-center gap-3">
        {/* Time Range Selector */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-[var(--radius-md)] bg-[hsl(var(--background))] border border-[hsl(var(--border))] text-[hsl(var(--foreground))] font-medium">
          <Clock size={13} className="text-[hsl(var(--primary))]" />
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="bg-transparent outline-none cursor-pointer text-xs font-semibold"
          >
            <option value="15m">Last 15 minutes</option>
            <option value="1h">Last 1 hour</option>
            <option value="6h">Last 6 hours</option>
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
          </select>
        </div>

        {/* Auto Refresh Dropdown */}
        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-[var(--radius-md)] bg-[hsl(var(--background))] border border-[hsl(var(--border))]">
          <button
            onClick={handleRefreshClick}
            className="p-0.5 text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] transition-transform cursor-pointer"
            title="Refresh now"
          >
            <RefreshCw size={13} className={isRefreshing ? 'animate-spin text-purple-400' : ''} />
          </button>
          <select
            value={refreshRate}
            onChange={(e) => setRefreshRate(e.target.value)}
            className="bg-transparent text-[hsl(var(--foreground))] outline-none cursor-pointer text-xs font-semibold"
          >
            <option value="off">Off</option>
            <option value="5s">Every 5s</option>
            <option value="10s">Every 10s</option>
            <option value="30s">Every 30s</option>
          </select>
        </div>
      </div>
    </header>
  );
}
