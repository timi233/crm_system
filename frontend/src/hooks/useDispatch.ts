import { useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  createDispatchFromLead,
  createDispatchFromOpportunity,
  createDispatchFromProject 
} from '../services/dispatchService';
import { DispatchApplicationRequest, DispatchApplicationResponse } from '../types/dispatch';

interface DispatchCreateParams {
  entityId: number;
  technicianIds: number[];
  startDate: string;
  startPeriod: string;
  endDate: string;
  endPeriod: string;
  workType: string;
  serviceMode: 'online' | 'offline';
}

export const useCreateDispatchFromLead = () => {
  const queryClient = useQueryClient();
  
  return useMutation<
    DispatchApplicationResponse,
    Error,
    DispatchCreateParams
  >({
    mutationFn: ({ entityId, technicianIds, startDate, startPeriod, endDate, endPeriod, workType, serviceMode }) => 
      createDispatchFromLead(entityId, { 
        technician_ids: technicianIds,
        service_mode: serviceMode,
        start_date: startDate,
        start_period: startPeriod,
        end_date: endDate,
        end_period: endPeriod,
        work_type: workType
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      queryClient.invalidateQueries({ queryKey: ['dispatchRecords'] });
    },
  });
};

export const useCreateDispatchFromOpportunity = () => {
  const queryClient = useQueryClient();
  
  return useMutation<
    DispatchApplicationResponse,
    Error,
    DispatchCreateParams
  >({
    mutationFn: ({ entityId, technicianIds, startDate, startPeriod, endDate, endPeriod, workType, serviceMode }) => 
      createDispatchFromOpportunity(entityId, { 
        technician_ids: technicianIds,
        service_mode: serviceMode,
        start_date: startDate,
        start_period: startPeriod,
        end_date: endDate,
        end_period: endPeriod,
        work_type: workType
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['opportunities'] });
      queryClient.invalidateQueries({ queryKey: ['dispatchRecords'] });
    },
  });
};

export const useCreateDispatchFromProject = () => {
  const queryClient = useQueryClient();
  
  return useMutation<
    DispatchApplicationResponse,
    Error,
    DispatchCreateParams
  >({
    mutationFn: ({ entityId, technicianIds, startDate, startPeriod, endDate, endPeriod, workType, serviceMode }) => 
      createDispatchFromProject(entityId, { 
        technician_ids: technicianIds,
        service_mode: serviceMode,
        start_date: startDate,
        start_period: startPeriod,
        end_date: endDate,
        end_period: endPeriod,
        work_type: workType
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['dispatchRecords'] });
    },
  });
};