'use client';

import React, { useEffect, useState, useContext } from 'react';
import { Moon, Sun, Contrast, Monitor } from 'lucide-react';
import { ThemeContext, type Theme } from '../../theme/ThemeProvider';

export type ThemeMode = 'dark' | 'light' | 'high-contrast';

export function ThemeSwitcher() {
  const context = useContext(ThemeContext);
  const [localTheme, setLocalTheme] = useState<ThemeMode>('dark');

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const stored = (localStorage.getItem('observability-theme') || localStorage.getItem('theme')) as ThemeMode;
    if (stored && ['dark', 'light', 'high-contrast'].includes(stored)) {
      setLocalTheme(stored);
      applyThemeToDOM(stored);
    }
  }, []);

  const applyThemeToDOM = (mode: ThemeMode) => {
    if (typeof document === 'undefined') return;
    const root = document.documentElement;
    root.classList.remove('dark', 'light', 'high-contrast');
    if (mode === 'high-contrast') {
      root.classList.add('dark', 'high-contrast');
    } else {
      root.classList.add(mode);
    }
    try {
      localStorage.setItem('observability-theme', mode);
      localStorage.setItem('theme', mode);
    } catch {}
  };

  const handleSelect = (mode: ThemeMode) => {
    setLocalTheme(mode);
    if (context?.setTheme) {
      context.setTheme(mode as Theme);
    }
    applyThemeToDOM(mode);
  };

  const activeTheme = context?.theme || localTheme;

  return (
    <div className="rounded-[var(--radius-lg)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 space-y-3 text-left shadow-sm">
      <div>
        <h3 className="text-sm font-bold text-[hsl(var(--foreground))] flex items-center gap-2">
          <Monitor size={16} className="text-[hsl(var(--primary))]" />
          Appearance & Visual Theme
        </h3>
        <p className="text-xs text-[hsl(var(--muted-foreground))] mt-0.5">
          Select your color scheme preference and workspace contrast. Preserved automatically across refreshes.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-3 pt-1">
        <button
          type="button"
          onClick={() => handleSelect('dark')}
          className={`flex flex-col items-center justify-center p-3 rounded-[var(--radius-md)] border text-xs font-semibold transition-all cursor-pointer ${
            activeTheme === 'dark'
              ? 'border-purple-500 dark:bg-purple-950/40 bg-purple-100/90 dark:text-purple-200 text-purple-950 shadow-md ring-2 ring-purple-500/50'
              : 'border-[hsl(var(--border))] bg-[hsl(var(--background))] text-[hsl(var(--muted-foreground))] hover:border-[hsl(var(--ring))]'
          }`}
        >
          <Moon size={18} className="mb-1.5 text-purple-600 dark:text-purple-400" />
          <span>Dark Mode</span>
        </button>

        <button
          type="button"
          onClick={() => handleSelect('light')}
          className={`flex flex-col items-center justify-center p-3 rounded-[var(--radius-md)] border text-xs font-semibold transition-all cursor-pointer ${
            activeTheme === 'light'
              ? 'border-indigo-500 dark:bg-indigo-950/40 bg-indigo-100/90 dark:text-indigo-200 text-indigo-950 shadow-md ring-2 ring-indigo-500/50'
              : 'border-[hsl(var(--border))] bg-[hsl(var(--background))] text-[hsl(var(--muted-foreground))] hover:border-[hsl(var(--ring))]'
          }`}
        >
          <Sun size={18} className="mb-1.5 text-amber-600 dark:text-amber-400" />
          <span>Light Mode</span>
        </button>

        <button
          type="button"
          onClick={() => handleSelect('high-contrast')}
          className={`flex flex-col items-center justify-center p-3 rounded-[var(--radius-md)] border text-xs font-semibold transition-all cursor-pointer ${
            activeTheme === 'high-contrast'
              ? 'border-cyan-500 dark:bg-cyan-950/40 bg-cyan-100/90 dark:text-cyan-200 text-cyan-950 shadow-md ring-2 ring-cyan-500/50'
              : 'border-[hsl(var(--border))] bg-[hsl(var(--background))] text-[hsl(var(--muted-foreground))] hover:border-[hsl(var(--ring))]'
          }`}
        >
          <Contrast size={18} className="mb-1.5 text-cyan-600 dark:text-cyan-400" />
          <span>High Contrast</span>
        </button>
      </div>
    </div>
  );
}
