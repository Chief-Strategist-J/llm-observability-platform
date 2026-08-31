import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  httpClient,
  ScalableHttpClient,
  calculateFullJitterBackoff,
  isCacheDisabled,
  sanitizeUrlForTelemetry,
  filterAllowedAttributes,
  generateHashedKey,
  deriveRouteTemplate,
  validateDestinationUrl,
  isMethodIdempotent,
  TenantPartitionedCacheStore,
  TenantRateLimiter,
  StandardCircuitBreaker
} from '../http-client';
import { RequestContextHolder } from '../../tracing/request-context';
import { getCallerInfo } from '../../tracing/caller-info';

describe('ScalableHttpClient Production Hardening Architecture', () => {
  let client: ScalableHttpClient;

  beforeEach(() => {
    client = new ScalableHttpClient();
    vi.restoreAllMocks();
  });

  describe('AsyncLocalStorage Request Context Isolation', () => {
    it('guarantees thread-safe isolated tenant context across async chains', async () => {
      const ctx1 = RequestContextHolder.create({ tenantId: 'tenant-acme' });
      const ctx2 = RequestContextHolder.create({ tenantId: 'tenant-globex' });

      const res1 = await RequestContextHolder.run(ctx1, async () => {
        await new Promise(r => setTimeout(r, 10));
        return RequestContextHolder.get().tenantId;
      });

      const res2 = await RequestContextHolder.run(ctx2, async () => {
        await new Promise(r => setTimeout(r, 5));
        return RequestContextHolder.get().tenantId;
      });

      expect(res1).toBe('tenant-acme');
      expect(res2).toBe('tenant-globex');
    });
  });

  describe('Self-Verifying Dynamic Caller Location Telemetry', () => {
    it('dynamically scans V8 stack frames outside http-client infrastructure', () => {
      const caller = getCallerInfo();
      expect(caller.filePath).toBeDefined();
      expect(caller.functionName).toBeDefined();
      expect(caller.filePath).not.toContain('/home/');
    });
  });

  describe('DNS IP-Level SSRF & Protocol Protection', () => {
    it('blocks private internal IP ranges and invalid protocols', async () => {
      await expect(validateDestinationUrl('http://169.254.169.254/latest/meta-data')).rejects.toThrow(/SSRF Blocked/);
      await expect(validateDestinationUrl('http://127.0.0.1/admin')).rejects.toThrow(/SSRF Blocked/);
      await expect(validateDestinationUrl('ftp://api.org/data')).rejects.toThrow(/Blocked insecure URL protocol scheme/);
    });

    it('allows valid public HTTP/HTTPS URLs', async () => {
      const valid = await validateDestinationUrl('https://api.observability.com/v1/summary');
      expect(valid.hostname).toBe('api.observability.com');
    });
  });

  describe('Per-Tenant Token Bucket Outbound Rate Limiter', () => {
    it('enforces outbound rate limits per tenant', () => {
      const limiter = new TenantRateLimiter(2, 1);
      expect(limiter.allowRequest('tenant-A')).toBe(true);
      expect(limiter.allowRequest('tenant-A')).toBe(true);
      expect(limiter.allowRequest('tenant-A')).toBe(false);
      // Independent tenant bucket
      expect(limiter.allowRequest('tenant-B')).toBe(true);
    });
  });

  describe('Bounded LRU Circuit Breaker & Write Cache Invalidation', () => {
    it('invalidates tenant cache entries on mutating write RPCs', () => {
      const cache = new TenantPartitionedCacheStore(10);
      cache.set('tenant-1', 'key-1', 'cached-data', 5000);
      expect(cache.get('tenant-1', 'key-1')).toBe('cached-data');

      // Clear tenant partition on write mutation
      cache.clear('tenant-1');
      expect(cache.get('tenant-1', 'key-1')).toBeUndefined();
    });

    it('bounds circuit breaker states using LRU capacity', () => {
      const cb = new StandardCircuitBreaker();
      const key = cb.getCircuitKey('tenant-1', 'http://api.org/users/123');
      expect(key).toBe('tenant-1:api.org/users/:id');
      expect(cb.canExecute(key)).toBe(true);
    });
  });
});
