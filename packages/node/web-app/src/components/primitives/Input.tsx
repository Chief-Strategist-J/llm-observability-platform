import React from 'react';
import { cn } from '../../lib/cn';

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = 'text', ...props }, ref) => {
    return (
      <input
        ref={ref}
        type={type}
        className={cn(
          'flex h-9 w-full rounded-[var(--radius-md)] border border-[hsl(var(--input))] bg-[hsl(var(--card))] px-3 py-1 text-sm text-[hsl(var(--foreground))] shadow-sm transition-colors',
          'placeholder:text-[hsl(var(--muted-foreground))]',
          'focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[hsl(var(--ring))]',
          'disabled:cursor-not-allowed disabled:opacity-50',
          'file:border-0 file:bg-transparent file:text-sm file:font-medium',
          className
        )}
        {...props}
      />
    );
  }
);
Input.displayName = 'Input';
