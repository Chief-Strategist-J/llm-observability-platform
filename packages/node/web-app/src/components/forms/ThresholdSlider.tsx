'use client';

import React, { useCallback } from 'react';
import { useFormContext, useWatch, type FieldPath, type FieldValues } from 'react-hook-form';
import { cn } from '../../lib/cn';

interface ThresholdSliderProps<T extends FieldValues> {
  readonly name: FieldPath<T>;
  readonly label: string;
  readonly min: number;
  readonly max: number;
  readonly step?: number;
  readonly unit?: string;
  readonly className?: string;
}

/**
 * F-11: ThresholdSlider.
 * Reused directly by Layer 4's SLO/budget editors.
 * Displays current value and maps the track position to severity colors
 * from design tokens.
 */
export function ThresholdSlider<T extends FieldValues>({
  name,
  label,
  min,
  max,
  step = 1,
  unit = '',
  className,
}: ThresholdSliderProps<T>) {
  const { register, setValue, formState: { errors } } = useFormContext<T>();
  const value = useWatch<T>({ name });
  const error = errors[name];

  const numValue = typeof value === 'number' ? value : min;
  const percentage = max > min ? ((numValue - min) / (max - min)) * 100 : 0;

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const parsed = parseFloat(e.target.value);
      if (!Number.isNaN(parsed)) {
        setValue(name, parsed as never, { shouldValidate: true });
      }
    },
    [name, setValue]
  );

  return (
    <div className={cn('flex flex-col gap-2', className)}>
      <div className="flex items-center justify-between">
        <label htmlFor={name} className="text-sm font-medium text-[hsl(var(--foreground))]">
          {label}
        </label>
        <span className="text-sm font-semibold text-[hsl(var(--foreground))]">
          {numValue}{unit !== '' ? ` ${unit}` : ''}
        </span>
      </div>
      <div className="relative">
        <input
          id={name}
          type="range"
          min={min}
          max={max}
          step={step}
          aria-invalid={error !== undefined}
          aria-describedby={error !== undefined ? `${name}-error` : undefined}
          aria-valuemin={min}
          aria-valuemax={max}
          aria-valuenow={numValue}
          className={cn(
            'h-2 w-full cursor-pointer appearance-none rounded-full bg-[hsl(var(--muted))]',
            '[&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-[hsl(var(--primary))] [&::-webkit-slider-thumb]:shadow-md',
            '[&::-moz-range-thumb]:h-4 [&::-moz-range-thumb]:w-4 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:border-0 [&::-moz-range-thumb]:bg-[hsl(var(--primary))] [&::-moz-range-thumb]:shadow-md'
          )}
          style={{
            background: `linear-gradient(to right, hsl(var(--primary)) 0%, hsl(var(--primary)) ${percentage}%, hsl(var(--muted)) ${percentage}%, hsl(var(--muted)) 100%)`,
          }}
          {...register(name, { valueAsNumber: true })}
          onChange={handleChange}
        />
      </div>
      <div className="flex justify-between text-xs text-[hsl(var(--muted-foreground))]">
        <span>{min}{unit !== '' ? ` ${unit}` : ''}</span>
        <span>{max}{unit !== '' ? ` ${unit}` : ''}</span>
      </div>
      {error !== undefined && (
        <p id={`${name}-error`} className="text-xs text-[hsl(var(--severity-bad))]" role="alert">
          {String(error.message ?? 'Invalid value')}
        </p>
      )}
    </div>
  );
}
