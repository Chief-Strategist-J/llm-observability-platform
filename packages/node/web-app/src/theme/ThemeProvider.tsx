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

/**
 * F-09: Theme provider.
 * Light / dark / high-contrast via CSS variables on <html>.
 * No component-level conditionals — all theming flows through CSS custom properties
 * defined in design-tokens/dist/variables.css.
 */
export function ThemeProvider({ children, defaultTheme = 'dark' }: ThemeProviderProps) {
  const [theme, setThemeState] = useState<Theme>(defaultTheme);

  // Hydrate from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored !== null && VALID_THEMES.has(stored)) {
        setThemeState(stored as Theme);
      }
    } catch {
      // localStorage may be unavailable (e.g. SSR, incognito restrictions)
    }
  }, []);

  // Apply theme class to <html> and persist
  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove('light', 'dark', 'high-contrast');
    root.classList.add(theme);
  }, [theme]);

  const setTheme = useCallback((newTheme: Theme) => {
    if (!VALID_THEMES.has(newTheme)) {
      return;
    }
    setThemeState(newTheme);
    try {
      localStorage.setItem(STORAGE_KEY, newTheme);
    } catch {
      // Silently fail if localStorage is unavailable
    }
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
