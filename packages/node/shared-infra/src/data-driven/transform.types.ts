export type ListOp =
  | { op: 'filter'; field: string; value: unknown }
  | { op: 'search'; fields: string[]; query: string }
  | { op: 'sort'; field: string; direction: 'asc' | 'desc' }
  | { op: 'paginate'; page: number; pageSize: number }
  | { op: 'pick'; fields: string[] }
  | { op: 'groupBy'; field: string };

export type JsonMapOp =
  | { op: 'rename'; from: string; to: string }
  | { op: 'pick'; fields: string[] }
  | { op: 'omit'; fields: string[] }
  | { op: 'default'; field: string; value: unknown }
  | { op: 'coerce'; field: string; to: 'string' | 'number' | 'boolean' | 'date' };
