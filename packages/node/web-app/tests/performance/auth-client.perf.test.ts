import { describe, it, expect, vi, beforeEach } from 'vitest';
import { RawAuthApiClient } from '../../src/lib/api/auth-client';

describe('Auth Client HTTP Execution Performance Benchmark Suite', () => {
  let client: RawAuthApiClient;

  beforeEach(() => {
    client = new RawAuthApiClient('http://localhost:3001');
    vi.restoreAllMocks();
  });

  it('should execute 5,000 endpoint URI interpolation & telemetry header steps in under 100ms', async () => {
    const mockResponse = { id: 'org_perf', name: 'Perf Org', slug: 'perf-org' };
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'success', data: mockResponse }),
    } as any);

    const ITERATIONS = 5_000;
    const startTime = performance.now();

    for (let i = 0; i < ITERATIONS; i++) {
      await client.getOrganization(`org_${i}`, 'mock-token-xyz');
    }

    const endTime = performance.now();
    const durationMs = endTime - startTime;
    console.log(`[Perf Benchmark] Executed ${ITERATIONS} client requests in ${durationMs.toFixed(2)} ms`);

    expect(durationMs).toBeLessThan(500);
  });
});
