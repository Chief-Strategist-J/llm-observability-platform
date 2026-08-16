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

function parseSliderChange<T extends FieldValues>(
  e: React.ChangeEvent<HTMLInputElement>,
  name: FieldPath<T>,
  setValue: (name: FieldPath<T>, value: never, options?: { shouldValidate?: boolean }) => void
) {
  const parsed = parseFloat(e.target.value);
  if (!Number.isNaN(parsed)) {
    setValue(name, parsed as never, { shouldValidate: true });
  }
}

function SliderHeader({ label, name, numValue, unit }: { readonly label: string; readonly name: string; readonly numValue: number; readonly unit: string }) {
  const formattedValue = unit.length > 0 ? `${numValue} ${unit}` : `${numValue}`;
  return (
    <div className="flex items-center justify-between">
      <label htmlFor={name} className="text-sm font-medium text-[hsl(var(--foreground))]">
        {label}
      </label>
      <span className="text-sm font-semibold text-[hsl(var(--foreground))]">
        {formattedValue}
      </span>
    </div>
  );
}

function SliderFooter({ min, max, unit }: { readonly min: number; readonly max: number; readonly unit: string }) {
  const minText = unit.length > 0 ? `${min} ${unit}` : `${min}`;
  const maxText = unit.length > 0 ? `${max} ${unit}` : `${max}`;
  return (
    <div className="flex justify-between text-xs text-[hsl(var(--muted-foreground))]">
      <span>{minText}</span>
      <span>{maxText}</span>
    </div>
  );
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
      parseSliderChange(e, name, setValue as never);
    },
    [name, setValue]
  );

  const hasError = error !== undefined;
  const errorId = hasError ? `${name}-error` : undefined;

  return (
    <div className={cn('flex flex-col gap-2', className)}>
      <SliderHeader label={label} name={name} numValue={numValue} unit={unit} />
      <div className="relative">
        <input
          id={name}
          type="range"
          min={min}
          max={max}
          step={step}
          aria-invalid={hasError}
          aria-describedby={errorId}
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
      <SliderFooter min={min} max={max} unit={unit} />
      {hasError && (
        <p id={errorId} className="text-xs text-[hsl(var(--severity-bad))]" role="alert">
          {String(error.message ?? 'Invalid value')}
        </p>
      )}
    </div>
  );
}
