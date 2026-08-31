import type { Meta, StoryObj } from '@storybook/react';
import { TraceDetailWaterfallUI } from './TraceDetailWaterfallUI';

const meta: Meta<typeof TraceDetailWaterfallUI> = {
  title: 'Features/Traces/TraceDetailWaterfallUI',
  component: TraceDetailWaterfallUI,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
  },
};

export default meta;
type Story = StoryObj<typeof TraceDetailWaterfallUI>;

export const LoadedWaterfall: Story = {
  args: {
    trace: {
      trace_id: "trc_994a20f01b",
      root_span_name: "HTTP POST /v1/chat/completions",
      total_duration_ms: 1250,
      spans: [
        {
          id: "spn_root_1",
          name: "HTTP POST /v1/chat/completions",
          kind: "SERVER",
          service: "web-app",
          start_time_offset_ms: 0,
          duration_ms: 1250,
          status: "success",
          children: [
            {
              id: "spn_auth_2",
              name: "JWT Auth Verifier",
              kind: "INTERNAL",
              service: "auth-service",
              start_time_offset_ms: 12,
              duration_ms: 35,
              status: "success",
            },
            {
              id: "spn_infer_3",
              name: "LLM Model Inference",
              kind: "CLIENT",
              service: "latency-engine",
              model: "gpt-4o",
              start_time_offset_ms: 60,
              duration_ms: 1120,
              status: "success",
            },
          ],
        },
      ],
    },
    loading: false,
    error: null,
  },
};

export const ErrorWaterfall: Story = {
  args: {
    trace: {
      trace_id: "trc_err_8403c",
      root_span_name: "Agent Workflow Runner",
      total_duration_ms: 3400,
      spans: [
        {
          id: "spn_root_err",
          name: "Agent Workflow Runner",
          kind: "SERVER",
          service: "agent-engine",
          start_time_offset_ms: 0,
          duration_ms: 3400,
          status: "error",
          children: [
            {
              id: "spn_tool_err",
              name: "Python Sandbox Execution",
              kind: "INTERNAL",
              service: "sandbox-executor",
              start_time_offset_ms: 450,
              duration_ms: 2950,
              status: "error",
            },
          ],
        },
      ],
    },
    loading: false,
    error: null,
  },
};

export const SkeletonLoading: Story = {
  args: {
    trace: null,
    loading: true,
    error: null,
  },
};

export const TraceNotFound: Story = {
  args: {
    trace: null,
    loading: false,
    error: "Trace ID 'trc_invalid' not found in OpenTelemetry Tempo trace store.",
  },
};
