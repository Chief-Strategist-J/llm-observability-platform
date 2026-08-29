import { describe, it, expect } from 'vitest';
import { encodeFilters, decodeFilters } from '../../../../src/lib/utils/url-state';
import type { FilterState } from '@observability/api-types';

describe('URL Filter State Codec Unit Tests (F-11 / TEST-FE2-05)', () => {
  it('encodes FilterState into URL query string', () => {
    const filters: FilterState = {
      dateRange: { from: '2026-08-01', to: '2026-08-07' },
      model: 'gpt-4o',
      service: 'payment-service',
      environment: 'production',
    };

    const query = encodeFilters(filters);
    expect(query).toContain('from=2026-08-01');
    expect(query).toContain('to=2026-08-07');
    expect(query).toContain('model=gpt-4o');
    expect(query).toContain('service=payment-service');
    expect(query).toContain('env=production');
  });

  it('decodes query string back into FilterState', () => {
    const query = 'from=2026-08-01&to=2026-08-07&model=claude-3-opus&env=staging';
    const filters = decodeFilters(query);

    expect(filters.dateRange).toEqual({ from: '2026-08-01', to: '2026-08-07' });
    expect(filters.model).toBe('claude-3-opus');
    expect(filters.environment).toBe('staging');
  });

  it('degrades gracefully on invalid/retired filter values (EC-FE2-03)', () => {
    const query = 'env=invalid-env-name';
    const filters = decodeFilters(query);

    expect(filters.environment).toBe('all');
  });
});
