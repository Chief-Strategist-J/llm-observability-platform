'use client';

import React, { createContext, useCallback, useContext, useState } from 'react';
import {
  ToastProvider,
  ToastViewport,
  Toast,
  ToastTitle,
  ToastDescription,
  ToastClose,
} from '../primitives/Toast';
import { CheckCircle2, AlertTriangle, XCircle, Info } from 'lucide-react';

type NotificationType = 'info' | 'success' | 'warning' | 'error';

interface ToastItem {
  readonly id: string;
  readonly title: string;
  readonly description?: string;
  readonly type: NotificationType;
}

interface NotificationContextValue {
  readonly notify: (title: string, description?: string, type?: NotificationType) => void;
}

const NotificationContext = createContext<NotificationContextValue | undefined>(undefined);

const ICON_MAP: Record<NotificationType, React.ComponentType<{ size: number }>> = {
  info: Info,
  success: CheckCircle2,
  warning: AlertTriangle,
  error: XCircle,
} as const;

const VARIANT_MAP: Record<NotificationType, 'default' | 'success' | 'warning' | 'error'> = {
  info: 'default',
  success: 'success',
  warning: 'warning',
  error: 'error',
} as const;

/**
 * F-12: Notification/Toast system.
 * Single useNotify() hook. Mutations and WS errors both funnel through it.
 */
export function NotificationProvider({ children }: { readonly children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const notify = useCallback(
    (title: string, description?: string, type: NotificationType = 'info') => {
      const id = `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
      setToasts((prev) => [...prev, { id, title, description, type }]);
    },
    []
  );

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <NotificationContext.Provider value={{ notify }}>
      <ToastProvider swipeDirection="right">
        {children}

        {toasts.map((toast) => {
          const IconComponent = ICON_MAP[toast.type];
          return (
            <Toast
              key={toast.id}
              variant={VARIANT_MAP[toast.type]}
              onOpenChange={(open) => {
                if (!open) {
                  removeToast(toast.id);
                }
              }}
            >
              <div className="flex-shrink-0 pt-0.5">
                <IconComponent size={20} />
              </div>
              <div className="flex-grow">
                <ToastTitle>{toast.title}</ToastTitle>
                {toast.description !== undefined && (
                  <ToastDescription>{toast.description}</ToastDescription>
                )}
              </div>
              <ToastClose />
            </Toast>
          );
        })}

        <ToastViewport />
      </ToastProvider>
    </NotificationContext.Provider>
  );
}

/**
 * Hook to trigger toast notifications from anywhere in the component tree.
 * Must be used within a NotificationProvider.
 */
export function useNotify(): NotificationContextValue {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotify must be used within a NotificationProvider');
  }
  return context;
}
