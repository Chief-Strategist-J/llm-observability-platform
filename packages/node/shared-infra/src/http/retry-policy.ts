export interface RetryPolicyConfig {
  nonRetryableStatuses?: number[];
  nonRetryableCodes?: string[];
}

export class RetryPolicyRegistry {
  private readonly nonRetryableStatuses = new Set<number>([400, 401, 403, 404, 422]);
  private readonly nonRetryableCodes = new Set<string>(["UNAUTHORIZED", "FORBIDDEN", "VALIDATION_ERROR", "NOT_FOUND"]);

  public registerNonRetryableStatus(status: number): void {
    this.nonRetryableStatuses.add(status);
  }

  public registerNonRetryableCode(code: string): void {
    this.nonRetryableCodes.add(code);
  }

  public isRetryable(err: any): boolean {
    const status = err?.status ?? err?.statusCode;
    const code = err?.code ?? err?.errorCode;

    const isNonRetryableStatus = typeof status === "number" && this.nonRetryableStatuses.has(status);
    const isNonRetryableCode = typeof code === "string" && this.nonRetryableCodes.has(code);

    return !isNonRetryableStatus && !isNonRetryableCode;
  }
}

export const retryPolicyRegistry = new RetryPolicyRegistry();
