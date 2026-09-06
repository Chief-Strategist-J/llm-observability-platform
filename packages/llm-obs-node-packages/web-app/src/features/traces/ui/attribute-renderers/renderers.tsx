'use client';

import React, { useState } from 'react';
import { ChevronRight, ChevronDown, Check, Copy, AlertCircle, ShieldAlert } from 'lucide-react';
import { registerAttributeRenderer, type AttributeRenderContext } from './registry';

export function BooleanRenderer({ keyName, value }: AttributeRenderContext) {
  const boolVal = Boolean(value);
  const isSecurityOrPii = keyName.includes('pii') || keyName.includes('injection');

  if (isSecurityOrPii && boolVal) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
        <ShieldAlert size={12} />
        <span>TRUE (DETECTED)</span>
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold border ${
      boolVal ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-slate-500/10 text-slate-400 border-slate-500/20'
    }`}>
      {boolVal ? 'true' : 'false'}
    </span>
  );
}

export function ArrayRenderer({ keyName, value }: AttributeRenderContext) {
  const items = Array.isArray(value) ? value : [];
  const isWarningList = keyName.includes('warnings');

  if (items.length === 0) {
    return <span className="font-mono text-xs text-[hsl(var(--muted-foreground))]">[]</span>;
  }

  return (
    <div className="flex flex-wrap gap-1.5 py-1">
      {items.map((item, idx) => (
        <span
          key={idx}
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-medium border ${
            isWarningList
              ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
              : 'bg-indigo-500/10 text-indigo-300 border-indigo-500/20'
          }`}
        >
          {isWarningList && <AlertCircle size={10} />}
          <span>{String(item)}</span>
        </span>
      ))}
    </div>
  );
}

export function JsonObjectRenderer({ value }: AttributeRenderContext) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (value === null || value === undefined) {
    return <span className="font-mono text-xs text-[hsl(var(--muted-foreground))]">null</span>;
  }

  const jsonStr = JSON.stringify(value, null, 2);

  return (
    <div className="flex flex-col gap-1.5 my-1">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="inline-flex items-center gap-1 text-[11px] font-medium text-primary hover:underline w-fit"
      >
        {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        <span>{isExpanded ? 'Collapse JSON Object' : `Expand Object (${Object.keys(value as object).length} keys)`}</span>
      </button>

      {isExpanded && (
        <pre className="text-[11px] font-mono whitespace-pre-wrap p-2.5 rounded-lg border border-[hsl(var(--border))] bg-black/50 text-cyan-300/90 max-h-56 overflow-y-auto">
          {jsonStr}
        </pre>
      )}
    </div>
  );
}

export function CodeSnippetRenderer({ value }: AttributeRenderContext) {
  const [copied, setCopied] = useState(false);
  const text = String(value ?? '');

  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="p-2.5 rounded-lg border border-[hsl(var(--border))] bg-black/40 space-y-1.5 my-1">
      <div className="flex items-center justify-end">
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 text-[10px] text-[hsl(var(--muted-foreground))] hover:text-emerald-400 transition-colors"
        >
          {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
          <span>{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>
      <pre className="text-[11px] font-mono whitespace-pre-wrap text-emerald-300/90 max-h-36 overflow-y-auto break-all">
        {text}
      </pre>
    </div>
  );
}

export function NullSafeDefaultRenderer({ value }: AttributeRenderContext) {
  if (value === null || value === undefined) {
    return <span className="font-mono text-xs text-[hsl(var(--muted-foreground))] opacity-60">-</span>;
  }
  if (typeof value === 'number') {
    return <span className="font-mono text-xs font-semibold text-primary">{value.toLocaleString()}</span>;
  }
  return <span className="font-mono text-xs text-[hsl(var(--foreground))] break-all">{String(value)}</span>;
}

registerAttributeRenderer(
  'boolean-renderer',
  (_key, val) => typeof val === 'boolean',
  BooleanRenderer,
  100
);

registerAttributeRenderer(
  'array-renderer',
  (_key, val) => Array.isArray(val),
  ArrayRenderer,
  90
);

registerAttributeRenderer(
  'json-object-renderer',
  (_key, val) => typeof val === 'object' && val !== null && !Array.isArray(val),
  JsonObjectRenderer,
  80
);

registerAttributeRenderer(
  'code-snippet-renderer',
  (key, val) => (key.includes('prompt') || key.includes('completion') || key.includes('statement') || key.includes('payload')) && typeof val === 'string' && val.length > 30,
  CodeSnippetRenderer,
  70
);

registerAttributeRenderer(
  'default-renderer',
  () => true,
  NullSafeDefaultRenderer,
  0
);
