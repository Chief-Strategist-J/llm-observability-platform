import { test, expect } from '@playwright/test';
import { executeHttpRequest } from '../../../src/lib/api/executor';

test.describe('Category K — Observability Under Failure Automation Suite', () => {

  test('K-01: Should inject x-request-id and x-correlation-id header tokens into outbound HTTP requests', async () => {
    // Intercept fetch to verify correlation headers are attached automatically
    let capturedHeaders: Record<string, string> = {};

    const originalFetch = globalThis.fetch;
    globalThis.fetch = async (url: any, init: any) => {
      capturedHeaders = (init?.headers || {}) as Record<string, string>;
      return new Response(JSON.stringify({ status: 'success', data: [] }), { status: 200 });
    };

    try {
      await executeHttpRequest('http://localhost:3001', 'listOrganizations');
      expect(capturedHeaders['x-request-id']).toBeDefined();
      expect(capturedHeaders['x-correlation-id']).toBeDefined();
      expect(capturedHeaders['x-request-id']).toMatch(/^req-/);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});
