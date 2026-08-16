import { describe, it, expect } from 'vitest';
import { RealPostgresAuthAdapter } from '../../src/infra/adapters/postgres/real-postgres-auth.adapter';

describe('RealPostgresAuthAdapter Unit & Connection Tests', () => {
  it('should initialize PostgreSQL / AlloyDB Omni connection pool with configured environment properties', async () => {
    const adapter = new RealPostgresAuthAdapter();
    const status = await adapter.getPoolStatus();
    expect(status.totalCount).toBe(0);
    expect(adapter.queries.TENANT_RLS.SET_LOCAL_TENANT_CONTEXT).toBe("SELECT set_config('app.current_org_id', $1, true)");
    await adapter.close();
  });
});
