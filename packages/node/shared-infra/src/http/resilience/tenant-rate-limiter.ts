/**
 * @file tenant-rate-limiter.ts
 * @description Outbound Per-Tenant Token Bucket Rate Limiter.
 * 
 * ALGORITHM & SPECIFICATION:
 * 1. Token Bucket Mathematical Model:
 *    - Each `tenantId` maintains a bucket with `capacity` (max tokens) and `fillRate` (tokens/sec).
 *    - On evaluation, calculates elapsed time $\Delta t = \text{now} - \text{lastRefill}$.
 *    - Refills tokens: $\text{tokens} = \min(\text{capacity}, \text{tokens} + \Delta t \times \text{fillRate})$.
 * 2. Admission Control:
 *    - `allowRequest(tenantId)`: Consumes 1 token if $\text{tokens} \ge 1$ and returns `true`.
 *    - Returns `false` if insufficient tokens remain.
 */

interface Bucket {
  tokens: number;
  lastRefill: number;
}

export class TenantRateLimiter {
  private readonly buckets = new Map<string, Bucket>();

  constructor(
    private readonly capacity = 100,
    private readonly fillRatePerSec = 50
  ) {}

  public allowRequest(tenantId: string): boolean {
    const now = Date.now();
    let bucket = this.buckets.get(tenantId);

    if (!bucket) {
      bucket = { tokens: this.capacity, lastRefill: now };
      this.buckets.set(tenantId, bucket);
    }

    const elapsedSec = (now - bucket.lastRefill) / 1000;
    bucket.tokens = Math.min(this.capacity, bucket.tokens + elapsedSec * this.fillRatePerSec);
    bucket.lastRefill = now;

    if (bucket.tokens >= 1) {
      bucket.tokens -= 1;
      return true;
    }

    return false;
  }
}
