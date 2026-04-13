import { useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  createDispatchFromLead,
  createDispatchFromOpportunity,
  createDispatchFromProject 
} from '../services/dispatchService';
import { DispatchApplicationResponse } from '../types/dispatch';

export const useCreateDispatchFromLead = () => {
  const queryClient = useQueryClient();
  
  return useMutation<
    DispatchApplicationResponse,
    Error,
    number
  >({
    mutationFn: (leadId) => createDispatchFromLead(leadId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      queryClient.invalidateQueries({ queryKey: ['dispatch-records'] });
    },
  });
};

export const useCreateDispatchFromOpportunity = () => {
  const queryClient = useQueryClient();
  
  return useMutation<
    DispatchApplicationResponse,
    Error,
    number
  >({
    mutationFn: (opportunityId) => createDispatchFromOpportunity(opportunityId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['opportunities'] });
      queryClient.invalidateQueries({ queryKey: ['dispatch-records'] });
    },
  });
};

export const useCreateDispatchFromProject = () => {
  const queryClient = useQueryClient();
  
  return useMutation<
    DispatchApplicationResponse,
    Error,
    number
  >({
    mutationFn: (projectId) => createDispatchFromProject(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['dispatch-records'] });
    },
  });
};