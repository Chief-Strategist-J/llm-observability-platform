'use client';

import React, { useMemo } from 'react';
import { Provider } from 'react-redux';
import { createApplicationStore } from '@observability/core';
import { ThemeProvider } from '../theme/ThemeProvider';
import { NotificationProvider } from '../components/primitives/NotificationProvider';

export function Providers({ children }: { readonly children: React.ReactNode }) {
  const store = useMemo(() => createApplicationStore(), []);

  return (
    <Provider store={store}>
      <ThemeProvider defaultTheme="dark">
        <NotificationProvider>
          {children}
        </NotificationProvider>
      </ThemeProvider>
    </Provider>
  );
}
