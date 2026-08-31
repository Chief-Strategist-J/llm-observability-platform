import type { Meta, StoryObj } from '@storybook/react';
import { QualityDashboardUI } from './QualityDashboardUI';

const meta: Meta<typeof QualityDashboardUI> = {
  title: 'Features/Quality/QualityDashboardUI',
  component: QualityDashboardUI,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
  },
};

export default meta;
type Story = StoryObj<typeof QualityDashboardUI>;

export const LoadedWithMetrics: Story = {
  args: {
    summary: {
      avg_quality_score: 0.94,
      score_delta_pct: 3.2,
      below_slo_count: 14,
      total_evaluated_prompts: 12500,
    },
    trend: [
      { date: '2026-08-25', avg_quality_score: 0.91, toxicity_alerts: 1, hallucination_alerts: 3 },
      { date: '2026-08-26', avg_quality_score: 0.93, toxicity_alerts: 0, hallucination_alerts: 2 },
      { date: '2026-08-27', avg_quality_score: 0.94, toxicity_alerts: 2, hallucination_alerts: 4 },
      { date: '2026-08-28', avg_quality_score: 0.95, toxicity_alerts: 0, hallucination_alerts: 1 },
      { date: '2026-08-29', avg_quality_score: 0.92, toxicity_alerts: 1, hallucination_alerts: 5 },
      { date: '2026-08-30', avg_quality_score: 0.96, toxicity_alerts: 0, hallucination_alerts: 1 },
      { date: '2026-08-31', avg_quality_score: 0.94, toxicity_alerts: 0, hallucination_alerts: 2 },
    ],
    models: [
      { model: 'gpt-4o', avg_score: 0.96, min_score: 0.81, max_score: 0.99, evaluation_count: 5400, pass_rate_pct: 99.1 },
      { model: 'claude-3-5-sonnet', avg_score: 0.95, min_score: 0.79, max_score: 0.98, evaluation_count: 4100, pass_rate_pct: 98.6 },
      { model: 'gpt-4o-mini', avg_score: 0.91, min_score: 0.72, max_score: 0.96, evaluation_count: 3000, pass_rate_pct: 95.8 },
    ],
    flaggedAlerts: [
      {
        id: 'ALERT-801',
        span_id: 'spn_99f2a01',
        alert_type: 'hallucination',
        severity: 'warning',
        confidence_score: 0.89,
        prompt_snippet: 'Factual contradiction detected in summary generation output for finance report.',
        timestamp: '2026-08-31T20:30:00Z',
      },
      {
        id: 'ALERT-802',
        span_id: 'spn_10b4c89',
        alert_type: 'toxicity',
        severity: 'critical',
        confidence_score: 0.96,
        prompt_snippet: 'Potential policy violation: high toxicity score in raw user prompt payload.',
        timestamp: '2026-08-31T19:45:00Z',
      },
      {
        id: 'ALERT-803',
        span_id: 'spn_44a1e90',
        alert_type: 'pii_leak',
        severity: 'info',
        confidence_score: 0.78,
        prompt_snippet: 'SSN pattern detected in input context buffer before masking.',
        timestamp: '2026-08-31T18:15:00Z',
      },
    ],
    loading: false,
    error: null,
  },
};

export const CriticalToxicitySpike: Story = {
  args: {
    summary: {
      avg_quality_score: 0.76,
      score_delta_pct: -12.5,
      below_slo_count: 142,
      total_evaluated_prompts: 9800,
    },
    trend: [
      { date: '2026-08-25', avg_quality_score: 0.92, toxicity_alerts: 0, hallucination_alerts: 1 },
      { date: '2026-08-26', avg_quality_score: 0.90, toxicity_alerts: 1, hallucination_alerts: 2 },
      { date: '2026-08-27', avg_quality_score: 0.88, toxicity_alerts: 3, hallucination_alerts: 4 },
      { date: '2026-08-28', avg_quality_score: 0.82, toxicity_alerts: 8, hallucination_alerts: 9 },
      { date: '2026-08-29', avg_quality_score: 0.79, toxicity_alerts: 14, hallucination_alerts: 12 },
      { date: '2026-08-30', avg_quality_score: 0.77, toxicity_alerts: 19, hallucination_alerts: 15 },
      { date: '2026-08-31', avg_quality_score: 0.76, toxicity_alerts: 24, hallucination_alerts: 18 },
    ],
    models: [
      { model: 'gpt-4o', avg_score: 0.88, min_score: 0.62, max_score: 0.95, evaluation_count: 4200, pass_rate_pct: 88.4 },
      { model: 'claude-3-5-sonnet', avg_score: 0.85, min_score: 0.58, max_score: 0.94, evaluation_count: 3100, pass_rate_pct: 84.1 },
      { model: 'gpt-4o-mini', avg_score: 0.68, min_score: 0.41, max_score: 0.88, evaluation_count: 2500, pass_rate_pct: 69.2 },
    ],
    flaggedAlerts: [
      {
        id: 'ALERT-901',
        span_id: 'spn_99f2a88',
        alert_type: 'toxicity',
        severity: 'critical',
        confidence_score: 0.99,
        prompt_snippet: 'CRITICAL ALERT: Prompt injection attempt resulting in unmasked toxic output payload.',
        timestamp: new Date().toISOString(),
      },
      {
        id: 'ALERT-902',
        span_id: 'spn_10b4c99',
        alert_type: 'toxicity',
        severity: 'critical',
        confidence_score: 0.97,
        prompt_snippet: 'Severe abusive language pattern detected across multiple user chat sessions.',
        timestamp: new Date(Date.now() - 1800000).toISOString(),
      },
      {
        id: 'ALERT-903',
        span_id: 'spn_44a1e99',
        alert_type: 'hallucination',
        severity: 'warning',
        confidence_score: 0.91,
        prompt_snippet: 'High hallucination index: model invented non-existent API endpoints in code response.',
        timestamp: new Date(Date.now() - 3600000).toISOString(),
      },
    ],
    loading: false,
    error: null,
  },
};

export const SkeletonLoading: Story = {
  args: {
    summary: null,
    trend: [],
    models: [],
    flaggedAlerts: [],
    loading: true,
    error: null,
  },
};

export const EmptyState: Story = {
  args: {
    summary: null,
    trend: [],
    models: [],
    flaggedAlerts: [],
    loading: false,
    error: null,
  },
};

export const ErrorState: Story = {
  args: {
    summary: null,
    trend: [],
    models: [],
    flaggedAlerts: [],
    loading: false,
    error: 'Failed to connect to Quality & Evaluation REST Service (HTTP 503 Service Unavailable)',
  },
};
