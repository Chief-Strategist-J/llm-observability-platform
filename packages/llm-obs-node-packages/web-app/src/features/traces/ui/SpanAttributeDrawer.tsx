'use client';

import React, { useState } from 'react';
import { X, Copy, Check, Clock, Tag, Code, Terminal, Layers } from 'lucide-react';
import type { SpanNode } from '../types';
import { TRACES_TEXT, OTEL_ATTRIBUTES } from '../constants';
import { renderAttribute } from './attribute-renderers';

export interface SpanAttributeDrawerProps {
  span: SpanNode | null;
  totalTraceDurationMs: number;
  onClose: () => void;
}

export function SpanAttributeDrawer({
  span,
  totalTraceDurationMs,
  onClose,
}: SpanAttributeDrawerProps) {
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  if (!span) return null;

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const durationMs = span.duration_ms ?? 0;
  const totalMs = totalTraceDurationMs > 0 ? totalTraceDurationMs : 1;
  const durationPct = ((durationMs / totalMs) * 100).toFixed(1);

  const attributes = span.attributes ?? {};
  const promptSnippet = attributes[OTEL_ATTRIBUTES.PROMPT_TEXT] || attributes['llm.prompt'] || attributes['prompt'] || attributes['input'];
  const completionSnippet = attributes[OTEL_ATTRIBUTES.COMPLETION_TEXT] || attributes['llm.completion'] || attributes['completion'] || attributes['output'];

  return (
    <div className="span-drawer-overlay animate-in fade-in duration-200">
      <div className="flex-1" onClick={onClose} />

      <div className="span-drawer-card animate-in slide-in-from-right duration-300">
        <div className="p-5 border-b border-[hsl(var(--border))] flex items-center justify-between bg-[hsl(var(--muted)/0.3)]">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10 text-primary border border-primary/20">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-[hsl(var(--foreground))] truncate max-w-xs">{span.name || 'Unnamed Span'}</h3>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-xs text-[hsl(var(--muted-foreground))] font-mono">{span.service || 'unspecified'}</span>
                <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-[hsl(var(--muted))] text-[hsl(var(--muted-foreground))]">
                  {span.kind || 'INTERNAL'}
                </span>
                <span className={span.status === 'success' ? 'traces-badge-success' : 'traces-badge-error'}>
                  {span.status || 'unknown'}
                </span>
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--muted))] transition-colors"
            aria-label={TRACES_TEXT.DRAWER_CLOSE}
          >
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          <div className="p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--muted)/0.15)] flex flex-col gap-3">
            <div className="flex items-center justify-between text-xs font-semibold text-[hsl(var(--foreground))]">
              <span className="flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-primary" />
                {TRACES_TEXT.DRAWER_TITLE}
              </span>
              <span className="font-mono text-primary">{durationMs} ms</span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="p-2.5 rounded-lg bg-[hsl(var(--card))] border border-[hsl(var(--border))]">
                <div className="text-[10px] text-[hsl(var(--muted-foreground))]">{TRACES_TEXT.DRAWER_START_OFFSET}</div>
                <div className="font-mono font-bold mt-0.5">{span.start_time_offset_ms ?? 0} ms</div>
              </div>
              <div className="p-2.5 rounded-lg bg-[hsl(var(--card))] border border-[hsl(var(--border))]">
                <div className="text-[10px] text-[hsl(var(--muted-foreground))]">{TRACES_TEXT.DRAWER_DURATION}</div>
                <div className="font-mono font-bold mt-0.5">{durationMs} ms</div>
              </div>
              <div className="p-2.5 rounded-lg bg-[hsl(var(--card))] border border-[hsl(var(--border))]">
                <div className="text-[10px] text-[hsl(var(--muted-foreground))]">{TRACES_TEXT.DRAWER_TRACE_PCT}</div>
                <div className="font-mono font-bold text-indigo-400 mt-0.5">{durationPct}%</div>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <div className="text-xs font-semibold text-[hsl(var(--foreground))] flex items-center gap-1.5">
              <Tag className="w-4 h-4 text-indigo-400" />
              {TRACES_TEXT.DRAWER_SPAN_IDENTIFIERS}
            </div>
            <div className="p-3 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-[hsl(var(--muted-foreground))]">{TRACES_TEXT.DRAWER_SPAN_ID}</span>
                <div className="flex items-center gap-1.5 font-mono text-primary">
                  <span>{span.id || '-'}</span>
                  {span.id && (
                    <button
                      onClick={() => handleCopy(span.id, 'span_id')}
                      className="p-1 hover:bg-[hsl(var(--muted))] rounded transition-colors text-[hsl(var(--muted-foreground))]"
                      title="Copy Span ID"
                    >
                      {copiedKey === 'span_id' ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                    </button>
                  )}
                </div>
              </div>
              {span.parent_id && (
                <div className="flex items-center justify-between border-t border-[hsl(var(--border)/0.5)] pt-2">
                  <span className="text-[hsl(var(--muted-foreground))]">{TRACES_TEXT.DRAWER_PARENT_SPAN_ID}</span>
                  <span className="font-mono text-[hsl(var(--muted-foreground))]">{span.parent_id}</span>
                </div>
              )}
              {span.model && (
                <div className="flex items-center justify-between border-t border-[hsl(var(--border)/0.5)] pt-2">
                  <span className="text-[hsl(var(--muted-foreground))]">{TRACES_TEXT.DRAWER_MODEL_TARGET}</span>
                  <span className="font-mono text-amber-400 font-semibold">{span.model}</span>
                </div>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <div className="text-xs font-semibold text-[hsl(var(--foreground))] flex items-center gap-1.5">
              <Code className="w-4 h-4 text-cyan-400" />
              {TRACES_TEXT.DRAWER_OTEL_ATTRIBUTES} ({Object.keys(attributes).length})
            </div>
            {Object.keys(attributes).length === 0 ? (
              <div className="p-4 rounded-xl border border-[hsl(var(--border))] text-xs text-[hsl(var(--muted-foreground))] text-center">
                {TRACES_TEXT.DRAWER_NO_ATTRIBUTES}
              </div>
            ) : (
              <div className="rounded-xl border border-[hsl(var(--border))] overflow-hidden bg-[hsl(var(--card))]">
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="bg-[hsl(var(--muted)/0.4)] border-b border-[hsl(var(--border))] text-[10px] font-bold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">
                      <th className="py-2 px-3">{TRACES_TEXT.DRAWER_COL_KEY}</th>
                      <th className="py-2 px-3">{TRACES_TEXT.DRAWER_COL_VALUE}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(attributes).map(([key, val]) => (
                      <tr key={key} className="border-b border-[hsl(var(--border)/0.4)] hover:bg-[hsl(var(--muted)/0.2)]">
                        <td className="py-2.5 px-3 font-mono font-medium text-indigo-300 truncate max-w-[180px]" title={key}>
                          {key}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-[hsl(var(--foreground))]">
                          {renderAttribute(key, val)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {(promptSnippet !== undefined || completionSnippet !== undefined) && (
            <div className="space-y-3">
              <div className="text-xs font-semibold text-[hsl(var(--foreground))] flex items-center gap-1.5">
                <Terminal className="w-4 h-4 text-emerald-400" />
                {TRACES_TEXT.DRAWER_PAYLOAD_HEADER}
              </div>
              {promptSnippet !== undefined && (
                <div className="p-3 rounded-xl border border-[hsl(var(--border))] bg-black/40 space-y-1.5">
                  <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-emerald-400">
                    <span>{TRACES_TEXT.DRAWER_PROMPT_INPUT}</span>
                    <button
                      onClick={() => handleCopy(String(promptSnippet ?? ''), 'prompt')}
                      className="flex items-center gap-1 text-[hsl(var(--muted-foreground))] hover:text-emerald-400 transition-colors"
                    >
                      {copiedKey === 'prompt' ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                      <span>{TRACES_TEXT.DRAWER_COPY_BUTTON}</span>
                    </button>
                  </div>
                  <pre className="text-xs font-mono whitespace-pre-wrap text-emerald-300/90 max-h-40 overflow-y-auto p-1">
                    {String(promptSnippet ?? '')}
                  </pre>
                </div>
              )}

              {completionSnippet !== undefined && (
                <div className="p-3 rounded-xl border border-[hsl(var(--border))] bg-black/40 space-y-1.5">
                  <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-cyan-400">
                    <span>{TRACES_TEXT.DRAWER_COMPLETION_OUTPUT}</span>
                    <button
                      onClick={() => handleCopy(String(completionSnippet ?? ''), 'completion')}
                      className="flex items-center gap-1 text-[hsl(var(--muted-foreground))] hover:text-cyan-400 transition-colors"
                    >
                      {copiedKey === 'completion' ? <Check size={12} className="text-cyan-400" /> : <Copy size={12} />}
                      <span>{TRACES_TEXT.DRAWER_COPY_BUTTON}</span>
                    </button>
                  </div>
                  <pre className="text-xs font-mono whitespace-pre-wrap text-cyan-300/90 max-h-40 overflow-y-auto p-1">
                    {String(completionSnippet ?? '')}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
