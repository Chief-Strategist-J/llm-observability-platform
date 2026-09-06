import React from 'react';

export interface AttributeRenderContext {
  keyName: string;
  value: unknown;
}

export type AttributeMatcher = (keyName: string, value: unknown) => boolean;
export type AttributeRendererComponent = React.ComponentType<AttributeRenderContext>;

interface RegisteredEntry {
  name: string;
  matcher: AttributeMatcher;
  Component: AttributeRendererComponent;
  priority: number;
}

const registry: RegisteredEntry[] = [];

export function registerAttributeRenderer(
  name: string,
  matcher: AttributeMatcher,
  Component: AttributeRendererComponent,
  priority = 10
): void {
  const existingIdx = registry.findIndex((entry) => entry.name === name);
  if (existingIdx >= 0) {
    registry.splice(existingIdx, 1);
  }

  registry.push({ name, matcher, Component, priority });
  registry.sort((a, b) => b.priority - a.priority);
}

export function getAttributeRenderer(keyName: string, value: unknown): AttributeRendererComponent | null {
  for (const entry of registry) {
    try {
      if (entry.matcher(keyName, value)) {
        return entry.Component;
      }
    } catch {
      
    }
  }
  return null;
}

export function renderAttribute(keyName: string, value: unknown): React.ReactNode {
  const Component = getAttributeRenderer(keyName, value);
  if (!Component) {
    return React.createElement('span', { className: 'font-mono text-[hsl(var(--foreground))]' }, String(value ?? '-'));
  }
  return React.createElement(Component, { keyName, value });
}
