/**
 * WebSocket hook for streaming LLM responses
 */

import { useEffect, useRef, useState } from 'react';
import type { BranchRequest } from '../types/graph';

interface StreamToken {
  type: 'token';
  content: string;
}

interface StreamComplete {
  type: 'complete';
  node_id: string;
  metadata: {
    latency_ms: number;
    model: string;
  };
}

interface StreamError {
  type: 'error';
  message: string;
}

type StreamMessage = StreamToken | StreamComplete | StreamError;

interface UseWebSocketProps {
  conversationId: string;
  wsUrl: string;
  onToken: (token: string) => void;
  onComplete: (nodeId: string, metadata: any) => void;
  onError: (error: string) => void;
}

export function useWebSocket({
  conversationId,
  wsUrl,
  onToken,
  onComplete,
  onError,
}: UseWebSocketProps) {
  const wsRef = useRef<WebSocket | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isConnected, setIsConnected] = useState(false);

  // Cleanup on unmount or URL change
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [wsUrl]);

  const sendBranchRequest = (request: BranchRequest) => {
    console.log('🔌 sendBranchRequest called', { wsUrl, conversationId, request });

    if (!wsUrl || !conversationId) {
      console.error('❌ No conversation selected');
      onError('No conversation selected');
      return;
    }

    // Close existing connection
    if (wsRef.current) {
      console.log('🔌 Closing existing WebSocket connection');
      wsRef.current.close();
    }

    console.log('🔌 Creating new WebSocket connection to:', wsUrl);
    // Create new WebSocket connection
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('✅ WebSocket connected!');
      setIsConnected(true);
      setIsStreaming(true);
      // Send the branch request
      console.log('📤 Sending branch request:', request);
      ws.send(JSON.stringify(request));
    };

    ws.onmessage = (event) => {
      console.log('📨 WebSocket message received:', event.data);
      try {
        const message: StreamMessage = JSON.parse(event.data);
        console.log('📨 Parsed message:', message);

        if (message.type === 'token') {
          onToken(message.content);
        } else if (message.type === 'complete') {
          console.log('✅ Stream complete:', message);
          setIsStreaming(false);
          onComplete(message.node_id, message.metadata);
          ws.close();
        } else if (message.type === 'error') {
          console.error('❌ Stream error:', message);
          setIsStreaming(false);
          onError(message.message);
          ws.close();
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      setIsStreaming(false);
      setIsConnected(false);
      onError('WebSocket connection error');
    };

    ws.onclose = (event) => {
      console.log('🔌 WebSocket closed:', event.code, event.reason);
      setIsConnected(false);
      setIsStreaming(false);
    };
  };

  return {
    isStreaming,
    isConnected,
    sendBranchRequest,
  };
}
