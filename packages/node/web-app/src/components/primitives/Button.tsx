import React from 'react';
import { cn } from '../../lib/cn';

export type ButtonVariant = 'default' | 'secondary' | 'outline' | 'destructive' | 'ghost' | 'gradient' | 'gradient-glow';
export type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  readonly variant?: ButtonVariant;
  readonly size?: ButtonSize;
}

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  default: 'bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] hover:opacity-90',
  gradient: 'bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-500 text-white font-bold shadow-md hover:opacity-95 hover:shadow-lg hover:shadow-purple-500/20 active:scale-[0.98] transition-all',
  'gradient-glow': 'bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-500 text-white font-bold shadow-[0_0_20px_rgba(147,51,234,0.35)] hover:shadow-[0_0_25px_rgba(147,51,234,0.5)] active:scale-[0.98] transition-all',
  secondary: 'bg-[hsl(var(--secondary))] text-[hsl(var(--secondary-foreground))] border border-[hsl(var(--border))] hover:opacity-80',
  outline: 'border border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] hover:bg-[hsl(var(--muted)/.3)]',
  destructive: 'bg-[hsl(var(--destructive))] text-[hsl(var(--destructive-foreground))] hover:opacity-90',
  ghost: 'bg-transparent text-[hsl(var(--foreground))] hover:bg-[hsl(var(--muted)/.2)]',
} as const;

const SIZE_CLASSES: Record<ButtonSize, string> = {
  sm: 'px-3.5 py-1.5 min-h-[36px] text-xs',
  md: 'px-5 py-2.5 min-h-[44px] text-sm',
  lg: 'px-7 py-3 min-h-[48px] text-base',
} as const;

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'md', type = 'button', ...props }, ref) => {
    return (
      <button
        ref={ref}
        type={type}
        className={cn(
          'inline-flex cursor-pointer items-center justify-center rounded-full font-semibold transition-all focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))] disabled:pointer-events-none disabled:opacity-50',
          VARIANT_CLASSES[variant],
          SIZE_CLASSES[size],
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';
