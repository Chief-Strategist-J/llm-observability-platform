import type { OrgSession } from '@observability/api-types';
import { getServerSession } from '../auth/session';

export interface Context {
  session: OrgSession | null;
  orgId: string | null;
}

export async function createContext(): Promise<Context> {
  const session = await getServerSession();
  return {
    session,
    orgId: session?.org.id ?? null,
  };
}
