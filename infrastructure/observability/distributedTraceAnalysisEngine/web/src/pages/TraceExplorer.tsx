import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api';
import { usePolling } from '../hooks';
import { TraceListTable } from '../components/traces/TraceListTable';
import { TraceDAGView } from '../components/traces/TraceDAGView';
import { TraceWaterfallView } from '../components/traces/TraceWaterfallView';
import { AnomalyExplanation } from '../components/traces/AnomalyExplanation';
import { Trace, AnalysisResult } from '../types/trace';
import { API_CONFIG, ANOMALY_THRESHOLDS, ANOMALY_COLORS } from '../constants/api';
import { validateNonEmptyString } from '../utils/validation';

type Tab = 'dag' | 'waterfall' | 'anomaly';

export function TraceExplorer() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedTraceId = searchParams.get('trace');

  const [selectedTrace, setSelectedTrace] = useState<Trace | null>(null);
  const [selectedResult, setSelectedResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('dag');

  // ✅ FIX: destructure `data` so TraceListTable can receive the trace list
  const { data: traceListData, loading: tracesLoading } = usePolling(
    () => api.results(API_CONFIG.TRACE_LIST_LIMIT, API_CONFIG.DEFAULT_OFFSET),
    API_CONFIG.POLLING_INTERVAL_MS
  );

  const { data: traceData, loading: traceLoading } = usePolling(
    () =>
      selectedTraceId
        ? api.traceById(selectedTraceId)
        : Promise.resolve({ trace_id: '', spans: [] } as Trace),
    API_CONFIG.POLLING_INTERVAL_MS,
    !!selectedTraceId
  );

  const { data: resultData } = usePolling(
    () =>
      selectedTraceId
        ? api.resultByTrace(selectedTraceId)
        : Promise.resolve(undefined),
    API_CONFIG.POLLING_INTERVAL_MS,
    !!selectedTraceId
  );

  useEffect(() => {
    if (traceData?.trace_id) setSelectedTrace(traceData);
  }, [traceData]);

  useEffect(() => {
    if (resultData) setSelectedResult(resultData);
  }, [resultData]);

  // Reset tab when a new trace is selected
  useEffect(() => {
    setActiveTab('dag');
    setSelectedTrace(null);
    setSelectedResult(null);
  }, [selectedTraceId]);

  const handleTraceSelect = useCallback((traceId: string) => {
    try {
      const validated = validateNonEmptyString(traceId);
      setSearchParams({ trace: validated });
    } catch {
      setError('Invalid trace ID selected');
    }
  }, [setSearchParams]);

  const getAnomalyScore = (result: AnalysisResult | null): number => {
    if (!result || typeof result.confidence !== 'number') return 0;
    return result.confidence;
  };

  const getAnomalyColor = (score: number) => {
    if (score >= ANOMALY_THRESHOLDS.HIGH) return ANOMALY_COLORS.HIGH;
    if (score >= ANOMALY_THRESHOLDS.MEDIUM) return ANOMALY_COLORS.MEDIUM;
    return ANOMALY_COLORS.LOW;
  };

  const getAnomalyLabel = (score: number) => {
    if (score >= ANOMALY_THRESHOLDS.HIGH) return 'High anomaly';
    if (score >= ANOMALY_THRESHOLDS.MEDIUM) return 'Medium anomaly';
    return 'Normal';
  };

  const anomalyScore = getAnomalyScore(selectedResult);
  const showAnomaly = !!selectedResult && anomalyScore > 0.3;

  const tabStyle = (tab: Tab): React.CSSProperties => ({
    flex: 1,
    textAlign: 'center',
    fontSize: '12px',
    padding: '5px 8px',
    borderRadius: 6,
    cursor: 'pointer',
    fontWeight: activeTab === tab ? 500 : 400,
    color: activeTab === tab
      ? 'var(--color-text-primary, #1f2937)'
      : 'var(--color-text-secondary, #6b7280)',
    background: activeTab === tab ? '#ffffff' : 'transparent',
    border: activeTab === tab ? '1px solid #e5e7eb' : 'none',
    transition: 'all 0.15s',
  });

  if (error) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center',
        height: '100vh', flexDirection: 'column', gap: 16 }}>
        <div style={{ fontSize: '16px', color: '#dc2626', fontWeight: 500 }}>
          Error loading Trace Explorer
        </div>
        <div style={{ fontSize: '13px', color: '#6b7280', textAlign: 'center' }}>{error}</div>
        <button onClick={() => setError(null)} style={{ padding: '8px 16px', background: '#3b82f6',
          color: 'white', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: '13px' }}>
          Dismiss
        </button>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Header */}
      <div style={{ background: '#ffffff', borderRadius: 12, border: '1px solid #e2e8f0',
        padding: '16px 20px', display: 'flex', alignItems: 'center',
        justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 500, color: '#1f2937' }}>
            Trace explorer
          </h2>
          <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#6b7280' }}>
            Analyze individual traces with DAG view, waterfall timeline, and anomaly explanations
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '12px',
          color: '#059669', background: '#d1fae5', padding: '4px 10px', borderRadius: 6 }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%',
            background: 'currentColor', display: 'inline-block' }} />
          Live polling
        </div>
      </div>

      {/* Main layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: 16 }}>
        {/* Trace list */}
        <div style={{ background: '#ffffff', borderRadius: 12, border: '1px solid #e2e8f0',
          padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ fontSize: '14px', fontWeight: 500, color: '#1f2937' }}>
            Recent traces
          </div>
          {tracesLoading && !traceListData ? (
            <div style={{ fontSize: '13px', color: '#9ca3af', padding: '24px 0',
              textAlign: 'center' }}>
              Loading traces...
            </div>
          ) : (
            // ✅ FIX: pass traceListData so the table actually has data
            <TraceListTable
              traces={traceListData}
              onSelectTrace={handleTraceSelect}
              selectedTraceId={selectedTraceId ?? undefined}
            />
          )}
        </div>

        {/* Detail panel */}
        <div style={{ background: '#ffffff', borderRadius: 12, border: '1px solid #e2e8f0',
          padding: 20, display: 'flex', flexDirection: 'column' }}>
          {!selectedTraceId ? (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center',
              justifyContent: 'center', flexDirection: 'column', gap: 12,
              padding: 32, textAlign: 'center', color: '#6b7280' }}>
              <div style={{ fontSize: '36px' }}>◎</div>
              <div style={{ fontSize: '15px', fontWeight: 500, color: '#374151' }}>
                No trace selected
              </div>
              <div style={{ fontSize: '13px', color: '#9ca3af', lineHeight: 1.6,
                maxWidth: 280 }}>
                Select a trace from the list to view the DAG visualization,
                waterfall timeline, and anomaly analysis.
              </div>
            </div>
          ) : (
            <>
              {/* Trace header */}
              <div style={{ display: 'flex', justifyContent: 'space-between',
                alignItems: 'flex-start', marginBottom: 16, paddingBottom: 14,
                borderBottom: '1px solid #e5e7eb' }}>
                <div>
                  <div style={{ fontSize: '15px', fontWeight: 500, color: '#1f2937' }}>
                    {selectedTraceId}
                  </div>
                  {traceData?.trace_id && (
                    <div style={{ fontSize: '12px', color: '#9ca3af',
                      fontFamily: 'monospace', marginTop: 2 }}>
                      {selectedTrace?.spans.length ?? '—'} spans
                    </div>
                  )}
                </div>
                {selectedResult && (
                  <div style={{
                    display: 'flex', alignItems: 'center', gap: 6,
                    padding: '4px 10px', borderRadius: 6,
                    fontSize: '12px', fontWeight: 500,
                    background: `${getAnomalyColor(anomalyScore)}20`,
                    color: getAnomalyColor(anomalyScore),
                  }}>
                    {getAnomalyLabel(anomalyScore)} · {anomalyScore.toFixed(2)}
                  </div>
                )}
              </div>

              {/* Tabs */}
              <div style={{ display: 'flex', gap: 2, background: '#f3f4f6',
                borderRadius: 8, padding: 3, marginBottom: 16 }}>
                {(['dag', 'waterfall', 'anomaly'] as Tab[]).map(tab => (
                  <button key={tab} onClick={() => setActiveTab(tab)}
                    style={tabStyle(tab)}>
                    {tab === 'dag' ? 'DAG view' : tab === 'waterfall' ? 'Waterfall' : 'Anomaly'}
                  </button>
                ))}
              </div>

              {/* Tab content */}
              {traceLoading ? (
                <div style={{ display: 'flex', alignItems: 'center',
                  justifyContent: 'center', height: 200, color: '#9ca3af',
                  fontSize: '13px' }}>
                  Loading trace data...
                </div>
              ) : (
                <div style={{ flex: 1, border: '1px solid #e5e7eb',
                  borderRadius: 8, background: '#fafafa', overflow: 'hidden' }}>
                  {activeTab === 'dag' && (
                    selectedTrace?.spans?.length ? (
                      <TraceDAGView spans={selectedTrace.spans} />
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center',
                        justifyContent: 'center', height: 300,
                        color: '#9ca3af', fontSize: '13px' }}>
                        No span data available
                      </div>
                    )
                  )}
                  {activeTab === 'waterfall' && (
                    selectedTrace?.spans?.length ? (
                      <TraceWaterfallView spans={selectedTrace.spans} />
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center',
                        justifyContent: 'center', height: 300,
                        color: '#9ca3af', fontSize: '13px' }}>
                        No span data available
                      </div>
                    )
                  )}
                  {activeTab === 'anomaly' && (
                    showAnomaly ? (
                      <AnomalyExplanation result={selectedResult!} />
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center',
                        justifyContent: 'center', height: 300,
                        color: '#9ca3af', fontSize: '13px' }}>
                        {selectedResult
                          ? 'No significant anomalies detected'
                          : 'No analysis result available'}
                      </div>
                    )
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}