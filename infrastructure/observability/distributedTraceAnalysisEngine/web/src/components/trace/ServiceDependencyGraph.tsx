import type { Span } from '../../types/trace';

function id(v: { 0: string } | string | null | undefined) {
  if (!v) return '';
  return typeof v === 'string' ? v : v['0'];
}

export function ServiceDependencyGraph({ spans }: { spans: Span[] }) {
  const byId = new Map(spans.map(s => [id(s.span_id), s]));
  const edges = new Map<string, number>();

  spans.forEach(span => {
    const parent = byId.get(id(span.parent_span_id));
    if (!parent || parent.service_name === span.service_name) return;
    const key = `${parent.service_name} -> ${span.service_name}`;
    edges.set(key, (edges.get(key) ?? 0) + 1);
  });

  return (
    <section>
      <h3>Service Dependency Graph</h3>
      <ul>
        {Array.from(edges.entries()).map(([edge, count]) => (
          <li key={edge}>
            {edge}: {count}
          </li>
        ))}
      </ul>
    </section>
  );
}
