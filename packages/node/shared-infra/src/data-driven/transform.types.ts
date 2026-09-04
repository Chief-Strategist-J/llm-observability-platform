export enum JsonMapOpKind {
  RENAME = 'rename',
  PICK = 'pick',
  OMIT = 'omit',
  DEFAULT = 'default',
  COERCE = 'coerce',
}

export enum CoerceTarget {
  STRING = 'string',
  NUMBER = 'number',
  BOOLEAN = 'boolean',
  DATE = 'date',
}

export enum ListOpKind {
  FILTER = 'filter',
  SEARCH = 'search',
  SORT = 'sort',
  PAGINATE = 'paginate',
  PICK = 'pick',
  GROUP_BY = 'groupBy',
}

export enum FilterComparison {
  EQ = 'eq',
  NEQ = 'neq',
  GT = 'gt',
  LT = 'lt',
  CONTAINS = 'contains',
}

export enum SortDirection {
  ASC = 'asc',
  DESC = 'desc',
}

export type ListOp =
  | { op: ListOpKind.FILTER | 'filter'; field: string; value: unknown; cmp?: FilterComparison | `${FilterComparison}` }
  | { op: ListOpKind.SEARCH | 'search'; fields: string[]; query: string }
  | { op: ListOpKind.SORT | 'sort'; field: string; direction?: SortDirection | `${SortDirection}`; dir?: SortDirection | `${SortDirection}` }
  | { op: ListOpKind.PAGINATE | 'paginate'; page: number; pageSize: number }
  | { op: ListOpKind.PICK | 'pick'; fields: string[] }
  | { op: ListOpKind.GROUP_BY | 'groupBy'; field: string };

export type JsonMapOp =
  | { op: JsonMapOpKind.RENAME | 'rename'; from: string; to: string }
  | { op: JsonMapOpKind.PICK | 'pick'; keys: string[] }
  | { op: JsonMapOpKind.PICK | 'pick'; fields: string[] }
  | { op: JsonMapOpKind.OMIT | 'omit'; keys: string[] }
  | { op: JsonMapOpKind.OMIT | 'omit'; fields: string[] }
  | { op: JsonMapOpKind.DEFAULT | 'default'; key: string; value: unknown }
  | { op: JsonMapOpKind.DEFAULT | 'default'; field: string; value: unknown }
  | { op: JsonMapOpKind.COERCE | 'coerce'; key: string; to: CoerceTarget | `${CoerceTarget}` }
  | { op: JsonMapOpKind.COERCE | 'coerce'; field: string; to: CoerceTarget | `${CoerceTarget}` };
