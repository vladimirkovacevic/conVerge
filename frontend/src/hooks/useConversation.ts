/**
 * React Query hooks for conversation and graph data
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import type { CreateConversationRequest } from '../types/graph';

export function useConversations() {
  return useQuery({
    queryKey: ['conversations'],
    queryFn: () => apiClient.listConversations(),
  });
}

export function useConversation(conversationId: string | null) {
  return useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: () => apiClient.getConversation(conversationId!),
    enabled: !!conversationId,
  });
}

export function useGraph(conversationId: string | null) {
  return useQuery({
    queryKey: ['graph', conversationId],
    queryFn: () => apiClient.getGraph(conversationId!),
    enabled: !!conversationId,
    refetchInterval: false,
  });
}

export function useCreateConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateConversationRequest) =>
      apiClient.createConversation(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });
}

export function useSelectNode() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ conversationId, nodeId }: { conversationId: string; nodeId: string }) =>
      apiClient.selectNode(conversationId, nodeId),
    onSuccess: (_, { conversationId }) => {
      queryClient.invalidateQueries({ queryKey: ['graph', conversationId] });
    },
  });
}
