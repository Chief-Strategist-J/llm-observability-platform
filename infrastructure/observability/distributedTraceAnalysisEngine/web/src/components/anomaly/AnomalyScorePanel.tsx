import type { AnalysisResult } from '../../types/trace';

export function AnomalyScorePanel({ result }: { result?: AnalysisResult }) {
  if (!result)
    return (
      <section>
        <h3>Anomaly Scores</h3>
        <p>Select a trace.</p>
      </section>
    );
  return (
    <section>
      <h3>Anomaly Scores</h3>
      <ul>
        {(result.anomaly_scores ?? []).map(score => (
          <li key={score.signal_name}>
            {score.signal_name}: {score.score.toFixed(3)} / threshold{' '}
            {score.threshold.toFixed(3)}
          </li>
        ))}
      </ul>
    </section>
  );
}
