import { useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  createDispatchFromLead,
  createDispatchFromOpportunity,
  createDispatchFromProject 
} from '../services/dispatchService';
import { DispatchApplicationRequest, DispatchApplicationResponse } from '../types/dispatch';

export const useCreateDispatchFromLead = () => {
  const queryClient = useQueryClient();
  
  return useMutation<
    DispatchApplicationResponse,
    Error,
    { leadId: number; request: DispatchApplicationRequest }
  >({
    mutationFn: ({ leadId, request }) => createDispatchFromLead(leadId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] });
    },
  });
};

export const useCreateDispatchFromOpportunity = () => {
  const queryClient = useQueryClient();
  
  return useMutation<
    DispatchApplicationResponse,
    Error,
    { opportunityId: number; request: DispatchApplicationRequest }
  >({
    mutationFn: ({ opportunityId, request }) => createDispatchFromOpportunity(opportunityId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['opportunities'] });
    },
  });
};

export const useCreateDispatchFromProject = () => {
  const queryClient = useQueryClient();
  
  return useMutation<
    DispatchApplicationResponse,
    Error,
    { projectId: number; request: DispatchApplicationRequest }
  >({
    mutationFn: ({ projectId, request }) => createDispatchFromProject(projectId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
};