import type { AnalysisResult } from '../../types/trace';

interface AnomalyScoreBadgeProps {
  result: AnalysisResult;
  compact?: boolean;
}

export function AnomalyScoreBadge({
  result,
  compact = false,
}: AnomalyScoreBadgeProps) {
  const isAnomaly =
    result.is_anomalous || (result.confidence && result.confidence > 0.5);

  return (
    <span
      style={{
        padding: compact ? '2px 6px' : '2px 8px',
        borderRadius: compact ? 8 : 12,
        background: isAnomaly ? '#7f1d1d' : '#14532d',
        color: 'white',
        fontSize: compact ? 10 : 12,
        fontWeight: '500',
      }}
    >
      {compact ? (isAnomaly ? 'A' : 'N') : isAnomaly ? 'Anomalous' : 'Normal'}
    </span>
  );
}
