/**
 * API client for ConVerge backend
 */

import type {
  Conversation,
  CreateConversationRequest,
  GraphData,
  NodeData,
} from '../types/graph';

// Environment-aware API configuration
// Remove trailing slash if present to avoid double slashes
const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8001').replace(/\/$/, '');
const API_BASE = `${API_URL}/api`;
const WS_BASE = `${API_URL.replace('http', 'ws')}/api`;

class ApiClient {
  async listConversations(): Promise<Conversation[]> {
    const response = await fetch(`${API_BASE}/conversations`);
    if (!response.ok) throw new Error('Failed to fetch conversations');
    return response.json();
  }

  async createConversation(
    request: CreateConversationRequest
  ): Promise<{ conversation_id: string; root_node_id: string; active_node_id: string }> {
    const response = await fetch(`${API_BASE}/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    if (!response.ok) throw new Error('Failed to create conversation');
    return response.json();
  }

  async getConversation(conversationId: string): Promise<Conversation> {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}`);
    if (!response.ok) throw new Error('Failed to fetch conversation');
    return response.json();
  }

  async deleteConversation(conversationId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete conversation');
  }

  async getGraph(conversationId: string): Promise<GraphData> {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}/graph`);
    if (!response.ok) throw new Error('Failed to fetch graph');
    return response.json();
  }

  async selectNode(conversationId: string, nodeId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}/select`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ node_id: nodeId }),
    });
    if (!response.ok) throw new Error('Failed to select node');
  }

  async getAncestors(nodeId: string): Promise<NodeData[]> {
    const response = await fetch(`${API_BASE}/nodes/${nodeId}/ancestors`);
    if (!response.ok) throw new Error('Failed to fetch ancestors');
    return response.json();
  }

  getWebSocketUrl(conversationId: string): string {
    return `${WS_BASE}/conversations/${conversationId}/stream`;
  }
}

export const apiClient = new ApiClient();
