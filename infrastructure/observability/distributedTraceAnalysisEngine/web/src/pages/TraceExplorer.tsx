import { TraceListTable } from '../components/traces/TraceListTable';
import { TraceDAGView } from '../components/traces/TraceDAGView';
import { TraceWaterfallView } from '../components/traces/TraceWaterfallView';
import { AnomalyExplanation } from '../components/traces/AnomalyExplanation';
import { useTraceExplorer } from '../components/traces/hooks/useTraceExplorer';
import { ServiceFactory } from '../components/traces/interfaces/traceFactories';

export function TraceExplorer() {
  // Create dependencies using centralized factory (DRY Rule 10)
  const dependencies = {
    controller: ServiceFactory.createTraceExplorerController(ServiceFactory.createTraceAnalysisService()),
    analysisService: ServiceFactory.createTraceAnalysisService(),
    uiStylingService: ServiceFactory.createUIStylingService(),
  };

  const {
    state,
    handleTraceSelect,
    handleTabChange,
    clearError,
    anomalyScore,
    showAnomaly,
    getAnomalyColor,
    getAnomalyLabel,
    getTabStyle,
  } = useTraceExplorer(dependencies);

  if (state.error) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center',
        height: '100vh', flexDirection: 'column', gap: 16 }}>
        <div style={{ fontSize: '16px', color: '#dc2626', fontWeight: 500 }}>
          Error loading Trace Explorer
        </div>
        <div style={{ fontSize: '13px', color: '#6b7280', textAlign: 'center' }}>{state.error}</div>
        <button onClick={clearError} style={{ padding: '8px 16px', background: '#3b82f6',
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
      <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: 20, height: 'calc(100vh - 120px)' }}>
        {/* Trace list */}
        <div style={{ background: '#ffffff', borderRadius: 12, border: '1px solid #e2e8f0',
          padding: 20, display: 'flex', flexDirection: 'column', gap: 16, overflow: 'hidden' }}>
          <div style={{ fontSize: '16px', fontWeight: 600, color: '#1f2937', paddingBottom: 12, borderBottom: '1px solid #e5e7eb' }}>
            Recent traces
          </div>
          {state.tracesLoading && !state.traceListData.length ? (
            <div style={{ fontSize: '14px', color: '#9ca3af', padding: '32px 0',
              textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
              <div style={{ fontSize: '20px' }}>⏳</div>
              <div>Loading traces...</div>
            </div>
          ) : (
            <div style={{ flex: 1, overflow: 'auto' }}>
              <TraceListTable
                onSelectTrace={handleTraceSelect}
              />
            </div>
          )}
        </div>

        {/* Detail panel */}
        <div style={{ background: '#ffffff', borderRadius: 12, border: '1px solid #e2e8f0',
          padding: 20, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {!state.selectedTraceId ? (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center',
              justifyContent: 'center', flexDirection: 'column', gap: 12,
              padding: 32, textAlign: 'center', color: '#6b7280' }}>
              <div style={{ fontSize: '48px' }}>🔍</div>
              <div style={{ fontSize: '16px', fontWeight: 500, color: '#374151' }}>
                Select a trace to explore
              </div>
              <div style={{ fontSize: '13px' }}>
                Choose a trace from the list to view its DAG, waterfall, and analysis
              </div>
              <button 
                onClick={() => handleTraceSelect('test-trace-001')}
                style={{
                  marginTop: 16,
                  padding: '8px 16px',
                  background: '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: 6,
                  cursor: 'pointer',
                  fontSize: '13px'
                }}
              >
                Load Test Trace
              </button>
            </div>
          ) : (
            <>
              {/* Trace header */}
              <div style={{ display: 'flex', justifyContent: 'space-between',
                alignItems: 'flex-start', marginBottom: 16, paddingBottom: 14,
                borderBottom: '1px solid #e5e7eb' }}>
                <div>
                  <div style={{ fontSize: '15px', fontWeight: 500, color: '#1f2937' }}>
                    {state.selectedTraceId}
                  </div>
                  {state.selectedTrace?.trace_id && (
                    <div style={{ fontSize: '12px', color: '#9ca3af',
                      fontFamily: 'monospace', marginTop: 2 }}>
                      {state.selectedTrace?.spans.length ?? '—'} spans
                    </div>
                  )}
                </div>
                {state.selectedResult && (
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
                {(['dag', 'waterfall', 'anomaly'] as const).map(tab => (
                  <button key={tab} onClick={() => handleTabChange(tab)}
                    style={getTabStyle(state.activeTab, tab)}>
                    {tab === 'dag' ? 'DAG view' : tab === 'waterfall' ? 'Waterfall' : 'Anomaly'}
                  </button>
                ))}
              </div>

              {/* Tab content - Full Space Utilization */}
              {state.traceLoading ? (
                <div style={{ 
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  height: 'calc(100vh - 200px)', 
                  color: '#9ca3af', 
                  fontSize: '13px',
                  background: '#fafafa', 
                  border: '1px solid #e5e7eb',
                  borderRadius: 8
                }}>
                  Loading trace data...
                </div>
              ) : (
                <div style={{ 
                  width: '100%',
                  height: 'calc(100vh - 200px)', 
                  background: '#fafafa', 
                  border: '1px solid #e5e7eb',
                  borderRadius: 8,
                  overflow: 'hidden',
                  position: 'relative'
                }}>
                  {state.activeTab === 'dag' && (
                    state.selectedTrace?.spans?.length ? (
                      <TraceDAGView spans={state.selectedTrace.spans} />
                    ) : (
                      <div style={{ 
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        height: '100%', 
                        color: '#9ca3af', 
                        fontSize: '13px'
                      }}>
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: '24px', marginBottom: 8 }}>📊</div>
                          <div>No span data available</div>
                          <div style={{ fontSize: '11px', marginTop: 4 }}>
                            This trace has no spans to visualize
                          </div>
                        </div>
                      </div>
                    )
                  )}
                  {state.activeTab === 'waterfall' && (
                    state.selectedTrace?.spans?.length ? (
                      <div style={{ height: 400, padding: 16 }}>
                        <TraceWaterfallView spans={state.selectedTrace.spans} />
                      </div>
                    ) : (
                      <div style={{ 
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        height: 400, color: '#9ca3af', fontSize: '13px'
                      }}>
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: '24px', marginBottom: 8 }}>📈</div>
                          <div>No span data available</div>
                          <div style={{ fontSize: '11px', marginTop: 4 }}>
                            This trace has no spans to visualize
                          </div>
                        </div>
                      </div>
                    )
                  )}
                  {state.activeTab === 'anomaly' && (
                    showAnomaly ? (
                      <div style={{ height: 400, padding: 16, overflow: 'auto' }}>
                        <AnomalyExplanation result={state.selectedResult!} />
                      </div>
                    ) : (
                      <div style={{ 
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        height: 400, color: '#9ca3af', fontSize: '13px'
                      }}>
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: '24px', marginBottom: 8 }}>✅</div>
                          <div>
                            {state.selectedResult
                              ? 'No significant anomalies detected'
                              : 'No analysis result available'}
                          </div>
                          <div style={{ fontSize: '11px', marginTop: 4 }}>
                            {state.selectedResult 
                              ? 'This trace appears to be behaving normally'
                              : 'Analysis not yet available for this trace'}
                          </div>
                        </div>
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