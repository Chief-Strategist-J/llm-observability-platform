/**
 * Locale-sensitive number and currency formatters.
 * Uses Intl.NumberFormat exclusively — never hand-rolled string concatenation (EC-FE1-04).
 * Single source of truth for all number formatting in data-display components.
 */

const MICRODOLLARS_PER_USD = 1_000_000;

const compactFormatter = new Intl.NumberFormat(undefined, {
  notation: 'compact',
  maximumFractionDigits: 1,
});

const fullPrecisionFormatter = new Intl.NumberFormat(undefined, {
  maximumFractionDigits: 6,
  minimumFractionDigits: 2,
});

const msFormatter = new Intl.NumberFormat(undefined, {
  maximumFractionDigits: 1,
});

const tokenFormatter = new Intl.NumberFormat(undefined, {
  maximumFractionDigits: 0,
});

const percentFormatter = new Intl.NumberFormat(undefined, {
  style: 'percent',
  maximumFractionDigits: 1,
});

/**
 * Format cost from micro-USD to display string.
 * Returns both compact (for card display) and full precision (for tooltip).
 */
export function formatCostUsdMicro(microUsd: number): { compact: string; full: string } {
  const usd = microUsd / MICRODOLLARS_PER_USD;
  return {
    compact: `$${compactFormatter.format(usd)}`,
    full: `$${fullPrecisionFormatter.format(usd)}`,
  };
}

/** Format latency in milliseconds. */
export function formatLatencyMs(ms: number): string {
  return `${msFormatter.format(ms)} ms`;
}

/** Format token counts. */
export function formatTokens(count: number): string {
  return `${tokenFormatter.format(count)} tokens`;
}

/** Format a quality score (0–1) as a percentage. */
export function formatQualityScore(score: number): string {
  return percentFormatter.format(score);
}

/** Format a generic number compactly. */
export function formatCompact(value: number): string {
  return compactFormatter.format(value);
}
