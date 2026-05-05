import { Span, Trace, AnalysisResult } from '../../../types/trace';

// Trace list item interface
export interface TraceListItem extends AnalysisResult {}

// Layout position interface
export interface LayoutPosition {
  x: number;
  y: number;
}

// Performance metrics interface
export interface PerformanceMetrics {
  layoutTime: number;
  renderTime: number;
}

// Trace statistics interface
export interface TraceStats {
  spanCount: number;
  rootCount: number;
  maxDepth: number;
  totalDuration: number;
  avgDuration: number;
  serviceCount: number;
  uniqueServices: string[];
}

// Filter options interface
export interface FilterOptions {
  serviceFilter: string;
  minDuration: number;
  maxDuration: number;
  showErrorsOnly: boolean;
  depthRange: [number, number];
}

// Cache entry interface
export interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

// React Flow node interface
export interface ReactFlowNode {
  id: string;
  type: string;
  position: LayoutPosition;
  data: {
    label: string;
    span: Span;
    isSelected: boolean;
    theme: string;
  };
  style?: React.CSSProperties;
}

// React Flow edge interface
export interface ReactFlowEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  data?: {
    label?: string;
    theme: string;
  };
  style?: React.CSSProperties;
}
