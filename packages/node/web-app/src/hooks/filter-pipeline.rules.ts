export type TimeRangeOption = '1h' | '24h' | '7d' | '30d' | 'custom';

export interface DashboardFilters {
  timeRange: TimeRangeOption;
  from?: string;
  to?: string;
  model: string;
  service: string;
  environment: string;
}

export const DEFAULT_DASHBOARD_FILTERS: DashboardFilters = {
  timeRange: '24h',
  model: 'all',
  service: 'all',
  environment: 'all',
};

export interface FilterRuleConfig {
  key: keyof DashboardFilters;
  defaultValue: unknown;
  allowedValues?: Set<string>;
  isDate?: boolean;
}

export const FILTER_PIPELINE_RULES: FilterRuleConfig[] = [
  {
    key: 'timeRange',
    defaultValue: '24h',
    allowedValues: new Set(['1h', '24h', '7d', '30d', 'custom']),
  },
  {
    key: 'from',
    defaultValue: undefined,
    isDate: true,
  },
  {
    key: 'to',
    defaultValue: undefined,
    isDate: true,
  },
  {
    key: 'model',
    defaultValue: 'all',
  },
  {
    key: 'service',
    defaultValue: 'all',
  },
  {
    key: 'environment',
    defaultValue: 'all',
  },
];
