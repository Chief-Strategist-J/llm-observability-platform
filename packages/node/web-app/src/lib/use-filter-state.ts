'use client';

import { useMemo, useCallback } from 'react';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import type { FilterState } from '@observability/api-types';
import { encodeFilters, decodeFilters } from './url-state';

export function useFilterState(): readonly [FilterState, (newFilters: FilterState) => void] {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const filters = useMemo(() => {
    return decodeFilters(searchParams);
  }, [searchParams]);

  const setFilters = useCallback(
    (newFilters: FilterState) => {
      const queryString = encodeFilters(newFilters);
      const target = queryString ? `${pathname}?${queryString}` : pathname;
      router.push(target);
    },
    [pathname, router]
  );

  return [filters, setFilters] as const;
}
