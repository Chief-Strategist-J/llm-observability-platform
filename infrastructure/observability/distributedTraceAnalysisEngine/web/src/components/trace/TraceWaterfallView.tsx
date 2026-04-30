import type { Span } from '../../types/trace';

function id(v: { 0: string } | string | null | undefined) {
  if (!v) return '';
  return typeof v === 'string' ? v : v['0'];
}

export function TraceWaterfallView({ spans }: { spans: Span[] }) {
  const byParent = new Map<string, Span[]>();
  spans.forEach((s) => {
    const p = id(s.parent_span_id) || '__root__';
    byParent.set(p, [...(byParent.get(p) ?? []), s]);
  });

  const ordered: Array<{ span: Span; depth: number }> = [];
  const walk = (parent: string, depth: number) => {
    (byParent.get(parent) ?? []).forEach((s) => {
      ordered.push({ span: s, depth });
      walk(id(s.span_id), depth + 1);
    });
  };
  walk('__root__', 0);

  return (
    <section>
      <h3>Trace Waterfall View</h3>
      {ordered.map(({ span, depth }) => (
        <div key={id(span.span_id)} style={{ marginLeft: depth * 16, borderLeft: '2px solid #64748b', paddingLeft: 8, marginBottom: 4 }}>
          <strong>{span.service_name}</strong> · {span.operation_name} · {span.duration_ns} ns
        </div>
      ))}
    </section>
  );
}
