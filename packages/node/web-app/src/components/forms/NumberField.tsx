'use client';

import React from 'react';
import { useFormContext, type FieldPath, type FieldValues } from 'react-hook-form';
import { cn } from '../../lib/utils/cn';

type UnitSuffix = '$' | 'ms' | 'tokens' | '%' | string;

interface NumberFieldProps<T extends FieldValues> {
  readonly name: FieldPath<T>;
  readonly label: string;
  readonly unit: UnitSuffix;
  readonly placeholder?: string;
  readonly min?: number;
  readonly max?: number;
  readonly step?: number;
  readonly className?: string;
}

/**
 * F-11: NumberField with unit suffix ($ or ms).
 * Wired to React Hook Form context. Reused by Layer 4's SLO/budget editors.
 */
export function NumberField<T extends FieldValues>({
  name,
  label,
  unit,
  placeholder,
  min,
  max,
  step,
  className,
}: NumberFieldProps<T>) {
  const { register, formState: { errors } } = useFormContext<T>();
  const error = errors[name];

  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      <label htmlFor={name} className="text-sm font-medium text-[hsl(var(--foreground))]">
        {label}
      </label>
      <div className="relative">
        <input
          id={name}
          type="number"
          placeholder={placeholder}
          min={min}
          max={max}
          step={step}
          aria-invalid={error !== undefined}
          aria-describedby={error !== undefined ? `${name}-error` : undefined}
          className={cn(
            'flex h-9 w-full rounded-[var(--radius-md)] border border-[hsl(var(--input))] bg-[hsl(var(--card))] px-3 py-1 pr-10 text-sm text-[hsl(var(--foreground))] shadow-sm transition-colors',
            'placeholder:text-[hsl(var(--muted-foreground))]',
            'focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[hsl(var(--ring))]',
            'disabled:cursor-not-allowed disabled:opacity-50',
            '[appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none'
          )}
          {...register(name, { valueAsNumber: true })}
        />
        <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-[hsl(var(--muted-foreground))]">
          {unit}
        </span>
      </div>
      {error !== undefined && (
        <p id={`${name}-error`} className="text-xs text-[hsl(var(--severity-bad))]" role="alert">
          {String(error.message ?? 'Invalid value')}
        </p>
      )}
    </div>
  );
}
