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
  TenantPartitionedCacheStore
} from '../http-client';
import { HTTP_CONSTANTS } from '../constants';

describe('ScalableHttpClient Hardened Security & Architecture', () => {
  let client: ScalableHttpClient;

  beforeEach(() => {
    client = new ScalableHttpClient();
    vi.restoreAllMocks();
  });

  describe('Telemetry URL Sanitization & Default-Deny Allowlist', () => {
    it('strips query parameters and userinfo credentials from URLs for telemetry', () => {
      const rawUrl = 'https://admin:secret123@api.observability.com/v1/traces?access_token=secret_token&signature=abc';
      const cleanUrl = sanitizeUrlForTelemetry(rawUrl);
      expect(cleanUrl).toBe('https://api.observability.com/v1/traces');
      expect(cleanUrl).not.toContain('secret123');
      expect(cleanUrl).not.toContain('access_token');
    });

    it('filters out non-whitelisted attributes via default-deny allowlist', () => {
      const rawAttributes = {
        'http.method': 'GET',
        'http.status_code': 200,
        'untrusted.sensitive.header': 'bearer_token_123',
        'raw.auth.payload': { password: 'secret' },
        'tenant.id': 'tenant-acme',
      };
      const cleanAttributes = filterAllowedAttributes(rawAttributes);
      expect(cleanAttributes).toEqual({
        'http.method': 'GET',
        'http.status_code': 200,
        'tenant.id': 'tenant-acme',
      });
      expect(cleanAttributes).not.toHaveProperty('untrusted.sensitive.header');
      expect(cleanAttributes).not.toHaveProperty('raw.auth.payload');
    });
  });

  describe('Tenant-Isolated SHA-256 Hashed Keys & Route Templates', () => {
    it('derives SHA-256 hashed request keys with tenant isolation', () => {
      const keyA = generateHashedKey('tenant-A', 'GET', 'http://api.org/data', { page: 1 });
      const keyB = generateHashedKey('tenant-B', 'GET', 'http://api.org/data', { page: 1 });
      expect(keyA).not.toEqual(keyB);
      expect(keyA).toMatch(/^[0-9a-f]{64}$/);
    });

    it('derives normalized route templates replacing unique IDs with :id', () => {
      const templateNum = deriveRouteTemplate('http://api.org/users/123/items/456');
      expect(templateNum).toBe('api.org/users/:id/items/:id');

      const templateUuid = deriveRouteTemplate('http://api.org/traces/a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d');
      expect(templateUuid).toBe('api.org/traces/:id');
    });
  });

  describe('SSRF Private IP & Protocol Protection', () => {
    it('blocks private internal IP ranges and invalid protocols', () => {
      expect(() => validateDestinationUrl('http://169.254.169.254/latest/meta-data')).toThrow(/SSRF Blocked/);
      expect(() => validateDestinationUrl('http://127.0.0.1/admin')).toThrow(/SSRF Blocked/);
      expect(() => validateDestinationUrl('ftp://api.org/data')).toThrow(/Blocked insecure URL protocol scheme/);
    });

    it('allows valid public HTTP/HTTPS URLs', () => {
      const valid = validateDestinationUrl('https://api.observability.com/v1/summary');
      expect(valid.hostname).toBe('api.observability.com');
    });
  });

  describe('Method Idempotency & Tenant Partitioned Cache', () => {
    it('restricts retries for non-idempotent methods unless x-idempotency-key is set', () => {
      expect(isMethodIdempotent('GET', {})).toBe(true);
      expect(isMethodIdempotent('POST', {})).toBe(false);
      expect(isMethodIdempotent('POST', { 'x-idempotency-key': 'uuid-123' })).toBe(true);
    });

    it('partitions cache stores per tenant preventing cross-tenant eviction', () => {
      const cache = new TenantPartitionedCacheStore(2);
      cache.set('tenant-1', 'key-1', 'data-tenant-1', 5000);
      cache.set('tenant-2', 'key-1', 'data-tenant-2', 5000);

      expect(cache.get('tenant-1', 'key-1')).toBe('data-tenant-1');
      expect(cache.get('tenant-2', 'key-1')).toBe('data-tenant-2');
    });
  });
});
