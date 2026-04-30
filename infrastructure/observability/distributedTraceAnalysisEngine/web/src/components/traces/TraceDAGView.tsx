import { useEffect } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Position,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Span } from '../../types/trace';

interface TraceDAGViewProps {
  spans: Span[];
}

export function TraceDAGView({ spans }: TraceDAGViewProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    if (!spans || spans.length === 0) return;

    // Build nodes and edges from spans
    const nodeMap = new Map<string, Node>();
    const edgeList: Edge[] = [];

    // Create nodes for each span
    spans.forEach((span, index) => {
      // Backend returns simple strings, no need for type checking
      const spanId = span.span_id;
      const parentSpanId = span.parent_span_id;

      nodeMap.set(spanId, {
        id: spanId,
        type: 'default',
        position: {
          x: 100 + (index % 3) * 200,
          y: 50 + Math.floor(index / 3) * 100,
        },
        data: {
          label: (
            <div
              style={{
                padding: '8px 12px',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
                background: '#ffffff',
                fontSize: '12px',
                minWidth: '120px',
                textAlign: 'center',
              }}
            >
              <div style={{ fontWeight: '600', color: '#1f2937' }}>
                {span.service_name}
              </div>
              <div style={{ color: '#6b7280', fontSize: '10px', marginTop: 2 }}>
                {span.operation_name}
              </div>
              <div style={{ color: '#3b82f6', fontSize: '10px', marginTop: 2 }}>
                {(span.duration_ns / 1_000_000).toFixed(1)}ms
              </div>
            </div>
          ),
        },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      });

      // Create edge from parent to child
      if (parentSpanId && nodeMap.has(parentSpanId)) {
        edgeList.push({
          id: `${parentSpanId}-${spanId}`,
          source: parentSpanId,
          target: spanId,
          type: 'smoothstep',
          style: { stroke: '#94a3b8', strokeWidth: 2 },
          animated: true,
        });
      }
    });

    // Find root nodes (no parent)
    const rootNodeIds = new Set(nodeMap.keys());
    spans.forEach(span => {
      const parentSpanId = span.parent_span_id
        ? typeof span.parent_span_id === 'string'
          ? span.parent_span_id
          : span.parent_span_id['0']
        : null;
      if (parentSpanId && rootNodeIds.has(parentSpanId)) {
        rootNodeIds.delete(parentSpanId);
      }
    });

    // Position root nodes at the top
    let rootX = 50;
    rootNodeIds.forEach(rootId => {
      const node = nodeMap.get(rootId);
      if (node) {
        node.position = { x: rootX, y: 20 };
        rootX += 250;
      }
    });

    setNodes(Array.from(nodeMap.values()));
    setEdges(edgeList);
  }, [spans, setNodes, setEdges]);

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        style={{ background: '#fafafa' }}
      >
        <Controls />
        <Background color="#e5e7eb" gap={16} />
      </ReactFlow>
    </div>
  );
}
