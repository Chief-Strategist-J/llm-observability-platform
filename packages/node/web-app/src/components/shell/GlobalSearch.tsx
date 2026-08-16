'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Search, LayoutDashboard, Key, Users, Building2, Settings, Command } from 'lucide-react';

interface SearchItem {
  readonly title: string;
  readonly category: string;
  readonly href: string;
  readonly icon: React.ComponentType<{ size?: number }>;
}

const SEARCH_ITEMS: readonly SearchItem[] = [
  { title: 'Overview Dashboard', category: 'Dashboards', href: '/', icon: LayoutDashboard },
  { title: 'Cost Analytics', category: 'Dashboards', href: '/costs', icon: LayoutDashboard },
  { title: 'Latency Metrics', category: 'Dashboards', href: '/latency', icon: LayoutDashboard },
  { title: 'API Keys Management', category: 'Access & Security', href: '/settings/api-keys', icon: Key },
  { title: 'Member Management', category: 'Access & Security', href: '/settings/members', icon: Users },
  { title: 'Organization Admin', category: 'Access & Security', href: '/admin/organizations', icon: Building2 },
  { title: 'Org Settings', category: 'Access & Security', href: '/settings/org', icon: Settings },
];

export function GlobalSearch() {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      }
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  const filtered = query.trim()
    ? SEARCH_ITEMS.filter(
        (item) =>
          item.title.toLowerCase().includes(query.toLowerCase()) ||
          item.category.toLowerCase().includes(query.toLowerCase())
      )
    : SEARCH_ITEMS;

  const handleSelect = (href: string) => {
    router.push(href);
    setIsOpen(false);
    setQuery('');
  };

  return (
    <>
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="flex items-center justify-between w-full px-3 py-1.5 text-xs text-[hsl(var(--muted-foreground))] bg-[hsl(var(--background))] border border-[hsl(var(--border))] rounded-[var(--radius-md)] hover:bg-[hsl(var(--accent)/0.5)] transition-all cursor-pointer mb-3"
      >
        <span className="flex items-center gap-2">
          <Search size={14} className="text-[hsl(var(--muted-foreground))]" />
          <span>Search platform...</span>
        </span>
        <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-mono font-bold bg-[hsl(var(--muted))] border border-[hsl(var(--border))] rounded text-[hsl(var(--muted-foreground))]">
          <Command size={10} />K
        </kbd>
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-150">
          <div className="w-full max-w-xl rounded-[var(--radius-xl)] bg-[hsl(var(--card))] border border-[hsl(var(--border))] shadow-2xl overflow-hidden text-left">
            <div className="flex items-center px-4 border-b border-[hsl(var(--border))] bg-[hsl(var(--background))]">
              <Search size={18} className="text-[hsl(var(--muted-foreground))] mr-3" />
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Type a command or search page..."
                className="w-full py-3 text-sm bg-transparent text-[hsl(var(--foreground))] outline-none placeholder:[hsl(var(--muted-foreground))]"
              />
              <button
                onClick={() => setIsOpen(false)}
                className="text-xs text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] px-2 py-1"
              >
                ESC
              </button>
            </div>

            <div className="max-h-80 overflow-y-auto p-2">
              {filtered.length > 0 ? (
                filtered.map((item) => {
                  const Icon = item.icon;
                  return (
                    <button
                      key={item.href + item.title}
                      onClick={() => handleSelect(item.href)}
                      className="w-full flex items-center justify-between px-3 py-2.5 rounded-[var(--radius-md)] text-xs text-left hover:bg-gradient-to-r hover:from-purple-900/30 hover:to-indigo-900/20 text-[hsl(var(--foreground))] transition-all group cursor-pointer"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-1.5 rounded-md bg-[hsl(var(--primary)/0.1)] text-[hsl(var(--primary))] group-hover:bg-[hsl(var(--primary)/0.2)]">
                          <Icon size={16} />
                        </div>
                        <div>
                          <div className="font-bold">{item.title}</div>
                          <div className="text-[10px] text-[hsl(var(--muted-foreground))]">{item.category}</div>
                        </div>
                      </div>
                      <span className="text-[10px] font-mono text-[hsl(var(--muted-foreground))] group-hover:text-[hsl(var(--primary))]">
                        Jump to →
                      </span>
                    </button>
                  );
                })
              ) : (
                <div className="p-6 text-center text-xs text-[hsl(var(--muted-foreground))]">
                  No matching platform commands found.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
