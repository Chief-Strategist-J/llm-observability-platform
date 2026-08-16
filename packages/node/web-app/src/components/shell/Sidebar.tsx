'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '../../lib/cn';
import { OrgSwitcher } from './OrgSwitcher';
import { UserMenu } from './UserMenu';
import {
  LayoutDashboard,
  DollarSign,
  Clock,
  Award,
  MessageSquareCode,
  Sliders,
  ShieldCheck,
  FileCode,
  Lock,
  Flag,
  Activity,
  Key,
  Building2,
  Users,
  Settings,
} from 'lucide-react';

interface NavItem {
  readonly label: string;
  readonly href: string;
  readonly icon: React.ComponentType<{ size?: number }>;
  readonly adminOnly?: boolean;
}

const NAV_GROUPS: readonly { title: string; items: readonly NavItem[] }[] = [
  {
    title: 'Dashboards',
    items: [
      { label: 'Overview', href: '/', icon: LayoutDashboard },
      { label: 'Costs', href: '/costs', icon: DollarSign },
      { label: 'Latency', href: '/latency', icon: Clock },
      { label: 'Quality', href: '/quality', icon: Award },
      { label: 'Prompts', href: '/prompts', icon: MessageSquareCode },
    ],
  },
  {
    title: 'Access & Security',
    items: [
      { label: 'API Keys', href: '/settings/api-keys', icon: Key },
      { label: 'Member Management', href: '/settings/members', icon: Users },
      { label: 'Organizations Admin', href: '/admin/organizations', icon: Building2, adminOnly: true },
      { label: 'Org Settings', href: '/settings/org', icon: Settings },
    ],
  },
  {
    title: 'Platform Administration',
    items: [
      { label: 'Budgets', href: '/admin/budgets', icon: Sliders, adminOnly: true },
      { label: 'SLO Thresholds', href: '/admin/slos', icon: ShieldCheck, adminOnly: true },
      { label: 'Templates', href: '/admin/templates', icon: FileCode, adminOnly: true },
      { label: 'Compliance', href: '/admin/compliance', icon: Lock, adminOnly: true },
      { label: 'Feature Flags', href: '/admin/feature-flags', icon: Flag, adminOnly: true },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();

  if (pathname.startsWith('/auth')) {
    return null;
  }

  return (
    <aside className="flex h-screen w-64 flex-col border-r border-[hsl(var(--border))] bg-[hsl(var(--card))] text-[hsl(var(--card-foreground))]">
      <div className="border-b border-[hsl(var(--border))] p-3">
        <div className="flex items-center gap-2 px-2 py-1">
          <Activity className="text-[hsl(var(--primary))]" size={20} />
          <span className="font-bold tracking-tight">Observability</span>
        </div>
        <div className="mt-2">
          <OrgSwitcher />
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto p-3">
        {NAV_GROUPS.map((group) => (
          <div key={group.title} className="mb-6">
            <h2 className="px-2 mb-2 text-[10px] font-bold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">
              {group.title}
            </h2>
            <div className="flex flex-col gap-1">
              {group.items.map((item) => {
                const isActive = item.href === '/' ? pathname === '/' : pathname.startsWith(item.href);
                const IconComponent = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      'flex items-center gap-2.5 rounded-[var(--radius-md)] px-3 py-2 text-xs font-semibold transition-colors',
                      isActive
                        ? 'bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]'
                        : 'text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--muted)/.5)] hover:text-[hsl(var(--foreground))]'
                    )}
                  >
                    <IconComponent size={16} />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="border-t border-[hsl(var(--border))] p-3">
        <UserMenu />
      </div>
    </aside>
  );
}
