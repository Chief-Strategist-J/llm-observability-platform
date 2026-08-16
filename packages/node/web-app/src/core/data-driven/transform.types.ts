export type JsonMapOp =
  | { op: "rename"; from: string; to: string }
  | { op: "pick"; keys: string[] }
  | { op: "omit"; keys: string[] }
  | { op: "default"; key: string; value: unknown }
  | { op: "coerce"; key: string; to: "string" | "number" | "boolean" | "date" };

export type ListOp =
  | { op: "filter"; field: string; value: unknown; cmp?: "eq" | "neq" | "gt" | "lt" | "contains" }
  | { op: "search"; fields: string[]; query: string }
  | { op: "sort"; field: string; dir?: "asc" | "desc" }
  | { op: "paginate"; page: number; pageSize: number }
  | { op: "pick"; fields: string[] }
  | { op: "groupBy"; field: string };
