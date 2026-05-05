import { Span } from '../../../types/trace';
import { LayoutPosition, PerformanceMetrics, TraceStats } from '../types/traceTypes';
import { ITraceCacheRepository } from '../repositories/traceCacheRepository';

// Layout service interface (Port)
export interface ILayoutService {
  computeLayout(spans: Span[], useCache?: boolean): Map<string, LayoutPosition>;
  getPerformanceMetrics(): PerformanceMetrics | null;
  clearCache(): void;
}

// Layout service implementation
export class LayoutService implements ILayoutService {
  private performanceMetrics: PerformanceMetrics | null = null;

  constructor(private cacheRepository: ITraceCacheRepository) {}

  computeLayout(spans: Span[], useCache = true): Map<string, LayoutPosition> {
    const cacheKey = this.generateCacheKey(spans);
    
    if (useCache) {
      const cached = this.cacheRepository.getLayoutPositions(cacheKey);
      if (cached) {
        return cached;
      }
    }

    const startTime = performance.now();
    
    // Build parent-child relationships
    const parentMap = new Map<string, string>();
    const childrenMap = new Map<string, string[]>();
    
    spans.forEach(span => {
      if (span.parent_span_id) {
        parentMap.set(span.span_id, span.parent_span_id);
        const children = childrenMap.get(span.parent_span_id) || [];
        children.push(span.span_id);
        childrenMap.set(span.parent_span_id, children);
      }
    });

    // Calculate depth for each span
    const depthMap = new Map<string, number>();
    const calculateDepth = (spanId: string, depth = 0): number => {
      if (depthMap.has(spanId)) return depthMap.get(spanId)!;
      
      const parentId = parentMap.get(spanId);
      if (!parentId) {
        depthMap.set(spanId, 0);
        return 0;
      }
      
      const parentDepth = calculateDepth(parentId, depth + 1);
      depthMap.set(spanId, parentDepth + 1);
      return parentDepth + 1;
    };

    spans.forEach(span => calculateDepth(span.span_id));

    // Group spans by depth
    const columns = new Map<number, string[]>();
    spans.forEach(span => {
      const depth = depthMap.get(span.span_id) || 0;
      const columnSpans = columns.get(depth) || [];
      columnSpans.push(span.span_id);
      columns.set(depth, columnSpans);
    });

    // Proper spacing to prevent overlap
    const COL_W = 200; // Fixed column width for proper spacing
    const ROW_H = 80;  // Fixed row height for proper spacing
    const positions = new Map<string, LayoutPosition>();

    // Assign positions
    let maxCol = 0;
    columns.forEach((spanIds, depth) => {
      maxCol = Math.max(maxCol, depth);
      spanIds.forEach((spanId, index) => {
        positions.set(spanId, {
          x: depth * COL_W,
          y: index * ROW_H,
        });
      });
    });

    const endTime = performance.now();
    
    // Cache the result
    if (useCache) {
      this.cacheRepository.setLayoutPositions(cacheKey, positions);
    }

    // Store performance metrics
    this.performanceMetrics = {
      layoutTime: endTime - startTime,
      renderTime: 0, // Will be set by the component
    };

    return positions;
  }

  getPerformanceMetrics(): PerformanceMetrics | null {
    return this.performanceMetrics;
  }

  clearCache(): void {
    this.cacheRepository.clear();
  }

  private generateCacheKey(spans: Span[]): string {
    // Create a deterministic cache key based on span IDs and their relationships
    const spanIds = spans.map(s => s.span_id).sort();
    const relationships = spans.map(s => `${s.span_id}:${s.parent_span_id || ''}`).sort();
    return `${spanIds.join('|')}-${relationships.join('|')}`;
  }
}

