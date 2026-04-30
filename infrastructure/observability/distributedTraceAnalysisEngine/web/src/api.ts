import { AnalysisResult, Trace } from './types/trace';
import { API_CONFIG, HTTP_STATUS } from './constants/api';
import { validateNonEmptyString, validateNumberRange, validateApiResponse } from './utils/validation';
import { safeAsyncCall, ApiError } from './utils/errorHandling';

// Backend trace response type
interface TraceResponse {
  trace_id: string;
  span_count: number;
  status: string;
  duration_ns: number;
}

// Health check response type
interface HealthResponse {
  status: string;
  version: string;
}

// Flush response type
interface FlushResponse {
  complete_traces: number;
  partial_traces: number;
  analysis_results: number;
}

export const api = {
  async results(
    limit: number = API_CONFIG.DEFAULT_LIMIT,
    offset: number = API_CONFIG.DEFAULT_OFFSET
  ): Promise<{ results: AnalysisResult[] }> {
    return safeAsyncCall(
      async () => {
        const validatedLimit = validateNumberRange(
          limit,
          1,
          1000,
          'limit'
        );
        const validatedOffset = validateNumberRange(
          offset,
          0,
          10000,
          'offset'
        );

        const response = await fetch(
          `${API_CONFIG.BASE_URL}/analysis/results?limit=${validatedLimit}&offset=${validatedOffset}`
        );
        validateApiResponse(response);
        
        const data = await response.json();
        if (!data || typeof data !== 'object' || !('results' in data)) {
          throw new ApiError('Invalid response format: missing results property');
        }
        
        return data as { results: AnalysisResult[] };
      },
      'Failed to fetch results',
      'analysis/results'
    );
  },

  async resultByTrace(traceId: string): Promise<AnalysisResult | undefined> {
    return safeAsyncCall(
      async () => {
        const validatedTraceId = validateNonEmptyString(traceId);

        const response = await fetch(
          `${API_CONFIG.BASE_URL}/analysis/results/${validatedTraceId}`
        );
        
        if (response.status === HTTP_STATUS.NOT_FOUND) {
          return undefined;
        }
        
        validateApiResponse(response);
        return response.json();
      },
      'Failed to fetch result',
      `analysis/results/${traceId}`
    );
  },

  async traces(): Promise<TraceResponse[]> {
    return safeAsyncCall(
      async () => {
        const response = await fetch(`${API_CONFIG.BASE_URL}/traces`);
        validateApiResponse(response);
        
        const data = await response.json();
        if (!Array.isArray(data)) {
          throw new ApiError('Invalid response format: expected array of traces');
        }
        
        return data as TraceResponse[];
      },
      'Failed to fetch traces',
      'traces'
    );
  },

  async traceById(traceId: string): Promise<Trace> {
    return safeAsyncCall(
      async () => {
        const validatedTraceId = validateNonEmptyString(traceId);

        const response = await fetch(
          `${API_CONFIG.BASE_URL}/traces/${validatedTraceId}`
        );
        
        if (response.status === HTTP_STATUS.NOT_FOUND) {
          throw new ApiError(`Trace not found: ${validatedTraceId}`, HTTP_STATUS.NOT_FOUND);
        }
        
        validateApiResponse(response);
        
        const data = await response.json();
        if (!data || typeof data !== 'object' || !('trace_id' in data) || !('spans' in data)) {
          throw new ApiError('Invalid response format: missing required trace properties');
        }
        
        return data as Trace;
      },
      'Failed to fetch trace',
      `traces/${traceId}`
    );
  },

  async health(): Promise<HealthResponse> {
    return safeAsyncCall(
      async () => {
        const response = await fetch(API_CONFIG.HEALTH_URL);
        validateApiResponse(response);
        
        const data = await response.json();
        if (!data || typeof data !== 'object' || !('status' in data) || !('version' in data)) {
          throw new ApiError('Invalid health response format');
        }
        
        return data as HealthResponse;
      },
      'Failed to fetch health',
      'health'
    );
  },

  async flush(): Promise<FlushResponse> {
    return safeAsyncCall(
      async () => {
        const response = await fetch(`${API_CONFIG.BASE_URL}/flush`, { 
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        validateApiResponse(response);
        
        const data = await response.json();
        if (!data || typeof data !== 'object' || 
            !('complete_traces' in data) || 
            !('partial_traces' in data) || 
            !('analysis_results' in data)) {
          throw new ApiError('Invalid flush response format');
        }
        
        return data as FlushResponse;
      },
      'Failed to trigger flush',
      'flush'
    );
  },
};
