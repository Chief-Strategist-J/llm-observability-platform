import { describe, it, expect } from 'vitest';
import { DEFAULT_DASHBOARD_FILTERS, type DashboardFilters } from '../filter-pipeline.rules';
import { executeFilterPipeline, buildFilterListOps, foldQueryParams, checkHasActiveFilters } from '../filter-pipeline.engine';

describe('Data-Driven Filter Pipeline Engine Unit Tests (F-11)', () => {
  it('should return default filters when search params are empty', () => {
    const params = new URLSearchParams('');
    const filters = executeFilterPipeline(params);
    expect(filters).toEqual(DEFAULT_DASHBOARD_FILTERS);
  });

  it('should execute pipeline over valid search params', () => {
    const params = new URLSearchParams('timeRange=7d&model=gpt-4o&service=checkout-service&environment=production');
    const filters = executeFilterPipeline(params);

    expect(filters.timeRange).toBe('7d');
    expect(filters.model).toBe('gpt-4o');
    expect(filters.service).toBe('checkout-service');
    expect(filters.environment).toBe('production');
  });

  it('should fall back to default timeRange when invalid value is provided in pipeline', () => {
    const params = new URLSearchParams('timeRange=invalid_range');
    const filters = executeFilterPipeline(params);

    expect(filters.timeRange).toBe('24h');
  });

  it('should build data-driven ListOp filter steps from dashboard filter state', () => {
    const filters: DashboardFilters = {
      timeRange: '7d',
      model: 'gpt-4o',
      service: 'checkout-service',
      environment: 'production',
    };

    const ops = buildFilterListOps(filters);
    expect(ops).toEqual([
      { op: 'filter', field: 'model', value: 'gpt-4o', cmp: 'eq' },
      { op: 'filter', field: 'service', value: 'checkout-service', cmp: 'eq' },
      { op: 'filter', field: 'environment', value: 'production', cmp: 'eq' },
    ]);
  });

  it('should fold new params into URLSearchParams without mutating defaults', () => {
    const current = new URLSearchParams('timeRange=7d');
    const updated = foldQueryParams(current, { model: 'gpt-4o' });
    expect(updated.toString()).toContain('model=gpt-4o');
  });

  it('should detect active filters correctly', () => {
    expect(checkHasActiveFilters(DEFAULT_DASHBOARD_FILTERS)).toBe(false);
    expect(checkHasActiveFilters({ ...DEFAULT_DASHBOARD_FILTERS, timeRange: '7d' })).toBe(true);
  });
});
