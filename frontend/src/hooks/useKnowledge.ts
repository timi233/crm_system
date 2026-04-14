import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as knowledgeService from '../services/knowledgeService';
import { Knowledge, KnowledgeCreate, KnowledgeUpdate } from '../types/knowledge';

export const KNOWLEDGE_QUERY_KEY = 'knowledge';

export const useKnowledgeList = (params?: knowledgeService.KnowledgeQueryParams) => {
  return useQuery<Knowledge[]>({
    queryKey: [KNOWLEDGE_QUERY_KEY, params],
    queryFn: () => knowledgeService.getKnowledgeList(params),
  });
};

export const useKnowledge = (id: number) => {
  return useQuery<Knowledge>({
    queryKey: [KNOWLEDGE_QUERY_KEY, id],
    queryFn: () => knowledgeService.getKnowledgeById(id),
    enabled: !!id,
  });
};

export const useCreateKnowledge = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (knowledge: KnowledgeCreate) =>
      knowledgeService.createKnowledge(knowledge),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [KNOWLEDGE_QUERY_KEY] });
    },
  });
};

export const useUpdateKnowledge = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, knowledge }: { id: number; knowledge: KnowledgeUpdate }) =>
      knowledgeService.updateKnowledge(id, knowledge),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [KNOWLEDGE_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [KNOWLEDGE_QUERY_KEY, variables.id] });
    },
  });
};

export const useDeleteKnowledge = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => knowledgeService.deleteKnowledge(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [KNOWLEDGE_QUERY_KEY] });
    },
  });
};
