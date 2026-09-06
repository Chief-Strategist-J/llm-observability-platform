import { FilterStateSchema, type FilterState } from '@observability/api-types';

export function encodeFilters(filters: FilterState): string {
  const params = new URLSearchParams();

  if (filters.dateRange?.from) {
    params.set('from', filters.dateRange.from);
  }
  if (filters.dateRange?.to) {
    params.set('to', filters.dateRange.to);
  }
  if (filters.model) {
    params.set('model', filters.model);
  }
  if (filters.service) {
    params.set('service', filters.service);
  }
  if (filters.environment && filters.environment !== 'all') {
    params.set('env', filters.environment);
  }

  return params.toString();
}

export function decodeFilters(searchParams: URLSearchParams | string): FilterState {
  const params = typeof searchParams === 'string' ? new URLSearchParams(searchParams) : searchParams;

  const raw: Record<string, unknown> = {};

  const from = params.get('from');
  const to = params.get('to');
  if (from && to) {
    raw.dateRange = { from, to };
  }

  const model = params.get('model');
  if (model) {
    raw.model = model;
  }

  const service = params.get('service');
  if (service) {
    raw.service = service;
  }

  const env = params.get('env');
  if (env) {
    raw.environment = env;
  }

  const result = FilterStateSchema.safeParse(raw);
  if (result.success) {
    return result.data;
  }

  return { environment: 'all' };
}
