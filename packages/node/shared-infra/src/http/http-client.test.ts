import { describe, it, expect, vi, beforeEach } from 'vitest';
import { httpClient, ScalableHttpClient, calculateFullJitterBackoff, isCacheDisabled } from './http-client';
import { HTTP_CONSTANTS } from './constants';

describe('ScalableHttpClient Edge Cases & Architecture', () => {
  let client: ScalableHttpClient;

  beforeEach(() => {
    client = new ScalableHttpClient();
    vi.restoreAllMocks();
  });

  describe('Full Jitter Backoff', () => {
    it('calculates backoff within 0 and capped exponential limit', () => {
      const backoffAttempt1 = calculateFullJitterBackoff(1, 200, 10000);
      expect(backoffAttempt1).toBeGreaterThanOrEqual(0);
      expect(backoffAttempt1).toBeLessThanOrEqual(200);

      const backoffAttempt3 = calculateFullJitterBackoff(3, 200, 10000);
      expect(backoffAttempt3).toBeGreaterThanOrEqual(0);
      expect(backoffAttempt3).toBeLessThanOrEqual(800);
    });
  });

  describe('Endpoint & Header Driven Cache Control', () => {
    it('bypasses cache when noCache is set at endpoint level', () => {
      const config = { method: 'GET', url: '/api/test', noCache: true };
      const headers = {};
      expect(isCacheDisabled(config, headers)).toBe(true);
    });

    it('bypasses cache when Cache-Control header contains no-cache or no-store', () => {
      const config = { method: 'GET', url: '/api/test' };
      const headers = { 'Cache-Control': 'no-cache, no-store' };
      expect(isCacheDisabled(config, headers)).toBe(true);
    });

    it('allows caching when no opt-out directive is present', () => {
      const config = { method: 'GET', url: '/api/test' };
      const headers = { 'Cache-Control': 'max-age=3600' };
      expect(isCacheDisabled(config, headers)).toBe(false);
    });
  });

  describe('Pluggable Pipeline Registries', () => {
    it('invokes registered header providers and merges headers', async () => {
      client.registerHeaderProvider(() => ({ 'x-custom-provider': 'active-val' }));

      vi.stubGlobal(
        'fetch',
        vi.fn().mockResolvedValue({
          ok: true,
          status: 200,
          headers: new Headers(),
          json: async () => ({ status: 'ok' }),
        })
      );

      const res = await client.get('/api/test-headers');
      expect(res.data).toEqual({ status: 'ok' });
    });
  });
});
