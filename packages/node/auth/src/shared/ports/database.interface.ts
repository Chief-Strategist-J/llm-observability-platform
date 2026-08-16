export interface IDatabasePort {
  query<T = unknown>(sql: string, params?: unknown[]): Promise<{ rows: T[] }>;
}
