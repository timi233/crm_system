import api from './api';
import { DispatchApplicationRequest, DispatchApplicationResponse } from '../types/dispatch';

export const createDispatchFromLead = async (
  leadId: number
): Promise<DispatchApplicationResponse> => {
  const response = await api.post<DispatchApplicationResponse>(
    `/leads/${leadId}/create-dispatch`
  );
  return response.data;
};

export const createDispatchFromOpportunity = async (
  opportunityId: number
): Promise<DispatchApplicationResponse> => {
  const response = await api.post<DispatchApplicationResponse>(
    `/opportunities/${opportunityId}/create-dispatch`
  );
  return response.data;
};

export const createDispatchFromProject = async (
  projectId: number
): Promise<DispatchApplicationResponse> => {
  const response = await api.post<DispatchApplicationResponse>(
    `/projects/${projectId}/create-dispatch`
  );
  return response.data;
};