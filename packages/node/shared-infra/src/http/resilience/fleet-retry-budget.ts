/**
 * @file fleet-retry-budget.ts
 * @description Fleet-Wide Retry Storm Prevention Budgeting Engine.
 * 
 * ALGORITHM & SPECIFICATION:
 * 1. Retry Storm Prevention:
 *    - Tracks total requests (`totalRequests`) and total retry attempts (`totalRetries`).
 *    - Evaluates retry ratio: `ratio = totalRetries / totalRequests`.
 * 2. Dynamic Retry Suppression:
 *    - `canRetry()`: If `totalRequests >= minRequestsThreshold` AND `ratio > maxRetryRatio` (default: 20%),
 *      suppresses retries globally by returning `false`.
 *    - Prevents microservices from compounding downstream outages via retry storms.
 */

export class FleetRetryBudget {
  private totalRequests = 0;
  private totalRetries = 0;

  constructor(
    private readonly maxRetryRatio = 0.2,
    private readonly minRequestsThreshold = 10
  ) {}

  public recordRequest(): void {
    this.totalRequests++;
  }

  public recordRetry(): void {
    this.totalRetries++;
  }

  public canRetry(): boolean {
    if (this.totalRequests < this.minRequestsThreshold) {
      return true;
    }
    const ratio = this.totalRetries / this.totalRequests;
    return ratio <= this.maxRetryRatio;
  }

  public getStats(): { totalRequests: number; totalRetries: number; ratio: number } {
    const ratio = this.totalRequests > 0 ? this.totalRetries / this.totalRequests : 0;
    return {
      totalRequests: this.totalRequests,
      totalRetries: this.totalRetries,
      ratio,
    };
  }
}
