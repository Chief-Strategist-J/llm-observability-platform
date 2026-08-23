'use client';

import { useMemo, useCallback } from 'react';
import { useRouter, usePathname, useSearchParams } from 'next/navigation';
import type { ListOp } from '../core/data-driven/transform.types';
import {
  DEFAULT_DASHBOARD_FILTERS,
  type DashboardFilters,
  type TimeRangeOption,
} from './filter-pipeline.rules';
import {
  executeFilterPipeline,
  buildFilterListOps,
  foldQueryParams,
  checkHasActiveFilters,
} from './filter-pipeline.engine';

export { DEFAULT_DASHBOARD_FILTERS };
export type { DashboardFilters, TimeRangeOption };

export function useDashboardFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const filters = useMemo(() => executeFilterPipeline(searchParams), [searchParams]);
  const listOps = useMemo(() => buildFilterListOps(filters), [filters]);
  const hasActiveFilters = useMemo(() => checkHasActiveFilters(filters), [filters]);

  const updateQueryParams = useCallback((newParams: Record<string, string | null | undefined>) => {
    const updated = foldQueryParams(searchParams, newParams);
    const query = updated.toString();
    router.push(`${pathname}${query ? `?${query}` : ''}`, { scroll: false });
  }, [pathname, router, searchParams]);

  const setFilter = useCallback((key: keyof DashboardFilters, value: string | null) => {
    updateQueryParams({ [key]: value });
  }, [updateQueryParams]);

  const setFilters = useCallback((patch: Partial<DashboardFilters>) => {
    updateQueryParams(patch as Record<string, string | null | undefined>);
  }, [updateQueryParams]);

  const resetFilters = useCallback(() => {
    router.push(pathname, { scroll: false });
  }, [pathname, router]);

  return { filters, listOps, setFilter, setFilters, resetFilters, hasActiveFilters };
}
