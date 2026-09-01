import type { Meta, StoryObj } from '@storybook/react';
import { SpanAttributeDrawer } from './SpanAttributeDrawer';
import type { SpanNode } from '../types';

const mockLLMSpan: SpanNode = {
  id: 'spn_llm_123',
  parent_id: 'spn_root_001',
  name: 'llm.generateCompletion',
  kind: 'CLIENT',
  service: 'latency-engine',
  model: 'gpt-4o',
  start_time_offset_ms: 150,
  duration_ms: 850,
  status: 'success',
  attributes: {
    'service.name': 'latency-engine',
    'endpoint': '/v1/chat/completions',
    'llm.provider': 'openai',
    'llm.model': 'gpt-4o',
    'llm.usage.prompt_tokens': 512,
    'llm.usage.completion_tokens': 128,
    'llm.latency_ms_ttft': 180,
    'llm.cost_usd_micro': 14500,
    'llm.finish_reason': 'stop',
    'llm.pii_detected': true,
    'llm.injection_attempt': false,
    'llm.span_warnings': [
      'RULE-W-01: token_count_method == "estimated" -> warn: cost accuracy reduced',
      'RULE-W-02: retry_count > 0 -> warn: latency includes retry overhead',
    ],
    'custom.metadata.config': {
      temperature: 0.7,
      top_p: 0.95,
      fallback_chain: ['gpt-4o', 'claude-3-5-sonnet'],
      retry_policy: { max_retries: 3, backoff_factor: 2.0 },
    },
    'llm.prompt': 'Explain the difference between P95 latency and SLO burn rates in LLM observability platforms.',
    'llm.completion': 'P95 latency indicates the 95th percentile request execution speed. SLO burn rate measures how rapidly an error budget is consumed over time.',
  },
};

const mockNullAttributesSpan: SpanNode = {
  id: 'spn_null_999',
  name: 'raw.fetchMetadata',
  kind: 'INTERNAL',
  service: 'web-app',
  start_time_offset_ms: 200,
  duration_ms: 50,
  status: 'error',
  attributes: {
    'empty_field': null,
    'missing_field': undefined,
    'zero_count': 0,
    'blank_text': '',
  },
};

const meta: Meta<typeof SpanAttributeDrawer> = {
  title: 'Features/Traces/SpanAttributeDrawer',
  component: SpanAttributeDrawer,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof SpanAttributeDrawer>;

export const LLMSpanWithVisitorRegistry: Story = {
  args: {
    span: mockLLMSpan,
    totalTraceDurationMs: 1200,
    onClose: () => console.log('Close drawer'),
  },
};

export const NullAndUndefinedAttributesSpan: Story = {
  args: {
    span: mockNullAttributesSpan,
    totalTraceDurationMs: 1200,
    onClose: () => console.log('Close drawer'),
  },
};
