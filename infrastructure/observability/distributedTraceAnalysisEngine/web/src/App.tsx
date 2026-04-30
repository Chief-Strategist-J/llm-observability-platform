import { HealthStatusBar } from './components/HealthStatusBar';
import { FlushTriggerPanel } from './components/FlushTriggerPanel';
import { TraceListTable } from './components/TraceListTable';
import { api } from './lib/api';
import { usePolling } from './hooks';
import { TraceWaterfallView } from './components/trace/TraceWaterfallView';
import { CriticalPathOverlay } from './components/trace/CriticalPathOverlay';
import { ServiceDependencyGraph } from './components/trace/ServiceDependencyGraph';
import { AnomalyScorePanel } from './components/anomaly/AnomalyScorePanel';
import { ClusterDistributionChart } from './components/charts/ClusterDistributionChart';
import { LatencyHistogram } from './components/charts/LatencyHistogram';
import { useState } from 'react';

const panel = { background: '#fff', border: '1px solid #dde4dd', borderRadius: 8, padding: 12 };

export function App() {
  const [selectedTraceId, setSelectedTraceId] = useState<string | undefined>();
  const [histogramBins, setHistogramBins] = useState(20);
  const { data: resultsData, error: resultsError } = usePolling(() => api.results(200, 0), 5_000);
  const { data: traceData } = usePolling(() => api.traceById(selectedTraceId!), 5_000, !!selectedTraceId);
  const { data: selectedResult } = usePolling(() => api.resultByTrace(selectedTraceId!), 5_000, !!selectedTraceId);

  return (
    <div style={{ fontFamily: 'Inter, sans-serif', height: '100vh', overflow: 'hidden', background: '#f4fbf4' }}>
      <header style={{ height: 56, borderBottom: '1px solid #dde4dd', background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 16px' }}>
        <strong>DTAE Ops</strong>
        <input placeholder="Search traces, services..." style={{ width: 280, border: '1px solid #bbcabf', borderRadius: 6, padding: '6px 10px' }} />
      </header>
      <div style={{ display: 'flex', height: 'calc(100vh - 56px)' }}>
        <aside style={{ width: 240, borderRight: '1px solid #dde4dd', padding: 12, background: '#eef6ee' }}>
          <div style={{ fontSize: 12, color: '#3c4a42', marginBottom: 12 }}>Enterprise Observability</div>
          <div>Dashboard</div><div>Services</div><div><b>Traces</b></div><div>Clusters</div><div>Incidents</div>
        </aside>
        <main style={{ flex: 1, overflow: 'auto', padding: 16, display: 'grid', gap: 12 }}>
          <HealthStatusBar />
          <div style={panel}><FlushTriggerPanel /></div>
          <div style={panel}><h2>Recent Traces</h2>{resultsError ? <p style={{ color: '#b91c1c' }}>{resultsError}</p> : null}<TraceListTable onSelectTrace={setSelectedTraceId} /></div>
          <div style={panel}><h2>Trace Details {selectedTraceId ? `· ${selectedTraceId}` : ''}</h2><TraceWaterfallView spans={traceData?.spans ?? []} /><CriticalPathOverlay result={selectedResult} /><ServiceDependencyGraph spans={traceData?.spans ?? []} /><AnomalyScorePanel result={selectedResult} /></div>
          <div style={panel}><h2>Cluster & Latency Overview</h2><ClusterDistributionChart results={resultsData?.results ?? []} /><label>Histogram bins: <input type="number" value={histogramBins} min={5} max={100} onChange={(e: any) => setHistogramBins(Number(e.target.value || 20))} /></label><LatencyHistogram results={resultsData?.results ?? []} bins={histogramBins} /></div>
        </main>
      </div>
    </div>
  );
}
