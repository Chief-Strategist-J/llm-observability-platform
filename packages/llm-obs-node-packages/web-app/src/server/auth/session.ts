import type { OrgSession, OrgRole } from '@observability/api-types';
import { auth } from './auth';

function parseUser(sessionUser: Record<string, unknown>, email: string) {
  return {
    id: typeof sessionUser.id === 'string' ? sessionUser.id : 'usr-001-admin',
    email,
    name: typeof sessionUser.name === 'string' ? sessionUser.name : 'Demo User',
    image: typeof sessionUser.image === 'string' ? sessionUser.image : undefined,
  };
}

function parseOrg(rawOrg: Record<string, unknown>) {
  return {
    id: typeof rawOrg.id === 'string' ? rawOrg.id : 'org-001-default',
    name: typeof rawOrg.name === 'string' ? rawOrg.name : 'Acme Corp',
    role: (typeof rawOrg.role === 'string' ? rawOrg.role : 'owner') as OrgRole,
  };
}

export async function getServerSession(): Promise<OrgSession | null> {
  const session = await auth();
  if (!session?.user?.email) return null;

  const rawUser = session.user as Record<string, unknown>;
  const rawSession = session as unknown as Record<string, unknown>;
  const rawOrg = (rawSession.org ?? {}) as Record<string, unknown>;

  return {
    user: parseUser(rawUser, session.user.email),
    org: parseOrg(rawOrg),
    expires: session.expires,
  };
}
