import type { OrgSession, OrgRole } from '@observability/api-types';
import { auth } from './auth';

export async function getServerSession(): Promise<OrgSession | null> {
  const session = await auth();
  if (!session?.user?.email) return null;

  const rawUser = session.user as Record<string, unknown>;
  const rawSession = session as unknown as Record<string, unknown>;
  const rawOrg = (rawSession.org ?? {}) as Record<string, unknown>;

  return {
    user: {
      id: typeof rawUser.id === 'string' ? rawUser.id : 'usr-001-admin',
      email: session.user.email,
      name: session.user.name ?? 'Demo User',
      image: session.user.image ?? undefined,
    },
    org: {
      id: typeof rawOrg.id === 'string' ? rawOrg.id : 'org-001-default',
      name: typeof rawOrg.name === 'string' ? rawOrg.name : 'Acme Corp',
      role: (typeof rawOrg.role === 'string' ? rawOrg.role : 'owner') as OrgRole,
    },
    expires: session.expires,
  };
}
