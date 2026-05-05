import { Span } from '../../../types/trace';
import { Edge } from 'reactflow';
import { Theme } from '../TraceDAGView.themes';
import { getTheme } from '../TraceDAGView.themes';

// Edge creation service interface (Port)
export interface IEdgeCreationService {
  createReactFlowEdges(spans: Span[], theme: Theme): Edge[];
}

// Edge creation service implementation
export class EdgeCreationService implements IEdgeCreationService {
  createReactFlowEdges(spans: Span[], theme: Theme): Edge[] {
    const colors = getTheme(theme);
    
    return spans
      .filter(span => span.parent_span_id)
      .map(span => ({
        id: `${span.parent_span_id}-${span.span_id}`,
        source: span.parent_span_id!,
        target: span.span_id,
        type: 'smoothstep',
        style: { stroke: colors.edge, strokeWidth: 2 },
        animated: false,
        markerEnd: {
          type: 'arrowclosed',
          color: colors.edge,
        },
      }));
  }
}
