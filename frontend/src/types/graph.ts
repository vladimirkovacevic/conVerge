/**
 * TypeScript type definitions for ConVerge graph data structures
 */

export interface NodeData {
  id: string;
  conversation_id: string;
  parent_id: string | null;
  context: string;
  response: string | null;
  query: string | null;
  created_at: string;
  model: string | null;
  tokens_used: number | null;
  latency_ms: number | null;
}

export interface EdgeData {
  id: string;
  source: string;
  target: string;
  query_text: string;
  created_at: string;
}

export interface GraphData {
  conversation_id: string;
  active_node_id: string;
  nodes: NodeData[];
  edges: EdgeData[];
}

export interface Conversation {
  id: string;
  title: string;
  root_node_id: string;
  active_node_id: string;
  created_at: string;
  updated_at: string;
}

export interface CreateConversationRequest {
  title: string;
  initial_context: string;
}

export interface BranchRequest {
  query: string;
  parent_node_id?: string;
  model?: string;
}
