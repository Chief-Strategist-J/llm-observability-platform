import { httpClient } from '../http/http-client';
import { mapJson } from './json-map';
import type { EntitySchema } from './entity-schema.types';

export interface CrudPort<T> {
  list(): Promise<T[]>;
  get(id: string): Promise<T>;
  create(payload: Partial<T>): Promise<T>;
  update(id: string, payload: Partial<T>): Promise<T>;
  remove(id: string): Promise<void>;
}

export function createEntityAdapter<T extends Record<string, unknown>>(
  schema: EntitySchema<T>,
): CrudPort<T> {
  const fromApi = (raw: unknown): T => {
    const mapped = schema.fromApi ? mapJson(raw as Record<string, unknown>, schema.fromApi) : raw;
    return schema.validate.parse(mapped);
  };

  const toApi = (entity: Partial<T>): Record<string, unknown> => {
    return schema.toApi
      ? mapJson(entity as Record<string, unknown>, schema.toApi)
      : (entity as Record<string, unknown>);
  };

  return {
    async list(): Promise<T[]> {
      const { data } = await httpClient.get<unknown[]>(schema.endpoint);
      return (data as unknown[]).map(fromApi);
    },
    async get(id: string): Promise<T> {
      const { data } = await httpClient.get<unknown>(`${schema.endpoint}/${id}`);
      return fromApi(data);
    },
    async create(payload: Partial<T>): Promise<T> {
      const { data } = await httpClient.post<unknown>(schema.endpoint, toApi(payload));
      return fromApi(data);
    },
    async update(id: string, payload: Partial<T>): Promise<T> {
      const { data } = await httpClient.patch<unknown>(`${schema.endpoint}/${id}`, toApi(payload));
      return fromApi(data);
    },
    async remove(id: string): Promise<void> {
      await httpClient.delete(`${schema.endpoint}/${id}`);
    },
  };
}
