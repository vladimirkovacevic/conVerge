/**
 * ConVerge - Main Application Component
 */

import { useState, useCallback, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactFlowProvider } from 'reactflow';

import { GraphView } from './components/GraphView';
import { ContextPanel } from './components/ContextPanel';
import { QueryPanel } from './components/QueryPanel';
import {
  useConversations,
  useGraph,
  useCreateConversation,
  useSelectNode,
} from './hooks/useConversation';
import { useWebSocket } from './hooks/useWebSocket';
import { apiClient } from './lib/api';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 0,
    },
  },
});

function ConVergeApp() {
  console.log('ConVergeApp rendering...');

  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [streamingResponse, setStreamingResponse] = useState('');
  const [selectedNodeAncestors, setSelectedNodeAncestors] = useState<any[]>([]);

  const { data: conversations } = useConversations();
  const { data: graphData, refetch: refetchGraph } = useGraph(currentConversationId);
  const createConversation = useCreateConversation();
  const selectNode = useSelectNode();

  console.log('ConVergeApp state:', { currentConversationId, conversations, graphData });

  const selectedNode = graphData?.nodes.find((n) => n.id === graphData.active_node_id);

  // Fetch ancestors when node changes
  useEffect(() => {
    if (selectedNode?.id) {
      apiClient.getAncestors(selectedNode.id).then(setSelectedNodeAncestors);
    }
  }, [selectedNode?.id]);

  const { isStreaming, sendBranchRequest } = useWebSocket({
    conversationId: currentConversationId || '',
    wsUrl: currentConversationId
      ? apiClient.getWebSocketUrl(currentConversationId)
      : '',
    onToken: (token) => {
      setStreamingResponse((prev) => prev + token);
    },
    onComplete: async () => {
      setStreamingResponse('');
      await refetchGraph();
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
      alert(`Error: ${error}`);
      setStreamingResponse('');
    },
  });

  const handleCreateConversation = async () => {
    const title = prompt('Enter conversation title:', 'New Conversation');
    if (!title) return;

    const context = prompt(
      'Enter initial system context:',
      'You are a helpful AI assistant.'
    );
    if (!context) return;

    const result = await createConversation.mutateAsync({
      title,
      initial_context: context,
    });

    setCurrentConversationId(result.conversation_id);
  };

  const handleNodeClick = useCallback(
    (nodeId: string) => {
      if (currentConversationId) {
        selectNode.mutate({ conversationId: currentConversationId, nodeId });
      }
    },
    [currentConversationId, selectNode]
  );

  const handleQuerySubmit = useCallback(
    (query: string) => {
      if (!currentConversationId || !graphData?.active_node_id) return;

      sendBranchRequest({
        query,
        parent_node_id: graphData.active_node_id,
        model: 'google/gemma-2-9b-it:free',
      });
    },
    [currentConversationId, graphData?.active_node_id, sendBranchRequest]
  );

  return (
    <div className="h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              🌳 ConVerge
            </h1>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Graph-based Conversation Management
            </span>
          </div>

          <div className="flex items-center gap-3">
            {/* Conversation selector */}
            {conversations && conversations.length > 0 && (
              <select
                value={currentConversationId || ''}
                onChange={(e) => setCurrentConversationId(e.target.value || null)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                         bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
                         focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select conversation...</option>
                {conversations.map((conv) => (
                  <option key={conv.id} value={conv.id}>
                    {conv.title}
                  </option>
                ))}
              </select>
            )}

            <button
              onClick={handleCreateConversation}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg
                       transition-colors duration-200"
            >
              + New Conversation
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left sidebar - Context view */}
        <div className="w-80 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="h-full flex flex-col">
            <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
              <h2 className="font-semibold text-gray-900 dark:text-gray-100">
                📋 Node Details
              </h2>
            </div>
            <div className="flex-1 overflow-hidden">
              <ContextPanel node={selectedNode} ancestors={selectedNodeAncestors} />
            </div>
          </div>
        </div>

        {/* Center - Graph visualization */}
        <div className="flex-1 bg-gray-100 dark:bg-gray-900">
          <ReactFlowProvider>
            <GraphView
              graphData={graphData}
              onNodeClick={handleNodeClick}
            />
          </ReactFlowProvider>
        </div>

        {/* Right sidebar - Query panel */}
        <div className="w-96 bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="h-full flex flex-col">
            <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
              <h2 className="font-semibold text-gray-900 dark:text-gray-100">
                💬 Query & Branch
              </h2>
            </div>
            <div className="flex-1 overflow-hidden">
              <QueryPanel
                onSubmit={handleQuerySubmit}
                isStreaming={isStreaming}
                streamingResponse={streamingResponse}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-6 py-2">
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <div>
            💾 In-Memory Storage | Data resets on server restart
          </div>
          <div>
            {graphData && (
              <span>
                {graphData.nodes.length} nodes | {graphData.edges.length} edges
              </span>
            )}
          </div>
        </div>
      </footer>
    </div>
  );
}

export default function App() {
  console.log('App component rendering...');
  return (
    <QueryClientProvider client={queryClient}>
      <ConVergeApp />
    </QueryClientProvider>
  );
}

console.log('App.tsx module loaded');
