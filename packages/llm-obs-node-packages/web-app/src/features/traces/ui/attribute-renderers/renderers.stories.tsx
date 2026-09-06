import type { Meta } from '@storybook/react';
import React from 'react';
import {
  BooleanRenderer,
  ArrayRenderer,
  JsonObjectRenderer,
  CodeSnippetRenderer,
  NullSafeDefaultRenderer,
} from './renderers';

const meta: Meta = {
  title: 'Features/Traces/AttributeRenderers',
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
};

export default meta;

export const BooleanFlags = () => (
  <div className="flex flex-col gap-3 p-4 bg-[hsl(var(--card))] border border-[hsl(var(--border))] rounded-xl">
    <div className="flex items-center gap-4 text-xs">
      <span className="font-mono text-muted-foreground w-40">llm.pii_detected:</span>
      <BooleanRenderer keyName="llm.pii_detected" value={true} />
    </div>
    <div className="flex items-center gap-4 text-xs">
      <span className="font-mono text-muted-foreground w-40">llm.injection_attempt:</span>
      <BooleanRenderer keyName="llm.injection_attempt" value={true} />
    </div>
    <div className="flex items-center gap-4 text-xs">
      <span className="font-mono text-muted-foreground w-40">is_sampled:</span>
      <BooleanRenderer keyName="is_sampled" value={false} />
    </div>
  </div>
);

export const ArrayTagClouds = () => (
  <div className="flex flex-col gap-3 p-4 bg-[hsl(var(--card))] border border-[hsl(var(--border))] rounded-xl">
    <div className="flex flex-col gap-1 text-xs">
      <span className="font-mono text-muted-foreground">llm.span_warnings:</span>
      <ArrayRenderer
        keyName="llm.span_warnings"
        value={[
          'RULE-W-01: token_count_method == "estimated" -> warn: cost accuracy reduced',
          'RULE-W-02: retry_count > 0 -> warn: latency includes retry overhead',
        ]}
      />
    </div>
    <div className="flex flex-col gap-1 text-xs">
      <span className="font-mono text-muted-foreground">attempted_models:</span>
      <ArrayRenderer
        keyName="attempted_models"
        value={['gpt-4o', 'claude-3-5-sonnet', 'llama-3.1-70b']}
      />
    </div>
  </div>
);

export const ExpandableJsonObject = () => (
  <div className="p-4 bg-[hsl(var(--card))] border border-[hsl(var(--border))] rounded-xl text-xs space-y-2">
    <span className="font-mono text-muted-foreground">custom.metadata.config:</span>
    <JsonObjectRenderer
      keyName="custom.metadata.config"
      value={{
        temperature: 0.7,
        top_p: 0.95,
        fallback_chain: ['gpt-4o', 'claude-3-5-sonnet'],
        retry_policy: { max_retries: 3, backoff_factor: 2.0 },
      }}
    />
  </div>
);

export const CodeSnippets = () => (
  <div className="p-4 bg-[hsl(var(--card))] border border-[hsl(var(--border))] rounded-xl text-xs space-y-2">
    <span className="font-mono text-muted-foreground">llm.prompt:</span>
    <CodeSnippetRenderer
      keyName="llm.prompt"
      value="Explain the architectural benefits of self-hosting OpenTelemetry telemetry collectors in Kubernetes."
    />
  </div>
);

export const NullSafePrimitives = () => (
  <div className="flex flex-col gap-3 p-4 bg-[hsl(var(--card))] border border-[hsl(var(--border))] rounded-xl text-xs">
    <div className="flex items-center gap-4">
      <span className="font-mono text-muted-foreground w-40">null_value:</span>
      <NullSafeDefaultRenderer keyName="null_value" value={null} />
    </div>
    <div className="flex items-center gap-4">
      <span className="font-mono text-muted-foreground w-40">undefined_value:</span>
      <NullSafeDefaultRenderer keyName="undefined_value" value={undefined} />
    </div>
    <div className="flex items-center gap-4">
      <span className="font-mono text-muted-foreground w-40">number_value:</span>
      <NullSafeDefaultRenderer keyName="number_value" value={14500} />
    </div>
  </div>
);
