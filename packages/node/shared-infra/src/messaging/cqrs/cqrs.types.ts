export interface Command<TPayload = unknown> {
  commandId: string;
  commandName: string;
  timestamp: string;
  tenantId: string;
  payload: TPayload;
}

export interface DomainEvent<TPayload = unknown> {
  eventId: string;
  eventName: string;
  timestamp: string;
  tenantId: string;
  version: number;
  payload: TPayload;
}

export interface MaterializedProjection<TState = unknown> {
  projectionName: string;
  lastHandledEventId: string | null;
  state: TState;
  updatedAt: string;
}

export interface ProjectionStore<TState = unknown> {
  get(id: string): Promise<MaterializedProjection<TState> | null>;
  save(id: string, projection: MaterializedProjection<TState>): Promise<void>;
}

export interface QuerySelector<TQuery = unknown, TResult = unknown> {
  queryName: string;
  execute(query: TQuery): Promise<TResult>;
}
