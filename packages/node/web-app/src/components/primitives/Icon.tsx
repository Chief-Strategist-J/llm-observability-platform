'use client';

import React from 'react';
import { icons, type LucideIcon } from 'lucide-react';
import { cn } from '../../lib/utils/cn';

/** All valid icon names from the lucide-react set. */
export type IconName = keyof typeof icons;

interface IconProps {
  /** Icon name — must be a valid lucide-react icon key. */
  readonly name: IconName;
  /** Pixel size (width and height). */
  readonly size?: number;
  /** Additional class names. */
  readonly className?: string;
  /** Accessible label — when omitted, icon is decorative (aria-hidden). */
  readonly label?: string;
}

/**
 * F-10: Iconography.
 * Single icon set (lucide-react) wrapped in a typed component.
 * Prevents ad hoc icon imports scattered through the app.
 */
export function Icon({ name, size = 16, className, label }: IconProps) {
  const LucideComponent: LucideIcon | undefined = icons[name];

  if (LucideComponent === undefined) {
    if (process.env.NODE_ENV !== 'production') {
      console.warn(`[Icon] Unknown icon name: "${name}"`);
    }
    return null;
  }

  return (
    <LucideComponent
      size={size}
      className={cn(className)}
      aria-hidden={label === undefined ? 'true' : undefined}
      aria-label={label}
      role={label !== undefined ? 'img' : undefined}
    />
  );
}
