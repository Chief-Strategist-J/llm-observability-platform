'use client';

import React, { createContext, useCallback, useEffect, useState } from 'react';

export type Theme = 'light' | 'dark' | 'high-contrast';

const VALID_THEMES: ReadonlySet<string> = new Set<Theme>(['light', 'dark', 'high-contrast']);
const STORAGE_KEY = 'observability-theme' as const;

interface ThemeContextValue {
  readonly theme: Theme;
  readonly setTheme: (theme: Theme) => void;
}

export const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

interface ThemeProviderProps {
  readonly children: React.ReactNode;
  readonly defaultTheme?: Theme;
}

export function ThemeProvider({ children, defaultTheme = 'dark' }: ThemeProviderProps) {
  const [theme, setThemeState] = useState<Theme>(defaultTheme);

  // Hydrate from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY) || localStorage.getItem('theme');
      if (stored !== null && VALID_THEMES.has(stored)) {
        setThemeState(stored as Theme);
        applyThemeToRoot(stored as Theme);
      }
    } catch {}
  }, []);

  const applyThemeToRoot = (targetTheme: Theme) => {
    const root = document.documentElement;
    root.classList.remove('light', 'dark', 'high-contrast');
    if (targetTheme === 'high-contrast') {
      root.classList.add('dark', 'high-contrast');
    } else {
      root.classList.add(targetTheme);
    }
  };

  // Apply theme class to <html> and persist
  useEffect(() => {
    applyThemeToRoot(theme);
  }, [theme]);

  const setTheme = useCallback((newTheme: Theme) => {
    if (!VALID_THEMES.has(newTheme)) {
      return;
    }
    setThemeState(newTheme);
    applyThemeToRoot(newTheme);
    try {
      localStorage.setItem(STORAGE_KEY, newTheme);
      localStorage.setItem('theme', newTheme);
    } catch {}
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
