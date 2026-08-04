'use client';

import { useContext } from 'react';
import { ThemeContext } from './ThemeProvider';

/**
 * Hook to read and update the current theme.
 * Must be used inside a ThemeProvider.
 */
export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
