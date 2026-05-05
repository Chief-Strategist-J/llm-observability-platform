import { Tab, TraceExplorerState, TraceExplorerAction, traceExplorerStore } from './traceState';
import { validateNonEmptyString } from '../../../utils/validation';
import { ITraceAnalysisService } from '../services/traceAnalysisService';

// Trace Explorer Controller interface (Port)
export interface ITraceExplorerController {
  // State access
  getState(): TraceExplorerState;
  subscribe(listener: (state: TraceExplorerState) => void): () => void;
  
  // Input handling (only validation and forwarding)
  handleTraceSelect(traceId: string): void;
  handleTabChange(tab: Tab): void;
  clearError(): void;
  
  // State updates (from external data sources)
  updateTraceListData(data: import('../types/traceTypes').TraceListItem[]): void;
  updateTracesLoading(loading: boolean): void;
  updateTraceData(data: import('../../../types/trace').Trace | null): void;
  updateTraceLoading(loading: boolean): void;
  updateResultData(data: import('../../../types/trace').AnalysisResult | null): void;
  
  // Initialization
  initializeFromSearchParams(searchParams: URLSearchParams): void;
}

// Store interface for dependency injection
export interface ITraceExplorerStore {
  getState(): TraceExplorerState;
  subscribe(listener: (state: TraceExplorerState) => void): () => void;
  dispatch(action: TraceExplorerAction): void;
}

// Trace Explorer Controller implementation
export class TraceExplorerController implements ITraceExplorerController {
  constructor(
    private analysisService: ITraceAnalysisService,
    private store: ITraceExplorerStore = traceExplorerStore
  ) {}

  // Get current state
  getState(): TraceExplorerState {
    return this.store.getState();
  }

  // Subscribe to state changes
  subscribe(listener: (state: TraceExplorerState) => void): () => void {
    return this.store.subscribe(listener);
  }

  // Dispatch actions (private helper)
  private dispatch(action: TraceExplorerAction): void {
    this.store.dispatch(action);
  }

  // Handle trace selection - only validation and forwarding
  handleTraceSelect(traceId: string): void {
    try {
      const validated = validateNonEmptyString(traceId);
      this.dispatch({ type: 'SET_SELECTED_TRACE_ID', payload: validated });
      this.dispatch({ type: 'RESET_TRACE_SELECTION' });
    } catch {
      this.dispatch({ type: 'SET_ERROR', payload: 'Invalid trace ID selected' });
    }
  }

  // Handle tab change - only forwarding
  handleTabChange(tab: Tab): void {
    this.dispatch({ type: 'SET_ACTIVE_TAB', payload: tab });
  }

  // Clear error - only forwarding
  clearError(): void {
    this.dispatch({ type: 'SET_ERROR', payload: null });
  }

  // Update trace list data - only forwarding
  updateTraceListData(data: import('../types/traceTypes').TraceListItem[]): void {
    this.dispatch({ type: 'SET_TRACE_LIST_DATA', payload: data });
  }

  // Update traces loading state - only forwarding
  updateTracesLoading(loading: boolean): void {
    this.dispatch({ type: 'SET_TRACES_LOADING', payload: loading });
  }

  // Update trace data - only forwarding with minimal logic
  updateTraceData(data: import('../../../types/trace').Trace | null): void {
    this.dispatch({ type: 'SET_TRACE_DATA', payload: data });
    if (data?.trace_id) {
      this.dispatch({ type: 'SET_SELECTED_TRACE', payload: data });
    }
  }

  // Update trace loading state - only forwarding
  updateTraceLoading(loading: boolean): void {
    this.dispatch({ type: 'SET_TRACE_LOADING', payload: loading });
  }

  // Update result data - only forwarding with minimal logic
  updateResultData(data: import('../../../types/trace').AnalysisResult | null): void {
    this.dispatch({ type: 'SET_RESULT_DATA', payload: data });
    if (data) {
      this.dispatch({ type: 'SET_SELECTED_RESULT', payload: data });
    }
  }

  // Initialize from search params - only forwarding
  initializeFromSearchParams(searchParams: URLSearchParams): void {
    const traceId = searchParams.get('trace');
    if (traceId) {
      this.dispatch({ type: 'SET_SELECTED_TRACE_ID', payload: traceId });
    }
  }
}

// UI Styling service (separate from controller - Axis 7)
export interface IUIStylingService {
  getTabStyle(activeTab: Tab, currentTab: Tab): React.CSSProperties;
}

export class UIStylingService implements IUIStylingService {
  getTabStyle(activeTab: Tab, currentTab: Tab): React.CSSProperties {
    return {
      flex: 1,
      textAlign: 'center',
      fontSize: '12px',
      padding: '5px 8px',
      borderRadius: 6,
      cursor: 'pointer',
      fontWeight: activeTab === currentTab ? 500 : 400,
      color: activeTab === currentTab
        ? 'var(--color-text-primary, #1f2937)'
        : 'var(--color-text-secondary, #6b7280)',
      background: activeTab === currentTab ? '#ffffff' : 'transparent',
      border: activeTab === currentTab ? '1px solid #e5e7eb' : 'none',
      transition: 'all 0.15s',
    };
  }
}

