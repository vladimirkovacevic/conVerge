/**
 * Main graph visualization component using React Flow
 */

import { useCallback, useMemo, useEffect } from 'react';
import ReactFlow, {
  Controls,
  Background,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
  ConnectionLineType,
  MarkerType,
} from 'reactflow';
import dagre from 'dagre';
import 'reactflow/dist/style.css';

import { CustomNode } from './CustomNode';
import type { GraphData } from '../types/graph';

// Define our own types to avoid import issues
type FlowNode = {
  id: string;
  type?: string;
  data: any;
  position: { x: number; y: number };
};

type FlowEdge = {
  id: string;
  source: string;
  target: string;
  type?: string;
  animated?: boolean;
  markerEnd?: any;
  label?: string;
  labelStyle?: any;
  labelBgStyle?: any;
};

interface GraphViewProps {
  graphData: GraphData | undefined;
  onNodeClick: (nodeId: string) => void;
  onNodeDelete?: (nodeId: string) => void;
}

const nodeTypes = {
  custom: CustomNode,
};

// Layout algorithm using dagre
const getLayoutedElements = (nodes: FlowNode[], edges: FlowEdge[]) => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: 'TB', ranksep: 80, nodesep: 40 });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 250, height: 100 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - 125,
        y: nodeWithPosition.y - 50,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
};

export function GraphView({ graphData, onNodeClick }: GraphViewProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Convert graph data to React Flow format
  const { flowNodes, flowEdges } = useMemo(() => {
    if (!graphData) {
      return { flowNodes: [], flowEdges: [] };
    }

    const flowNodes: FlowNode[] = graphData.nodes.map((node) => ({
      id: node.id,
      type: 'custom',
      data: node,
      position: { x: 0, y: 0 }, // Will be set by layout algorithm
    }));

    const flowEdges: FlowEdge[] = graphData.edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: ConnectionLineType.SmoothStep,
      animated: true,
      markerEnd: {
        type: MarkerType.ArrowClosed,
        width: 20,
        height: 20,
      },
      label: edge.query_text?.slice(0, 30) + (edge.query_text?.length > 30 ? '...' : ''),
      labelStyle: { fontSize: 10, fill: '#666' },
      labelBgStyle: { fill: 'white', fillOpacity: 0.8 },
    }));

    return { flowNodes, flowEdges };
  }, [graphData]);

  // Apply layout when graph data changes
  useEffect(() => {
    if (flowNodes.length > 0) {
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        flowNodes,
        flowEdges
      );
      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
    } else {
      setNodes([]);
      setEdges([]);
    }
  }, [flowNodes, flowEdges, setNodes, setEdges]);

  const handleNodeClick = useCallback(
    (_event: React.MouseEvent, node: FlowNode) => {
      onNodeClick(node.id);
    },
    [onNodeClick]
  );

  if (!graphData) {
    return (
      <div className="w-full h-full flex items-center justify-center text-gray-500 dark:text-gray-400">
        <div className="text-center space-y-2">
          <div className="text-4xl">🌳</div>
          <div className="text-lg font-semibold">No Conversation Selected</div>
          <div className="text-sm">Create or select a conversation to get started</div>
        </div>
      </div>
    );
  }

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onNodeClick={handleNodeClick}
      nodeTypes={nodeTypes}
      fitView
      minZoom={0.1}
      maxZoom={2}
      defaultEdgeOptions={{
        type: ConnectionLineType.SmoothStep,
        animated: true,
      }}
    >
      <Background variant={BackgroundVariant.Dots} gap={16} size={1} />
      <Controls />
    </ReactFlow>
  );
}
