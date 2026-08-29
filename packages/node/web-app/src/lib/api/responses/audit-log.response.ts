export interface AuditLogItem {
  id: string;
  event_type: string;
  actor_id?: string;
  details?: Record<string, unknown>;
  created_at: string;
}
