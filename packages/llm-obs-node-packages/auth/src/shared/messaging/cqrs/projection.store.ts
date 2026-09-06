export interface AuthUserReadModel {
  userId: string;
  email: string;
  orgId: string;
  status: 'active' | 'pending';
  lastSignInAt?: string;
  createdAt: string;
  eventCount: number;
}

export class AuthReadProjectionStore {
  private static instance: AuthReadProjectionStore;
  private users = new Map<string, AuthUserReadModel>();

  public static getInstance(): AuthReadProjectionStore {
    if (!AuthReadProjectionStore.instance) {
      AuthReadProjectionStore.instance = new AuthReadProjectionStore();
    }
    return AuthReadProjectionStore.instance;
  }

  public applyUserSignedUp(event: { userId: string; email: string; orgId: string; timestamp: string }): void {
    const existing = this.users.get(event.userId);
    this.users.set(event.userId, {
      userId: event.userId,
      email: event.email,
      orgId: event.orgId,
      status: 'active',
      lastSignInAt: existing?.lastSignInAt,
      createdAt: existing?.createdAt || event.timestamp,
      eventCount: (existing?.eventCount || 0) + 1,
    });
    console.log(`[CQRS:ReadProjection] Folded USER_SIGNED_UP -> User: ${event.userId}`);
  }

  public applyUserSignedIn(event: { userId: string; email: string; orgId: string; timestamp: string }): void {
    const existing = this.users.get(event.userId);
    if (existing) {
      existing.lastSignInAt = event.timestamp;
      existing.eventCount += 1;
      this.users.set(event.userId, existing);
    } else {
      this.users.set(event.userId, {
        userId: event.userId,
        email: event.email,
        orgId: event.orgId,
        status: 'active',
        lastSignInAt: event.timestamp,
        createdAt: event.timestamp,
        eventCount: 1,
      });
    }
    console.log(`[CQRS:ReadProjection] Folded USER_SIGNED_IN -> User: ${event.userId}`);
  }

  public getUserById(userId: string): AuthUserReadModel | undefined {
    return this.users.get(userId);
  }

  public getAllUsers(): AuthUserReadModel[] {
    return Array.from(this.users.values());
  }

  public clear(): void {
    this.users.clear();
  }
}
