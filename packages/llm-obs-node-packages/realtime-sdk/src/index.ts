export interface Subscription<T> {
  unsubscribe: () => void;
}

export class RealtimeClient {
  private wsUrl: string;

  constructor(wsUrl: string = 'ws://localhost:8000/realtime') {
    this.wsUrl = wsUrl;
  }

  /**
   * Mock SSE subscription for real-time span stream
   */
  public subscribeToSpans(onSpan: (span: any) => void): Subscription<any> {
    console.log(`[RealtimeSDK] Subscribing to spans stream at ${this.wsUrl}/spans`);
    
    // Simulate real-time stream via interval
    const interval = setInterval(() => {
      const isError = Math.random() < 0.15;
      const latency = Math.floor(50 + Math.random() * 600);
      const inputTokens = Math.floor(100 + Math.random() * 2000);
      const outputTokens = Math.floor(50 + Math.random() * 1000);
      const cost = Math.floor((inputTokens * 0.0015 + outputTokens * 0.002) * 1000); // in micro USD
      
      const mockSpan = {
        trace_id: Math.random().toString(36).substring(2, 15),
        span_id: Math.random().toString(36).substring(2, 9),
        name: Math.random() > 0.5 ? 'completion' : 'embeddings',
        start_time_ms: Date.now() - latency,
        end_time_ms: Date.now(),
        latency_ms: latency,
        status: isError ? 'error' : 'success',
        cost_usd_micro: cost,
        model: Math.random() > 0.4 ? 'gpt-4o' : 'claude-3-5-sonnet',
        quality_score: isError ? undefined : parseFloat((0.7 + Math.random() * 0.3).toFixed(2)),
        tokens_input: inputTokens,
        tokens_output: outputTokens,
        error_message: isError ? 'Rate limit exceeded on LLM provider' : undefined
      };
      
      onSpan(mockSpan);
    }, 2000);

    return {
      unsubscribe: () => {
        console.log('[RealtimeSDK] Unsubscribed from spans stream');
        clearInterval(interval);
      }
    };
  }

  /**
   * Mock WS subscription for aggregated metrics updates
   */
  public subscribeToMetrics(onMetrics: (metrics: any) => void): Subscription<any> {
    console.log(`[RealtimeSDK] Subscribing to metrics stream at ${this.wsUrl}/metrics`);
    
    const interval = setInterval(() => {
      const mockMetrics = {
        latency_p50: Math.floor(100 + Math.random() * 100),
        latency_p95: Math.floor(350 + Math.random() * 150),
        latency_p99: Math.floor(500 + Math.random() * 300),
        total_cost_usd_micro: Math.floor(10000 + Math.random() * 50000),
        avg_quality_score: parseFloat((0.8 + Math.random() * 0.15).toFixed(2)),
        total_tokens: Math.floor(500000 + Math.random() * 200000),
        span_count: Math.floor(1000 + Math.random() * 500)
      };
      onMetrics(mockMetrics);
    }, 5000);

    return {
      unsubscribe: () => {
        console.log('[RealtimeSDK] Unsubscribed from metrics stream');
        clearInterval(interval);
      }
    };
  }
}
