import { Span } from '../../../types/trace';
import { Node } from 'reactflow';
import { LayoutPosition } from '../types/traceTypes';
import { Theme } from '../TraceDAGView.themes';
import { getTheme } from '../TraceDAGView.themes';

// Node creation service interface (Port)
export interface INodeCreationService {
  createReactFlowNodes(
    spans: Span[],
    positions: Map<string, LayoutPosition>,
    selectedSpanId: string | null,
    onSelect: (span: Span) => void,
    theme: Theme
  ): Node[];
}

// Node creation service implementation
export class NodeCreationService implements INodeCreationService {
  createReactFlowNodes(
    spans: Span[],
    positions: Map<string, LayoutPosition>,
    selectedSpanId: string | null,
    onSelect: (span: Span) => void,
    theme: Theme
  ): Node[] {
    const colors = getTheme(theme);
    
    return spans.map(span => {
      const position = positions.get(span.span_id);
      if (!position) return null;

      const serviceHue = this.getServiceHue(span.service_name);
      const isRoot = !span.parent_span_id;

      return {
        id: span.span_id,
        type: 'custom',
        position,
        data: {
          span,
          isRoot,
          depth: 0,
          selected: selectedSpanId === span.span_id,
          onSelect,
          theme,
          serviceHue,
        },
      };
    }).filter((node): node is NonNullable<typeof node> => node !== null);
  }

  private getServiceHue(serviceName: string): number {
    let hash = 0;
    for (let i = 0; i < serviceName.length; i++) {
      hash = serviceName.charCodeAt(i) + ((hash << 5) - hash);
    }
    return Math.abs(hash % 360);
  }
}
