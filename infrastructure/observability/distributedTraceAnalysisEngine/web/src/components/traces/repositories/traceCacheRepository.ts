import { CacheEntry } from '../types/traceTypes';
import { Trace, AnalysisResult } from '../../../types/trace';

// Cache repository interface (Port)
export interface ITraceCacheRepository {
  get(key: string): Trace | AnalysisResult | null;
  set(key: string, data: Trace | AnalysisResult, ttl?: number): void;
  getLayoutPositions(key: string): Map<string, import('../types/traceTypes').LayoutPosition> | null;
  setLayoutPositions(key: string, positions: Map<string, import('../types/traceTypes').LayoutPosition>, ttl?: number): void;
  clear(): void;
  size(): number;
  getStats(): { size: number; maxSize: number };
}

// Generic cache implementation with TTL and size limits
class GenericCache<T> {
  private cache = new Map<string, CacheEntry<T>>();
  private maxSize: number;
  private defaultTtl: number;

  constructor(maxSize = 100, defaultTtl = 300000) { // 5 minutes default TTL
    this.maxSize = maxSize;
    this.defaultTtl = defaultTtl;
  }

  get(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    // Check if entry has expired
    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }

  set(key: string, data: T, ttl?: number): void {
    // Remove expired entries
    this.cleanup();

    // Enforce size limit
    if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value;
      if (firstKey) {
        this.cache.delete(firstKey);
      }
    }

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl: ttl || this.defaultTtl,
    });
  }

  clear(): void {
    this.cache.clear();
  }

  size(): number {
    this.cleanup();
    return this.cache.size;
  }

  getStats(): { size: number; maxSize: number } {
    return {
      size: this.size(),
      maxSize: this.maxSize,
    };
  }

  private cleanup(): void {
    const now = Date.now();
    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > entry.ttl) {
        this.cache.delete(key);
      }
    }
  }
}

// Trace cache repository implementation
export class TraceCacheRepository implements ITraceCacheRepository {
  private layoutCache = new GenericCache<Map<string, import('../types/traceTypes').LayoutPosition>>(50, 300000);
  private traceCache = new GenericCache<Trace>(100, 300000);
  private analysisCache = new GenericCache<AnalysisResult>(75, 300000);

  // Layout cache operations
  getLayoutPositions(key: string): Map<string, import('../types/traceTypes').LayoutPosition> | null {
    return this.layoutCache.get(key);
  }

  setLayoutPositions(key: string, positions: Map<string, import('../types/traceTypes').LayoutPosition>, ttl?: number): void {
    this.layoutCache.set(key, positions, ttl);
  }

  // Trace cache operations
  getTrace(key: string): Trace | null {
    return this.traceCache.get(key);
  }

  setTrace(key: string, trace: Trace, ttl?: number): void {
    this.traceCache.set(key, trace, ttl);
  }

  // Analysis cache operations
  getAnalysis(key: string): AnalysisResult | null {
    return this.analysisCache.get(key);
  }

  setAnalysis(key: string, analysis: AnalysisResult, ttl?: number): void {
    this.analysisCache.set(key, analysis, ttl);
  }

  // Generic operations for backward compatibility
  get(key: string): Trace | AnalysisResult | null {
    // Try trace cache first, then analysis cache
    const trace = this.traceCache.get(key);
    if (trace) return trace;
    
    return this.analysisCache.get(key);
  }

  set(key: string, data: Trace | AnalysisResult, ttl?: number): void {
    // Type-safe discrimination - eliminates CoT coupling
    if (this.isTrace(data)) {
      this.setTrace(key, data, ttl);
    } else {
      this.setAnalysis(key, data, ttl);
    }
  }

  private isTrace(data: Trace | AnalysisResult): data is Trace {
    return 'trace_id' in data && 'spans' in data;
  }

  clear(): void {
    this.layoutCache.clear();
    this.traceCache.clear();
    this.analysisCache.clear();
  }

  size(): number {
    return this.layoutCache.size() + this.traceCache.size() + this.analysisCache.size();
  }

  getStats(): { size: number; maxSize: number } {
    return {
      size: this.size(),
      maxSize: this.layoutCache.getStats().maxSize + this.traceCache.getStats().maxSize + this.analysisCache.getStats().maxSize,
    };
  }
}

