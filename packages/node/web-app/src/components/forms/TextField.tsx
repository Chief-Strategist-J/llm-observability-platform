'use client';

import React from 'react';
import { useFormContext, type FieldPath, type FieldValues } from 'react-hook-form';
import { Input } from '../primitives/Input';
import { cn } from '../../lib/utils/cn';

interface TextFieldProps<T extends FieldValues> {
  readonly name: FieldPath<T>;
  readonly label: string;
  readonly placeholder?: string;
  readonly className?: string;
}

/**
 * F-11: TextField.
 * Wired to React Hook Form context. Displays validation errors from Zod resolver.
 */
export function TextField<T extends FieldValues>({
  name,
  label,
  placeholder,
  className,
}: TextFieldProps<T>) {
  const { register, formState: { errors } } = useFormContext<T>();
  const error = errors[name];

  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      <label htmlFor={name} className="text-sm font-medium text-[hsl(var(--foreground))]">
        {label}
      </label>
      <Input
        id={name}
        placeholder={placeholder}
        aria-invalid={error !== undefined}
        aria-describedby={error !== undefined ? `${name}-error` : undefined}
        {...register(name)}
      />
      {error !== undefined && (
        <p id={`${name}-error`} className="text-xs text-[hsl(var(--severity-bad))]" role="alert">
          {String(error.message ?? 'Invalid value')}
        </p>
      )}
    </div>
  );
}
