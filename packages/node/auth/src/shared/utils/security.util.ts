export class SecurityEngine {
  private readonly failedAttempts = new Map<string, { count: number; lockedUntilMs: number }>();
  private readonly rateLimitMap = new Map<string, number[]>();
  private readonly revokedTokens = new Set<string>();
  private readonly knownDevices = new Map<string, Set<string>>();
  private readonly stepUpOtps = new Map<string, { otp: string; expiresAtMs: number }>();
  private readonly ipAccountAttempts = new Map<string, { emails: Set<string>; resetAtMs: number }>();

  public checkBruteForceLockout(email: string): boolean {
    const record = this.failedAttempts.get(email);
    if (!record) return false;
    if (Date.now() < record.lockedUntilMs) return true;
    if (Date.now() >= record.lockedUntilMs && record.lockedUntilMs > 0) {
      this.failedAttempts.delete(email);
      return false;
    }
    return false;
  }

  public recordFailedAttempt(email: string): void {
    const record = this.failedAttempts.get(email) ?? { count: 0, lockedUntilMs: 0 };
    record.count += 1;
    if (record.count >= 5) {
      record.lockedUntilMs = Date.now() + 15 * 60 * 1000;
    }
    this.failedAttempts.set(email, record);
  }

  public clearFailedAttempts(email: string): void {
    this.failedAttempts.delete(email);
  }

  public checkRateLimit(key: string, limit = 100, windowMs = 60000): boolean {
    const now = Date.now();
    const timestamps = (this.rateLimitMap.get(key) ?? []).filter((t) => now - t < windowMs);
    if (timestamps.length >= limit) return false;
    timestamps.push(now);
    this.rateLimitMap.set(key, timestamps);
    return true;
  }

  public revokeToken(token: string): void {
    this.revokedTokens.add(token);
  }

  public isTokenRevoked(token: string): boolean {
    return this.revokedTokens.has(token);
  }

  public sanitizeHtml(input: string): string {
    return input
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;')
      .replace(/\//g, '&#x2F;');
  }

  public generateCsrfToken(sessionId: string): string {
    return `csrf_${sessionId}_${Math.random().toString(36).substring(2, 15)}`;
  }

  public verifyCsrfToken(headerToken: string, expectedToken: string): boolean {
    return Boolean(headerToken && headerToken === expectedToken);
  }

  public detectCredentialStuffing(ip: string, email: string): boolean {
    const now = Date.now();
    const record = this.ipAccountAttempts.get(ip) ?? { emails: new Set<string>(), resetAtMs: now + 60000 };
    if (now > record.resetAtMs) {
      record.emails = new Set<string>();
      record.resetAtMs = now + 60000;
    }
    record.emails.add(email);
    this.ipAccountAttempts.set(ip, record);
    return record.emails.size > 5;
  }

  public registerAndDetectAnomaly(userId: string, deviceFingerprint: string): { isAnomaly: boolean } {
    const userDevices = this.knownDevices.get(userId) ?? new Set<string>();
    const isAnomaly = userDevices.size > 0 && !userDevices.has(deviceFingerprint);
    userDevices.add(deviceFingerprint);
    this.knownDevices.set(userId, userDevices);
    return { isAnomaly };
  }

  public generateStepUpOtp(userId: string): string {
    const otp = Math.floor(100000 + Math.random() * 900000).toString();
    this.stepUpOtps.set(userId, { otp, expiresAtMs: Date.now() + 300000 });
    return otp;
  }

  public verifyStepUpOtp(userId: string, inputOtp: string): boolean {
    const record = this.stepUpOtps.get(userId);
    if (!record) return false;
    if (Date.now() > record.expiresAtMs) return false;
    const isValid = record.otp === inputOtp;
    if (isValid) this.stepUpOtps.delete(userId);
    return isValid;
  }
}

export interface SecretStorePort {
  getSecret(key: string): Promise<string | null>;
}

export class EnvSecretStoreAdapter implements SecretStorePort {
  async getSecret(key: string): Promise<string | null> {
    return process.env[key] ?? null;
  }
}
