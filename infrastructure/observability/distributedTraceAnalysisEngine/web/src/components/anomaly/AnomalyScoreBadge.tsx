import type { AnalysisResult } from '../../types/trace';

export function AnomalyScoreBadge({ result }: { result: AnalysisResult }) {
  const isAnomaly = result.anomaly;
  return (
    <span style={{ padding: '2px 8px', borderRadius: 12, background: isAnomaly ? '#7f1d1d' : '#14532d', color: 'white', fontSize: 12 }}>
      {isAnomaly ? 'Anomalous' : 'Normal'}
    </span>
  );
}
