import { Span } from '../../../types/trace';
import { IFormattingService } from './formattingService';

// Trace stats interface
export interface TraceStats {
  spanCount: number;
  rootCount: number;
  totalDuration: number;
}

// Trace stats service interface (Port)
export interface ITraceStatsService {
  calculateStats(spans: Span[]): TraceStats;
}

// Trace stats service implementation
export class TraceStatsService implements ITraceStatsService {
  calculateStats(spans: Span[]): TraceStats {
    const spanCount = spans.length;
    const rootCount = spans.filter(span => !span.parent_span_id).length;
    const totalDuration = spans.reduce((sum, span) => sum + span.duration_ns, 0);
    
    return {
      spanCount,
      rootCount,
      totalDuration
    };
  }
}
