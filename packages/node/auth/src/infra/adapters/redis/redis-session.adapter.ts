import type { AuthTokenPayload } from '../../../shared/types/auth.types';

export class RedisSessionAdapter {
  private readonly sessionStore = new Map<string, string>();

  async setSession(sessionId: string, payload: AuthTokenPayload, ttlSeconds = 3600): Promise<void> {
    const data = JSON.stringify({ payload, expiresAt: Date.now() + ttlSeconds * 1000 });
    this.sessionStore.set(sessionId, data);
  }

  async getSession(sessionId: string): Promise<AuthTokenPayload | null> {
    const raw = this.sessionStore.get(sessionId);
    if (!raw) return null;

    const parsed = JSON.parse(raw) as { payload: AuthTokenPayload; expiresAt: number };
    if (Date.now() > parsed.expiresAt) {
      this.sessionStore.delete(sessionId);
      return null;
    }
    return parsed.payload;
  }

  async deleteSession(sessionId: string): Promise<void> {
    this.sessionStore.delete(sessionId);
  }
}
