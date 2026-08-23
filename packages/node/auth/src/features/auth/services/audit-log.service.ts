import type { AuthRepositoryPort } from '../repository';
import type { AuditLogRecord, AuditLogFilter } from '../types';

export class AuditLogDomainService {
  constructor(private readonly repo: AuthRepositoryPort) {}

  async fetchUserAuditLogs(userId: string, filters?: AuditLogFilter): Promise<AuditLogRecord[]> {
    const mapped = filters
      ? {
          event_type: filters.event_type,
          from_ms: filters.from ? new Date(filters.from).getTime() : undefined,
          to_ms: filters.to ? new Date(filters.to).getTime() : undefined,
        }
      : undefined;
    return this.repo.fetchUserAuditLogs(userId, mapped);
  }

  async purgeExpiredSoftDeletes(): Promise<number> {
    return this.repo.purgeExpiredSoftDeletes();
  }
}
