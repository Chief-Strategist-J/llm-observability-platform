import {
  useEffect,
  useState,
  useRef,
  useMemo,
  useCallback,
  memo,
} from 'react';
import ReactFlow, {
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Position,
  NodeProps,
  Handle,
  BackgroundVariant,
  EdgeProps,
  getBezierPath,
  useReactFlow,
  ReactFlowProvider,
  Node,
  Edge,
  FitViewOptions,
  useStore,
} from 'reactflow';
import 'reactflow/dist/style.css';

// ═══════════════════════════════════════════════════════════════════
// § 1  TYPES
// ═══════════════════════════════════════════════════════════════════

export type Theme = 'dark' | 'light';

export interface Span {
  span_id: string;
  parent_span_id: string | null;
  trace_id: string;
  service_name: string;
  operation_name: string;
  start_time: number;
  end_time: number;
  duration_ms: number;
  status: 'ok' | 'error' | 'unset';
  attributes?: Record<string, unknown>;
}

export interface TraceDAGViewProps {
  spans: Span[];
  theme?: Theme;
  onThemeChange?: (theme: Theme) => void;
}

interface ThemeTokens {
  bg: string;
  grid: string;
  nodeBg: string;
  nodeBgHover: string;
  nodeBgSelected: string;
  nodeBorder: string;
  nodeBorderHover: string;
  nodeBorderSelected: string;
  text: string;
  textMuted: string;
  textFaint: string;
  accent: string;
  edgeColor: string;
  panelBg: string;
  panelBorder: string;
  chipBg: string;
  chipBorder: string;
  ok: string;
  error: string;
  unset: string;
  ctrlBg: string;
  ctrlBorder: string;
  shadow1: string;
  shadow2: string;
  shadow3: string;
  scrollbar: string;
}

/**
 * Node data stored in React Flow. Crucially, it does NOT contain
 * `isSelected` — selection is applied via a separate targeted
 * node-update so layout never re-runs on selection change.
 */
interface SpanNodeData {
  span: Span;
  isRoot: boolean;
  theme: Theme;
  serviceHue: number;
  /** Updated independently; does NOT cause layout recompute. */
  isSelected: boolean;
  /** Stable ref-based callback — never changes identity. */
  onSelectRef: React.MutableRefObject<(id: string) => void>;
}

interface LayoutResult {
  spanId: string;
  x: number;
  y: number;
  isRoot: boolean;
}

interface TraceStats {
  spanCount: number;
  serviceCount: number;
  totalDurationMs: number;
  maxDepth: number;
  errorCount: number;
}

// ═══════════════════════════════════════════════════════════════════
// § 2  CONSTANTS
// ═══════════════════════════════════════════════════════════════════

const NW = 172;   // node width
const NH = 54;    // node height
const HG = 72;    // horizontal gap between columns
const VG = 14;    // vertical gap between sibling rows
const FVO: FitViewOptions = { padding: 0.18, duration: 350 };

// ═══════════════════════════════════════════════════════════════════
// § 3  THEME
// ═══════════════════════════════════════════════════════════════════

const DARK: ThemeTokens = {
  bg: '#0d1117',
  grid: '#1c2128',
  nodeBg: '#161b22',
  nodeBgHover: '#1c2333',
  nodeBgSelected: '#1c2333',
  nodeBorder: '#2d333b',
  nodeBorderHover: '#444c56',
  nodeBorderSelected: '#388bfd',
  text: '#cdd9e5',
  textMuted: '#768390',
  textFaint: '#444c56',
  accent: '#388bfd',
  edgeColor: '#2d333b',
  panelBg: 'rgba(13,17,23,0.92)',
  panelBorder: '#2d333b',
  chipBg: '#161b22',
  chipBorder: '#2d333b',
  ok: '#3fb950',
  error: '#f85149',
  unset: '#6e7681',
  ctrlBg: '#161b22',
  ctrlBorder: '#2d333b',
  shadow1: '0 1px 4px rgba(0,0,0,0.55)',
  shadow2: '0 4px 16px rgba(0,0,0,0.65)',
  shadow3: '0 10px 36px rgba(0,0,0,0.75)',
  scrollbar: '#2d333b',
};

const LIGHT: ThemeTokens = {
  bg: '#f6f8fa',
  grid: '#d0d7de',
  nodeBg: '#ffffff',
  nodeBgHover: '#f6f8fa',
  nodeBgSelected: '#ddf4ff',
  nodeBorder: '#d0d7de',
  nodeBorderHover: '#adb6c0',
  nodeBorderSelected: '#0969da',
  text: '#1f2328',
  textMuted: '#656d76',
  textFaint: '#d0d7de',
  accent: '#0969da',
  edgeColor: '#c6cdd5',
  panelBg: 'rgba(255,255,255,0.94)',
  panelBorder: '#d0d7de',
  chipBg: '#f6f8fa',
  chipBorder: '#d0d7de',
  ok: '#1a7f37',
  error: '#cf222e',
  unset: '#6e7781',
  ctrlBg: '#ffffff',
  ctrlBorder: '#d0d7de',
  shadow1: '0 1px 3px rgba(0,0,0,0.10)',
  shadow2: '0 4px 14px rgba(0,0,0,0.12)',
  shadow3: '0 10px 32px rgba(0,0,0,0.16)',
  scrollbar: '#d0d7de',
};

function tok(theme: Theme): ThemeTokens {
  return theme === 'dark' ? DARK : LIGHT;
}

// ═══════════════════════════════════════════════════════════════════
// § 4  PURE HELPERS
// ═══════════════════════════════════════════════════════════════════

function serviceHue(name: string): number {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = name.charCodeAt(i) + ((h << 5) - h);
  return Math.abs(h) % 360;
}

function accentForHue(hue: number, theme: Theme): string {
  return theme === 'dark'
    ? `hsl(${hue},60%,58%)`
    : `hsl(${hue},58%,42%)`;
}

function fmtMs(ms: number): string {
  if (!Number.isFinite(ms) || ms < 0) return '—';
  if (ms < 1) return `${(ms * 1000).toFixed(0)}μs`;
  if (ms < 1000) return `${ms.toFixed(1)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

function validateSpans(raw: unknown): Span[] {
  if (!Array.isArray(raw)) return [];
  return raw.filter(
    (s): s is Span =>
      s != null &&
      typeof s === 'object' &&
      typeof (s as Span).span_id === 'string' &&
      (s as Span).span_id.length > 0 &&
      typeof (s as Span).service_name === 'string' &&
      typeof (s as Span).operation_name === 'string',
  );
}

/** Stable key that only changes when span IDs change. */
function spansKey(spans: Span[]): string {
  return spans
    .map(s => s.span_id)
    .slice()
    .sort()
    .join('\x00');
}

// ═══════════════════════════════════════════════════════════════════
// § 5  LAYOUT  (pure, no React)
// ═══════════════════════════════════════════════════════════════════

function buildChildMap(spans: Span[]): Map<string, string[]> {
  const ids = new Set(spans.map(s => s.span_id));
  const map = new Map<string, string[]>(spans.map(s => [s.span_id, []]));
  for (const s of spans) {
    if (s.parent_span_id && ids.has(s.parent_span_id)) {
      map.get(s.parent_span_id)!.push(s.span_id);
    }
  }
  return map;
}

function computeLayout(spans: Span[]): Map<string, LayoutResult> {
  const out = new Map<string, LayoutResult>();
  if (spans.length === 0) return out;

  const ids = new Set(spans.map(s => s.span_id));
  const childMap = buildChildMap(spans);
  const roots = spans.filter(s => !s.parent_span_id || !ids.has(s.parent_span_id));

  // subtree leaf-count for vertical band allocation
  const leafCount = new Map<string, number>();
  function countLeaves(id: string, visited = new Set<string>()): number {
    if (visited.has(id)) return 1;
    visited.add(id);
    const ch = (childMap.get(id) ?? []).filter(c => ids.has(c));
    if (ch.length === 0) { leafCount.set(id, 1); return 1; }
    const n = ch.reduce((a, c) => a + countLeaves(c, visited), 0);
    leafCount.set(id, n);
    return n;
  }
  for (const r of roots) countLeaves(r.span_id);

  let globalTop = 0;

  function place(
    id: string,
    col: number,
    bandTop: number,
    bandLeaves: number,
    isRoot: boolean,
    seen = new Set<string>(),
  ): void {
    if (seen.has(id)) return;
    seen.add(id);

    const rowH = NH + VG;
    const x = col * (NW + HG);
    const y = bandTop + (bandLeaves * rowH) / 2 - NH / 2;
    out.set(id, { spanId: id, x, y, isRoot });

    const children = (childMap.get(id) ?? []).filter(c => ids.has(c) && !seen.has(c));
    let childTop = bandTop;
    for (const child of children) {
      const leaves = leafCount.get(child) ?? 1;
      place(child, col + 1, childTop, leaves, false, seen);
      childTop += leaves * rowH;
    }
  }

  for (const r of roots) {
    const leaves = leafCount.get(r.span_id) ?? 1;
    place(r.span_id, 0, globalTop, leaves, true, new Set());
    globalTop += leaves * (NH + VG) + VG * 8;
  }

  return out;
}

// ═══════════════════════════════════════════════════════════════════
// § 6  STATS  (pure, no React)
// ═══════════════════════════════════════════════════════════════════

function computeStats(spans: Span[]): TraceStats {
  if (spans.length === 0)
    return { spanCount: 0, serviceCount: 0, totalDurationMs: 0, maxDepth: 0, errorCount: 0 };

  const ids = new Set(spans.map(s => s.span_id));
  const childMap = buildChildMap(spans);
  const roots = spans.filter(s => !s.parent_span_id || !ids.has(s.parent_span_id));

  function depth(id: string, seen = new Set<string>()): number {
    if (seen.has(id)) return 0;
    seen.add(id);
    const ch = (childMap.get(id) ?? []).filter(c => ids.has(c));
    return ch.length === 0 ? 1 : 1 + Math.max(...ch.map(c => depth(c, seen)));
  }

  return {
    spanCount: spans.length,
    serviceCount: new Set(spans.map(s => s.service_name)).size,
    totalDurationMs: spans.reduce((a, s) => a + (Number.isFinite(s.duration_ms) ? s.duration_ms : 0), 0),
    maxDepth: roots.length > 0 ? Math.max(...roots.map(r => depth(r.span_id))) : 0,
    errorCount: spans.filter(s => s.status === 'error').length,
  };
}

// ═══════════════════════════════════════════════════════════════════
// § 7  NODE / EDGE FACTORIES  (pure, no React)
// ═══════════════════════════════════════════════════════════════════

function makeNodes(
  spans: Span[],
  layout: Map<string, LayoutResult>,
  theme: Theme,
  onSelectRef: React.MutableRefObject<(id: string) => void>,
): Node<SpanNodeData>[] {
  const hues = new Map<string, number>();
  const getHue = (name: string) => {
    if (!hues.has(name)) hues.set(name, serviceHue(name));
    return hues.get(name)!;
  };

  return spans.reduce<Node<SpanNodeData>[]>((acc, span) => {
    const pos = layout.get(span.span_id);
    if (!pos) return acc;
    acc.push({
      id: span.span_id,
      type: 'spanNode',
      position: { x: pos.x, y: pos.y },
      width: NW,
      height: NH,
      draggable: true,
      selectable: false, // we handle selection ourselves
      data: {
        span,
        isRoot: pos.isRoot,
        theme,
        serviceHue: getHue(span.service_name),
        isSelected: false,
        onSelectRef,
      },
    });
    return acc;
  }, []);
}

function makeEdges(spans: Span[], theme: Theme): Edge[] {
  const t = tok(theme);
  const ids = new Set(spans.map(s => s.span_id));
  return spans
    .filter(s => s.parent_span_id != null && ids.has(s.parent_span_id!))
    .map(s => ({
      id: `${s.parent_span_id!}→${s.span_id}`,
      source: s.parent_span_id!,
      target: s.span_id,
      type: 'traceEdge',
      data: { color: t.edgeColor },
      selectable: false,
      focusable: false,
    }));
}

// ═══════════════════════════════════════════════════════════════════
// § 8  CSS INJECTION  (once per lifetime)
// ═══════════════════════════════════════════════════════════════════

let _cssReady = false;
function ensureCSS(): void {
  if (_cssReady || typeof document === 'undefined') return;
  _cssReady = true;
  const el = document.createElement('style');
  el.textContent = `
    @keyframes _traceSpin  { to { transform: rotate(360deg); } }
    @keyframes _traceFadeUp { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
    @keyframes _traceSlideIn { from { opacity:0; transform:translateX(12px); } to { opacity:1; transform:translateX(0); } }
    ._trace-panel  { animation: _traceSlideIn 0.18s cubic-bezier(.22,1,.36,1) forwards; }
    ._trace-empty  { animation: _traceFadeUp  0.3s  cubic-bezier(.22,1,.36,1) forwards; }
    .react-flow__controls { border-radius:8px!important; box-shadow:none!important; overflow:hidden; }
    .react-flow__controls button { border-bottom:none!important; transition:background 0.15s; }
    .react-flow__attribution { display:none!important; }
    .react-flow__handle { pointer-events:none!important; }
  `;
  document.head.appendChild(el);
}

// ═══════════════════════════════════════════════════════════════════
// § 9  UI — SpanNode  (memoised to avoid re-renders from parent)
// ═══════════════════════════════════════════════════════════════════

const SpanNode = memo(function SpanNode({ data }: NodeProps<SpanNodeData>) {
  const { span, isSelected, theme, serviceHue: hue, onSelectRef } = data;
  const t = tok(theme);
  const [hovered, setHovered] = useState(false);

  const accent = accentForHue(hue, theme);
  const statusColor = span.status === 'error' ? t.error : span.status === 'ok' ? t.ok : t.unset;
  const border = isSelected
    ? t.nodeBorderSelected
    : hovered
    ? t.nodeBorderHover
    : t.nodeBorder;
  const bg = isSelected ? t.nodeBgSelected : hovered ? t.nodeBgHover : t.nodeBg;
  const shadow = isSelected
    ? `0 0 0 3px ${t.nodeBorderSelected}33, ${t.shadow2}`
    : hovered
    ? t.shadow2
    : t.shadow1;

  return (
    <>
      <Handle
        type="target"
        position={Position.Left}
        style={{ opacity: 0, width: 1, height: 1, minWidth: 0, minHeight: 0, pointerEvents: 'none' }}
      />

      <div
        onClick={() => onSelectRef.current(span.span_id)}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        style={{
          width: NW,
          height: NH,
          display: 'flex',
          alignItems: 'stretch',
          background: bg,
          border: `1.5px solid ${border}`,
          borderRadius: 8,
          cursor: 'pointer',
          boxShadow: shadow,
          transition: 'background 0.12s, border-color 0.12s, box-shadow 0.12s, transform 0.12s',
          transform: hovered && !isSelected ? 'translateY(-1.5px)' : 'none',
          overflow: 'hidden',
          fontFamily: "'JetBrains Mono','Fira Code','Cascadia Code',monospace",
          userSelect: 'none',
          position: 'relative',
        }}
      >
        {/* Left accent bar */}
        <div style={{ width: 3, background: accent, flexShrink: 0 }} />

        {/* Main content */}
        <div style={{ flex: 1, overflow: 'hidden', padding: '0 9px', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 3 }}>
          <div
            title={span.service_name}
            style={{ fontSize: 11, fontWeight: 700, color: t.text, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', lineHeight: 1.2 }}
          >
            {span.service_name}
          </div>
          <div
            title={span.operation_name}
            style={{ fontSize: 9, color: t.textMuted, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', lineHeight: 1.2 }}
          >
            {span.operation_name}
          </div>
        </div>

        {/* Right meta */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', justifyContent: 'center', gap: 4, paddingRight: 9, flexShrink: 0 }}>
          <div
            title={`Status: ${span.status}`}
            style={{ width: 7, height: 7, borderRadius: '50%', background: statusColor, boxShadow: `0 0 0 2px ${statusColor}33` }}
          />
          <div style={{ fontSize: 8, color: t.textMuted, fontVariantNumeric: 'tabular-nums', letterSpacing: '-0.01em' }}>
            {fmtMs(span.duration_ms)}
          </div>
        </div>

        {/* Selected ring inner glow */}
        {isSelected && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              borderRadius: 7,
              background: `${t.nodeBorderSelected}08`,
              pointerEvents: 'none',
            }}
          />
        )}
      </div>

      <Handle
        type="source"
        position={Position.Right}
        style={{ opacity: 0, width: 1, height: 1, minWidth: 0, minHeight: 0, pointerEvents: 'none' }}
      />
    </>
  );
});

// ═══════════════════════════════════════════════════════════════════
// § 10  UI — TraceEdge
// ═══════════════════════════════════════════════════════════════════

const TraceEdge = memo(function TraceEdge({
  id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition,
  data,
}: EdgeProps<{ color: string }>) {
  const [path] = getBezierPath({ sourceX, sourceY, sourcePosition, targetX, targetY, targetPosition });
  return (
    <path
      id={id}
      d={path}
      style={{ stroke: data?.color ?? '#2d333b', strokeWidth: 1.5, fill: 'none', opacity: 0.5 }}
    />
  );
});

// ═══════════════════════════════════════════════════════════════════
// § 11  UI — Detail Panel
// ═══════════════════════════════════════════════════════════════════

const DetailPanel = memo(function DetailPanel({
  span, onClose, theme,
}: { span: Span; onClose: () => void; theme: Theme }) {
  const t = tok(theme);
  const hue = serviceHue(span.service_name);
  const accent = accentForHue(hue, theme);
  const statusColor = span.status === 'error' ? t.error : span.status === 'ok' ? t.ok : t.unset;

  const fields: Array<{ label: string; value: string; color?: string }> = [
    { label: 'Span ID', value: span.span_id },
    { label: 'Trace ID', value: span.trace_id },
    { label: 'Service', value: span.service_name },
    { label: 'Operation', value: span.operation_name },
    { label: 'Status', value: span.status, color: statusColor },
    { label: 'Duration', value: fmtMs(span.duration_ms) },
    { label: 'Parent', value: span.parent_span_id ?? '—' },
  ];

  const attrs = span.attributes ? Object.entries(span.attributes) : [];

  return (
    <div
      className="_trace-panel"
      style={{
        position: 'absolute',
        top: 12,
        right: 12,
        width: 308,
        maxHeight: 'calc(100% - 24px)',
        background: t.panelBg,
        border: `1px solid ${t.panelBorder}`,
        borderRadius: 10,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        boxShadow: t.shadow3,
        zIndex: 30,
        fontFamily: "'JetBrains Mono','Fira Code',monospace",
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '11px 13px', borderBottom: `1px solid ${t.panelBorder}`, background: `${accent}12`, flexShrink: 0 }}>
        <div style={{ width: 9, height: 9, borderRadius: '50%', background: accent, boxShadow: `0 0 0 2px ${accent}44` }} />
        <span style={{ flex: 1, fontSize: 9.5, fontWeight: 800, color: t.text, letterSpacing: '0.09em' }}>SPAN DETAIL</span>
        <button
          onClick={onClose}
          style={{ background: 'none', border: 'none', color: t.textMuted, cursor: 'pointer', fontSize: 14, lineHeight: 1, padding: '2px 3px', borderRadius: 4, display: 'flex', alignItems: 'center' }}
          title="Close"
        >
          ×
        </button>
      </div>

      {/* Body */}
      <div
        style={{ overflowY: 'auto', flex: 1, scrollbarWidth: 'thin', scrollbarColor: `${t.scrollbar} transparent` }}
      >
        <div style={{ padding: '6px 0 4px' }}>
          {fields.map(f => (
            <div
              key={f.label}
              style={{ display: 'grid', gridTemplateColumns: '76px 1fr', columnGap: 8, padding: '5px 13px', alignItems: 'start' }}
            >
              <span style={{ fontSize: 8, color: t.textMuted, letterSpacing: '0.08em', paddingTop: 1.5, textTransform: 'uppercase' }}>
                {f.label}
              </span>
              <span style={{ fontSize: 10, color: f.color ?? t.text, wordBreak: 'break-all', fontWeight: f.color ? 600 : 400, lineHeight: 1.45 }}>
                {f.value}
              </span>
            </div>
          ))}
        </div>

        {attrs.length > 0 && (
          <>
            <div style={{ margin: '4px 13px 0', padding: '8px 0 4px', borderTop: `1px solid ${t.panelBorder}`, fontSize: 8, color: t.textMuted, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              Attributes
            </div>
            {attrs.map(([k, v]) => (
              <div
                key={k}
                style={{ display: 'grid', gridTemplateColumns: '76px 1fr', columnGap: 8, padding: '4px 13px', alignItems: 'start' }}
              >
                <span style={{ fontSize: 8.5, color: t.textMuted, wordBreak: 'break-all' }}>{k}</span>
                <span style={{ fontSize: 9.5, color: t.text, wordBreak: 'break-all' }}>{String(v ?? '')}</span>
              </div>
            ))}
          </>
        )}

        <div style={{ height: 10 }} />
      </div>
    </div>
  );
});

// ═══════════════════════════════════════════════════════════════════
// § 12  UI — Stat Chip
// ═══════════════════════════════════════════════════════════════════

const StatChip = memo(function StatChip({ label, value, theme, color }: { label: string; value: string; theme: Theme; color?: string }) {
  const t = tok(theme);
  return (
    <div style={{ background: t.chipBg, border: `1px solid ${t.chipBorder}`, borderRadius: 7, padding: '5px 11px', fontFamily: "'JetBrains Mono',monospace" }}>
      <div style={{ fontSize: 7.5, color: t.textMuted, letterSpacing: '0.1em', textTransform: 'uppercase' }}>{label}</div>
      <div style={{ fontSize: 13, color: color ?? t.text, fontWeight: 700, lineHeight: 1.35, letterSpacing: '-0.02em' }}>{value}</div>
    </div>
  );
});

// ═══════════════════════════════════════════════════════════════════
// § 13  UI — Loading / Empty / Toggle
// ═══════════════════════════════════════════════════════════════════

function LoadingOverlay({ theme }: { theme: Theme }) {
  const t = tok(theme);
  return (
    <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 14, zIndex: 50, background: `${t.bg}e0`, backdropFilter: 'blur(3px)' }}>
      <div style={{ width: 28, height: 28, border: `2px solid ${t.panelBorder}`, borderTopColor: t.accent, borderRadius: '50%', animation: '_traceSpin 0.75s linear infinite' }} />
      <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: t.textMuted, letterSpacing: '0.1em' }}>COMPUTING LAYOUT</span>
    </div>
  );
}

function EmptyState({ theme }: { theme: Theme }) {
  const t = tok(theme);
  return (
    <div className="_trace-empty" style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 10, fontFamily: "'JetBrains Mono',monospace", pointerEvents: 'none' }}>
      <svg width="40" height="40" viewBox="0 0 40 40" fill="none" style={{ opacity: 0.15 }}>
        <circle cx="20" cy="20" r="18" stroke={t.text} strokeWidth="1.5" strokeDasharray="4 3" />
        <circle cx="20" cy="20" r="3" fill={t.text} />
      </svg>
      <div style={{ fontSize: 11, color: t.textMuted, letterSpacing: '0.08em' }}>NO TRACE DATA</div>
      <div style={{ fontSize: 9, color: t.textFaint }}>Pass a non-empty spans array</div>
    </div>
  );
}

function ThemeToggleBtn({ theme, onToggle }: { theme: Theme; onToggle: () => void }) {
  const t = tok(theme);
  return (
    <button
      onClick={onToggle}
      style={{ background: t.chipBg, border: `1px solid ${t.chipBorder}`, borderRadius: 7, padding: '6px 11px', fontFamily: "'JetBrains Mono',monospace", fontSize: 9, letterSpacing: '0.08em', color: t.text, cursor: 'pointer', lineHeight: 1.5 }}
    >
      {theme === 'dark' ? '☀ LIGHT' : '⏾ DARK'}
    </button>
  );
}

// ═══════════════════════════════════════════════════════════════════
// § 14  STABLE TYPE MAPS  (module-level — never recreated)
// ═══════════════════════════════════════════════════════════════════

const NODE_TYPES = { spanNode: SpanNode } as const;
const EDGE_TYPES = { traceEdge: TraceEdge } as const;

// ═══════════════════════════════════════════════════════════════════
// § 15  INNER COMPONENT
// ═══════════════════════════════════════════════════════════════════

/**
 * Key insight for stable hooks:
 *
 *  • Layout runs ONLY when spanKey changes (i.e. when actual spans change).
 *    It does NOT run when theme or selectedId change.
 *
 *  • Theme changes → we call setNodes() with a mapper (no layout recompute).
 *
 *  • Selection changes → we call setNodes() with a targeted mapper to flip
 *    only `data.isSelected` on the two affected nodes. No layout, no edge
 *    rebuild, no fitView.
 *
 *  • `onSelectRef` is a stable ref whose `.current` we swap — so the
 *    callback reference stored inside node data never changes, meaning
 *    memoised SpanNode components are not re-rendered by a new callback.
 */
function TraceDAGInner({ spans, theme = 'dark', onThemeChange }: TraceDAGViewProps) {
  ensureCSS();

  const [rfNodes, setRfNodes, onNodesChange] = useNodesState<SpanNodeData>([]);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { fitView } = useReactFlow();

  // Refs that let callbacks read latest values without causing effect deps
  const selectedIdRef = useRef<string | null>(null);
  const themeRef = useRef<Theme>(theme);
  const spanListRef = useRef<Span[]>([]);
  const prevSpanKey = useRef('');

  // Stable callback ref — stored inside node data; never changes identity
  const onSelectRef = useRef<(id: string) => void>(() => {});

  // Keep refs in sync
  selectedIdRef.current = selectedId;
  themeRef.current = theme;

  // Wire up the stable select handler
  onSelectRef.current = useCallback(
    (id: string) => {
      const prev = selectedIdRef.current;
      const next = prev === id ? null : id;
      selectedIdRef.current = next;
      setSelectedId(next);

      // Targeted node data update — only flips isSelected, no layout
      setRfNodes(nodes =>
        nodes.map(n => {
          if (n.id === id || n.id === prev) {
            return { ...n, data: { ...n.data, isSelected: n.id === next } };
          }
          return n;
        }),
      );
    },
    [setRfNodes],
  );

  // ── Effect 1: Runs only when spans identity changes ──────────────
  useEffect(() => {
    const list = validateSpans(spans);
    const key = spansKey(list);
    if (key === prevSpanKey.current) return;
    prevSpanKey.current = key;
    spanListRef.current = list;

    if (list.length === 0) {
      setRfNodes([]);
      setRfEdges([]);
      setSelectedId(null);
      selectedIdRef.current = null;
      return;
    }

    setLoading(true);
    const layout = computeLayout(list);
    const nodes = makeNodes(list, layout, themeRef.current, onSelectRef);
    const edges = makeEdges(list, themeRef.current);
    setRfNodes(nodes);
    setRfEdges(edges);
    setSelectedId(null);
    selectedIdRef.current = null;
    setLoading(false);

    setTimeout(() => fitView(FVO), 60);
  }, [spans, setRfNodes, setRfEdges, fitView]); // onSelectRef is a ref — not a dep

  // ── Effect 2: Runs only when theme changes ───────────────────────
  useEffect(() => {
    if (spanListRef.current.length === 0) return;
    const t = tok(theme);
    // Update node theme token + edge colors without recomputing layout
    setRfNodes(nodes =>
      nodes.map(n => ({ ...n, data: { ...n.data, theme } })),
    );
    setRfEdges(edges =>
      edges.map(e => ({ ...e, data: { ...e.data, color: t.edgeColor } })),
    );
  }, [theme, setRfNodes, setRfEdges]);

  const spanList = validateSpans(spans);
  const stats = useMemo(() => computeStats(spanList), [spanList]);
  const selectedSpan = useMemo(
    () => (selectedId ? spanList.find(s => s.span_id === selectedId) ?? null : null),
    [selectedId, spanList],
  );
  const t = tok(theme);
  const panelOpen = selectedSpan !== null;

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative', background: t.bg, overflow: 'hidden', borderRadius: 'inherit' }}>
      {loading && <LoadingOverlay theme={theme} />}
      {spanList.length === 0 && !loading && <EmptyState theme={theme} />}

      {/* Top-left stat bar */}
      <div style={{ position: 'absolute', top: 12, left: 12, zIndex: 20, display: 'flex', gap: 6, flexWrap: 'wrap', pointerEvents: 'none' }}>
        <StatChip label="Spans" value={String(stats.spanCount)} theme={theme} />
        <StatChip label="Services" value={String(stats.serviceCount)} theme={theme} />
        <StatChip label="Depth" value={String(stats.maxDepth)} theme={theme} />
        <StatChip label="Total" value={fmtMs(stats.totalDurationMs)} theme={theme} />
        {stats.errorCount > 0 && (
          <StatChip label="Errors" value={String(stats.errorCount)} theme={theme} color={t.error} />
        )}
      </div>

      {/* Top-right theme toggle (shifts left when panel is open) */}
      <div
        style={{
          position: 'absolute',
          top: 12,
          right: panelOpen ? 332 : 12,
          zIndex: 20,
          transition: 'right 0.22s cubic-bezier(.22,1,.36,1)',
        }}
      >
        <ThemeToggleBtn
          theme={theme}
          onToggle={() => onThemeChange?.(theme === 'dark' ? 'light' : 'dark')}
        />
      </div>

      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={NODE_TYPES}
        edgeTypes={EDGE_TYPES}
        fitView
        fitViewOptions={FVO}
        minZoom={0.04}
        maxZoom={2.5}
        style={{ background: 'transparent', width: '100%', height: '100%' }}
        proOptions={{ hideAttribution: true }}
        nodesDraggable
        nodesConnectable={false}
        elementsSelectable={false}
        panOnScroll={false}
        onPaneClick={() => {
          if (selectedIdRef.current === null) return;
          const prev = selectedIdRef.current;
          setSelectedId(null);
          selectedIdRef.current = null;
          setRfNodes(nodes =>
            nodes.map(n =>
              n.id === prev ? { ...n, data: { ...n.data, isSelected: false } } : n,
            ),
          );
        }}
        deleteKeyCode={null}
        selectionKeyCode={null}
      >
        <Background variant={BackgroundVariant.Dots} gap={22} size={1} color={t.grid} />
        <Controls
          style={{ background: t.ctrlBg, border: `1px solid ${t.ctrlBorder}`, borderRadius: 8, bottom: 12, left: 12 }}
          showInteractive={false}
        />
      </ReactFlow>

      {selectedSpan && (
        <DetailPanel
          span={selectedSpan}
          onClose={() => {
            const prev = selectedIdRef.current;
            setSelectedId(null);
            selectedIdRef.current = null;
            if (prev) {
              setRfNodes(nodes =>
                nodes.map(n =>
                  n.id === prev ? { ...n, data: { ...n.data, isSelected: false } } : n,
                ),
              );
            }
          }}
          theme={theme}
        />
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// § 16  PUBLIC EXPORT
// ═══════════════════════════════════════════════════════════════════

export function TraceDAGView({ spans, theme = 'dark', onThemeChange }: TraceDAGViewProps) {
  return (
    <ReactFlowProvider>
      <TraceDAGInner spans={spans} theme={theme} onThemeChange={onThemeChange} />
    </ReactFlowProvider>
  );
}

export default TraceDAGView;