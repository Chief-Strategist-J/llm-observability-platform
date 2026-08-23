import type { ListOp } from '../core/data-driven/transform.types';
import {
  FILTER_PIPELINE_RULES,
  DEFAULT_DASHBOARD_FILTERS,
  type DashboardFilters,
  type FilterRuleConfig,
} from './filter-pipeline.rules';

export function processFilterRule(rule: FilterRuleConfig, searchParams: URLSearchParams): unknown {
  const raw = searchParams.get(rule.key);
  const trimmed = typeof raw === 'string' ? raw.trim() : '';

  if (!trimmed) {
    return rule.defaultValue;
  }

  if (rule.allowedValues) {
    return rule.allowedValues.has(trimmed) ? trimmed : rule.defaultValue;
  }

  if (rule.isDate) {
    return !isNaN(Date.parse(trimmed)) ? new Date(trimmed).toISOString() : rule.defaultValue;
  }

  return trimmed;
}

export function executeFilterPipeline(searchParams: URLSearchParams): DashboardFilters {
  return FILTER_PIPELINE_RULES.reduce<Record<string, unknown>>(
    (acc, rule) => ({
      ...acc,
      [rule.key]: processFilterRule(rule, searchParams),
    }),
    {}
  ) as unknown as DashboardFilters;
}

export function buildFilterListOps(filters: DashboardFilters): ListOp[] {
  const filterKeys: Array<keyof DashboardFilters> = ['model', 'service', 'environment'];

  return filterKeys
    .map((key) => ({ key, value: filters[key] }))
    .filter((item) => Boolean(item.value) && item.value !== 'all')
    .map((item) => ({
      op: 'filter' as const,
      field: item.key,
      value: item.value,
      cmp: 'eq' as const,
    }));
}

export function foldQueryParams(
  searchParams: URLSearchParams,
  newParams: Record<string, string | null | undefined>
): URLSearchParams {
  return Object.entries(newParams).reduce((params, [key, val]) => {
    const isDefault = val === null || val === undefined || val === '' || val === DEFAULT_DASHBOARD_FILTERS[key as keyof DashboardFilters];
    if (isDefault) {
      params.delete(key);
    } else {
      params.set(key, String(val));
    }
    return params;
  }, new URLSearchParams(Array.from(searchParams.entries())));
}

export function checkHasActiveFilters(filters: DashboardFilters): boolean {
  return (
    filters.timeRange !== DEFAULT_DASHBOARD_FILTERS.timeRange ||
    Boolean(filters.from) ||
    Boolean(filters.to) ||
    Object.keys(DEFAULT_DASHBOARD_FILTERS)
      .filter((k) => k !== 'timeRange')
      .some((k) => filters[k as keyof DashboardFilters] !== DEFAULT_DASHBOARD_FILTERS[k as keyof DashboardFilters])
  );
}
