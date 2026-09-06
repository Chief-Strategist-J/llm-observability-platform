import type { Meta, StoryObj } from '@storybook/react';
import { TraceDetailWaterfallUI } from './TraceDetailWaterfallUI';
import type { TraceDetailResult } from '../types';

const mock5TierDeepTrace: TraceDetailResult = {
  trace_id: 'trc_deep_9900',
  root_span_name: 'POST /api/v1/agent/orchestrate',
  total_duration_ms: 2500,
  spans: [
    {
      id: 'spn_tier1_01',
      name: 'HTTP POST /api/v1/agent/orchestrate',
      kind: 'SERVER',
      service: 'web-app',
      start_time_offset_ms: 0,
      duration_ms: 2500,
      status: 'success',
      attributes: {
        'service.name': 'web-app',
        'endpoint': '/api/v1/agent/orchestrate',
      },
      children: [
        {
          id: 'spn_tier2_01',
          name: 'auth.verifySession',
          kind: 'INTERNAL',
          service: 'auth',
          start_time_offset_ms: 50,
          duration_ms: 100,
          status: 'success',
        },
        {
          id: 'spn_tier2_02',
          name: 'agent.plannerLoop',
          kind: 'INTERNAL',
          service: 'latency-engine',
          start_time_offset_ms: 200,
          duration_ms: 2200,
          status: 'success',
          children: [
            {
              id: 'spn_tier3_01',
              name: 'llm.generatePlanStep1',
              kind: 'CLIENT',
              service: 'latency-engine',
              model: 'gpt-4o',
              start_time_offset_ms: 250,
              duration_ms: 900,
              status: 'success',
              children: [
                {
                  id: 'spn_tier4_01',
                  name: 'embedding.computeVector',
                  kind: 'CLIENT',
                  service: 'queue-embedding-worker',
                  start_time_offset_ms: 1180,
                  duration_ms: 300,
                  status: 'success',
                  children: [
                    {
                      id: 'spn_tier5_01',
                      name: 'minilm.onnxInference',
                      kind: 'INTERNAL',
                      service: 'queue-embedding-worker',
                      start_time_offset_ms: 1220,
                      duration_ms: 240,
                      status: 'success',
                      attributes: {
                        'onnx.threads': 4,
                        'vector.dim': 384,
                      },
                    },
                  ],
                },
              ],
            },
            {
              id: 'spn_tier3_02',
              name: 'quality.evaluateStep1',
              kind: 'CLIENT',
              service: 'quality-engine',
              model: 'cross-encoder/ms-marco',
              start_time_offset_ms: 1550,
              duration_ms: 800,
              status: 'success',
            },
          ],
        },
      ],
    },
  ],
};

const meta: Meta<typeof TraceDetailWaterfallUI> = {
  title: 'Features/Traces/TraceDetailWaterfallUI',
  component: TraceDetailWaterfallUI,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof TraceDetailWaterfallUI>;

export const Deep5TierSpanTree: Story = {
  args: {
    trace: mock5TierDeepTrace,
    loading: false,
    error: null,
  },
};

export const LoadingState: Story = {
  args: {
    trace: null,
    loading: true,
  },
};
