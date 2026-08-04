'use client';

import React from 'react';
import * as ToastPrimitive from '@radix-ui/react-toast';
import { cn } from '../../lib/cn';
import { X } from 'lucide-react';

export const ToastProvider = ToastPrimitive.Provider;

export const ToastViewport = React.forwardRef<
  React.ComponentRef<typeof ToastPrimitive.Viewport>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitive.Viewport>
>(({ className, ...props }, ref) => (
  <ToastPrimitive.Viewport
    ref={ref}
    className={cn(
      'fixed bottom-4 right-4 z-[100] m-0 flex w-96 max-w-[100vw] list-none flex-col gap-2 p-0 outline-none',
      className
    )}
    {...props}
  />
));
ToastViewport.displayName = ToastPrimitive.Viewport.displayName;

export const Toast = React.forwardRef<
  React.ComponentRef<typeof ToastPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitive.Root> & {
    readonly variant?: 'default' | 'success' | 'warning' | 'error';
  }
>(({ className, variant = 'default', ...props }, ref) => {
  const variantClasses: Record<string, string> = {
    default: 'border-[hsl(var(--border))] bg-[hsl(var(--card))] text-[hsl(var(--card-foreground))]',
    success: 'border-[hsl(var(--severity-good)/.3)] bg-[hsl(var(--severity-good)/.1)] text-[hsl(var(--severity-good))]',
    warning: 'border-[hsl(var(--severity-warn)/.3)] bg-[hsl(var(--severity-warn)/.1)] text-[hsl(var(--severity-warn))]',
    error: 'border-[hsl(var(--severity-bad)/.3)] bg-[hsl(var(--severity-bad)/.1)] text-[hsl(var(--severity-bad))]',
  };

  return (
    <ToastPrimitive.Root
      ref={ref}
      className={cn(
        'group flex w-full gap-3 rounded-[var(--radius-lg)] border p-4 shadow-lg backdrop-blur-md transition-all',
        'data-[state=open]:animate-slide-in data-[state=closed]:animate-hide',
        variantClasses[variant],
        className
      )}
      {...props}
    />
  );
});
Toast.displayName = ToastPrimitive.Root.displayName;

export const ToastTitle = React.forwardRef<
  React.ComponentRef<typeof ToastPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitive.Title>
>(({ className, ...props }, ref) => (
  <ToastPrimitive.Title
    ref={ref}
    className={cn('text-sm font-semibold', className)}
    {...props}
  />
));
ToastTitle.displayName = ToastPrimitive.Title.displayName;

export const ToastDescription = React.forwardRef<
  React.ComponentRef<typeof ToastPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitive.Description>
>(({ className, ...props }, ref) => (
  <ToastPrimitive.Description
    ref={ref}
    className={cn('mt-1 text-xs opacity-90', className)}
    {...props}
  />
));
ToastDescription.displayName = ToastPrimitive.Description.displayName;

export const ToastClose = React.forwardRef<
  React.ComponentRef<typeof ToastPrimitive.Close>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitive.Close>
>(({ className, ...props }, ref) => (
  <ToastPrimitive.Close
    ref={ref}
    className={cn(
      'flex-shrink-0 cursor-pointer self-start p-1 opacity-70 transition-opacity hover:opacity-100',
      className
    )}
    {...props}
  >
    <X size={16} aria-hidden="true" />
    <span className="sr-only">Close</span>
  </ToastPrimitive.Close>
));
ToastClose.displayName = ToastPrimitive.Close.displayName;
