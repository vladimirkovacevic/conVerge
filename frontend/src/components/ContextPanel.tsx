/**
 * Panel for viewing node context and response
 */

import type { ConversationNode } from '../types/graph';

interface ContextPanelProps {
  node: ConversationNode | undefined;
  ancestors: ConversationNode[];
}

export function ContextPanel({ node, ancestors }: ContextPanelProps) {
  if (!node) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <div className="text-center p-8">
          <div className="text-4xl mb-3">👈</div>
          <div className="text-lg font-semibold">Select a node</div>
          <div className="text-sm mt-2">Click any node to view its details</div>
        </div>
      </div>
    );
  }

  const isRoot = !node.parent_id;

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-6 space-y-6">
        {/* Node info */}
        <div>
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">
            {isRoot ? '🌱 Root Node' : '💬 Conversation Node'}
          </h2>
          <div className="flex flex-wrap gap-2 text-xs">
            {node.model && (
              <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded">
                {node.model}
              </span>
            )}
            {node.latency_ms && (
              <span className="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded">
                {node.latency_ms}ms
              </span>
            )}
            {node.tokens_used && (
              <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 rounded">
                {node.tokens_used} tokens
              </span>
            )}
          </div>
        </div>

        {/* Path */}
        {ancestors.length > 1 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              📍 Path from Root
            </h3>
            <div className="space-y-1">
              {ancestors.map((ancestor, idx) => (
                <div
                  key={ancestor.id}
                  className="text-xs text-gray-600 dark:text-gray-400 pl-2 border-l-2 border-gray-300 dark:border-gray-700"
                >
                  <span className="font-mono text-gray-500">{idx + 1}.</span>{' '}
                  {ancestor.query || 'Root'}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Query */}
        {node.query && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              💬 Query
            </h3>
            <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg text-sm text-gray-800 dark:text-gray-200">
              {node.query}
            </div>
          </div>
        )}

        {/* Response */}
        {node.response && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              🤖 Response
            </h3>
            <div className="p-3 bg-blue-50 dark:bg-blue-950 rounded-lg text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap">
              {node.response}
            </div>
          </div>
        )}

        {/* Full Context */}
        <div>
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
            📄 Full Context
          </h3>
          <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg text-xs font-mono text-gray-700 dark:text-gray-300 max-h-96 overflow-y-auto">
            {node.context}
          </div>
        </div>

        {/* Metadata */}
        <details className="text-xs">
          <summary className="cursor-pointer font-semibold text-gray-700 dark:text-gray-300 mb-2">
            🔍 Metadata
          </summary>
          <pre className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg text-xs overflow-x-auto">
            {JSON.stringify(
              {
                id: node.id,
                conversation_id: node.conversation_id,
                parent_id: node.parent_id,
                created_at: node.created_at,
              },
              null,
              2
            )}
          </pre>
        </details>
      </div>
    </div>
  );
}
