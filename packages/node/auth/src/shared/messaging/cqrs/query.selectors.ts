import { AuthReadProjectionStore, AuthUserReadModel } from './projection.store';

export const authSelectors = {
  getUserById(userId: string): AuthUserReadModel | undefined {
    return AuthReadProjectionStore.getInstance().getUserById(userId);
  },

  getAllActiveUsers(): AuthUserReadModel[] {
    return AuthReadProjectionStore.getInstance()
      .getAllUsers()
      .filter((u) => u.status === 'active');
  },

  getUserSummary(userId: string): { userId: string; email: string; isRecentlyActive: boolean } | undefined {
    const user = AuthReadProjectionStore.getInstance().getUserById(userId);
    if (!user) return undefined;
    const isRecentlyActive = user.lastSignInAt
      ? Date.now() - new Date(user.lastSignInAt).getTime() < 3600000
      : false;
    return {
      userId: user.userId,
      email: user.email,
      isRecentlyActive,
    };
  },
};
