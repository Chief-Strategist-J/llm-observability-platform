import { describe, it, expect } from 'vitest';
import { executeFilterPipeline, buildFilterListOps, foldQueryParams, checkHasActiveFilters } from '../../src/hooks/filter-pipeline.engine';
import { encodeFilters, decodeFilters } from '../../src/lib/utils/url-state';
import { transformList } from '../../src/core/data-driven/list-transform';
import { FIXTURE_SPANS } from '../../src/lib/fixtures/fixtures';

describe('Filter Pipeline Engine & List Transform Integration Suite', () => {
  it('should end-to-end decode URL parameters, execute filter pipeline, and filter dataset via listTransform ops', () => {
    const rawQuery = 'model=gpt-4o&env=production';
    const filterState = decodeFilters(rawQuery);
    expect(filterState.model).toBe('gpt-4o');

    const searchParams = new URLSearchParams(rawQuery);
    const { filters, trace } = executeFilterPipeline(searchParams);
    expect(filters.model).toBe('gpt-4o');
    expect(trace.traceId).toBeDefined();

    const ops = buildFilterListOps(filters);
    const filteredSpans = transformList([...FIXTURE_SPANS] as any[], ops);

    expect(filteredSpans.length).toBeGreaterThan(0);
    filteredSpans.forEach((span: any) => {
      expect(span.model).toBe('gpt-4o');
    });
  });
});
