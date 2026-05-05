import { Trace, AnalysisResult } from '../../../types/trace';

// Tab type definition
export type Tab = 'dag' | 'waterfall' | 'anomaly';

// Trace list data type (using AnalysisResult structure)
export interface TraceListItem extends AnalysisResult {}

// State interface for trace explorer
export interface TraceExplorerState {
  // Selection state
  selectedTraceId: string | null;
  selectedTrace: Trace | null;
  selectedResult: AnalysisResult | null;
  
  // UI state
  activeTab: Tab;
  error: string | null;
  
  // Loading states
  tracesLoading: boolean;
  traceLoading: boolean;
  
  // Data
  traceListData: TraceListItem[];
  traceData: Trace | null;
  resultData: AnalysisResult | null;
}

// Action types for state management
export type TraceExplorerAction =
  | { type: 'SET_SELECTED_TRACE_ID'; payload: string | null }
  | { type: 'SET_SELECTED_TRACE'; payload: Trace | null }
  | { type: 'SET_SELECTED_RESULT'; payload: AnalysisResult | null }
  | { type: 'SET_ACTIVE_TAB'; payload: Tab }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_TRACES_LOADING'; payload: boolean }
  | { type: 'SET_TRACE_LOADING'; payload: boolean }
  | { type: 'SET_TRACE_LIST_DATA'; payload: TraceListItem[] }
  | { type: 'SET_TRACE_DATA'; payload: Trace | null }
  | { type: 'SET_RESULT_DATA'; payload: AnalysisResult | null }
  | { type: 'RESET_TRACE_SELECTION' };

// Initial state
export const initialTraceExplorerState: TraceExplorerState = {
  selectedTraceId: null,
  selectedTrace: null,
  selectedResult: null,
  activeTab: 'dag',
  error: null,
  tracesLoading: false,
  traceLoading: false,
  traceListData: [],
  traceData: null,
  resultData: null,
};

// State reducer
export function traceExplorerReducer(
  state: TraceExplorerState,
  action: TraceExplorerAction
): TraceExplorerState {
  switch (action.type) {
    case 'SET_SELECTED_TRACE_ID':
      return { ...state, selectedTraceId: action.payload };
    
    case 'SET_SELECTED_TRACE':
      return { ...state, selectedTrace: action.payload };
    
    case 'SET_SELECTED_RESULT':
      return { ...state, selectedResult: action.payload };
    
    case 'SET_ACTIVE_TAB':
      return { ...state, activeTab: action.payload };
    
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    
    case 'SET_TRACES_LOADING':
      return { ...state, tracesLoading: action.payload };
    
    case 'SET_TRACE_LOADING':
      return { ...state, traceLoading: action.payload };
    
    case 'SET_TRACE_LIST_DATA':
      return { ...state, traceListData: action.payload };
    
    case 'SET_TRACE_DATA':
      return { ...state, traceData: action.payload };
    
    case 'SET_RESULT_DATA':
      return { ...state, resultData: action.payload };
    
    case 'RESET_TRACE_SELECTION':
      return {
        ...state,
        activeTab: 'dag',
        selectedTrace: null,
        selectedResult: null,
      };
    
    default:
      return state;
  }
}

// State management hooks
export function createTraceExplorerStore() {
  let state = initialTraceExplorerState;
  let listeners: Array<(state: TraceExplorerState) => void> = [];

  const subscribe = (listener: (state: TraceExplorerState) => void) => {
    listeners.push(listener);
    return () => {
      listeners = listeners.filter(l => l !== listener);
    };
  };

  const dispatch = (action: TraceExplorerAction) => {
    state = traceExplorerReducer(state, action);
    listeners.forEach(listener => listener(state));
  };

  const getState = () => state;

  return {
    subscribe,
    dispatch,
    getState,
  };
}

// Default store instance for backward compatibility
export const traceExplorerStore = createTraceExplorerStore();

