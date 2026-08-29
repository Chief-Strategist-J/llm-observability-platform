import { test, expect } from '@playwright/test';
import { executeFilterPipeline } from '../../../../src/hooks/filter-pipeline.engine';

test.describe('Dashboard Filters - Selection & Pipeline Automation', () => {
  test('should execute filter pipeline over search params', async () => {
    const params = new URLSearchParams('timeRange=7d&model=gpt-4o&environment=production');
    const { filters, trace } = executeFilterPipeline(params);

    expect(filters.timeRange).toBe('7d');
    expect(filters.model).toBe('gpt-4o');
    expect(filters.environment).toBe('production');
    expect(trace.traceId).toBeDefined();
  });
});
