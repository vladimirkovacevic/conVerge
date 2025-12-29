/**
 * Custom node component for React Flow
 */

import { memo } from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeData } from '../types/graph';

interface CustomNodeProps {
  data: NodeData & { isActive?: boolean };
  selected?: boolean;
}

export const CustomNode = memo(({ data, selected }: CustomNodeProps) => {
  const isRoot = !data.parent_id;
  const hasResponse = !!data.response;

  return (
    <div
      className={`
        relative px-4 py-3 rounded-lg border-2 min-w-[200px] max-w-[300px]
        transition-all duration-200 shadow-md hover:shadow-lg
        ${selected || data.isActive
          ? 'border-blue-500 bg-blue-50 dark:bg-blue-950'
          : 'border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800'
        }
        ${isRoot ? 'border-purple-500 bg-purple-50 dark:bg-purple-950' : ''}
      `}
    >
      {!isRoot && (
        <Handle
          type="target"
          position={Position.Top}
          className="!bg-blue-500 !w-3 !h-3"
        />
      )}

      <div className="space-y-2">
        {/* Query */}
        {data.query && (
          <div className="text-sm">
            <div className="font-semibold text-gray-700 dark:text-gray-300 mb-1">
              {isRoot ? '🎯 Initial Context' : '💬 Query'}
            </div>
            <div className="text-gray-600 dark:text-gray-400 line-clamp-2">
              {data.query}
            </div>
          </div>
        )}

        {/* Response preview */}
        {hasResponse && (
          <div className="text-sm">
            <div className="font-semibold text-gray-700 dark:text-gray-300 mb-1">
              🤖 Response
            </div>
            <div className="text-gray-600 dark:text-gray-400 line-clamp-3">
              {data.response}
            </div>
          </div>
        )}

        {/* Root context */}
        {isRoot && !data.query && (
          <div className="text-sm">
            <div className="font-semibold text-purple-700 dark:text-purple-300 mb-1">
              🌱 Root Node
            </div>
            <div className="text-gray-600 dark:text-gray-400 line-clamp-2">
              {data.context.substring(0, 100)}...
            </div>
          </div>
        )}

        {/* Metadata */}
        {data.model && (
          <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-500">
            <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded">
              {data.model.split('/').pop()?.split(':')[0]}
            </span>
            {data.latency_ms && (
              <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded">
                {data.latency_ms}ms
              </span>
            )}
          </div>
        )}
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-blue-500 !w-3 !h-3"
      />
    </div>
  );
});

CustomNode.displayName = 'CustomNode';
