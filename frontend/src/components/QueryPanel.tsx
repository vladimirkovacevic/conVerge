/**
 * Query panel for submitting new queries and viewing streaming responses
 */

import { useState, useCallback } from 'react';

interface QueryPanelProps {
  onSubmit: (query: string) => void;
  isStreaming: boolean;
  streamingResponse: string;
}

export function QueryPanel({ onSubmit, isStreaming, streamingResponse }: QueryPanelProps) {
  const [query, setQuery] = useState('');

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (query.trim() && !isStreaming) {
        onSubmit(query.trim());
        setQuery('');
      }
    },
    [query, onSubmit, isStreaming]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      // Submit on Enter (without Shift)
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (query.trim() && !isStreaming) {
          onSubmit(query.trim());
          setQuery('');
        }
      }
    },
    [query, onSubmit, isStreaming]
  );

  return (
    <div className="h-full flex flex-col">
      {/* Streaming response viewer */}
      <div className="flex-1 overflow-y-auto p-4">
        {streamingResponse ? (
          <div className="space-y-2">
            <div className="text-xs font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
              <span className="animate-pulse">⚡</span> Streaming Response...
            </div>
            <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg text-sm text-gray-900 dark:text-gray-100 whitespace-pre-wrap">
              {streamingResponse}
              <span className="animate-pulse">▊</span>
            </div>
          </div>
        ) : (
          <div className="text-center text-gray-400 dark:text-gray-500 mt-8">
            <div className="text-3xl mb-2">💭</div>
            <div className="text-sm">Enter a query to start a new branch</div>
          </div>
        )}
      </div>

      {/* Query input form */}
      <div className="border-t border-gray-200 dark:border-gray-700 p-4">
        <form onSubmit={handleSubmit} className="space-y-3">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter your query here... (Press Enter to submit, Shift+Enter for new line)"
            disabled={isStreaming}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                     bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
                     placeholder-gray-400 dark:placeholder-gray-500
                     focus:ring-2 focus:ring-blue-500 focus:border-transparent
                     disabled:opacity-50 disabled:cursor-not-allowed
                     resize-none"
          />

          <button
            type="submit"
            disabled={!query.trim() || isStreaming}
            className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg
                     transition-colors duration-200
                     disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-blue-600"
          >
            {isStreaming ? (
              <span className="flex items-center justify-center gap-2">
                <span className="animate-spin">⚡</span>
                Streaming...
              </span>
            ) : (
              '🚀 Submit Query'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
