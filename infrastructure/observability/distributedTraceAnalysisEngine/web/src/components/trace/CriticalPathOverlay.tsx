import type { AnalysisResult } from '../../types/trace';

function spanId(v: { 0: string } | string | undefined) {
  if (!v) return '';
  return typeof v === 'string' ? v : v['0'];
}

export function CriticalPathOverlay({ result }: { result?: AnalysisResult }) {
  const nodes = result?.critical_path?.nodes ?? [];
  return (
    <div>
      <h4>Critical Path Overlay</h4>
      <ul>
        {nodes.map((n) => (
          <li key={spanId(n.span_id)}>{spanId(n.span_id)} — {(n.contribution * 100).toFixed(1)}%</li>
        ))}
      </ul>
    </div>
  );
}
