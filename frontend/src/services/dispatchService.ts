import { apiClient } from './apiClient';
import { DispatchApplicationRequest, DispatchApplicationResponse } from '../types/dispatch';

export const createDispatchFromLead = async (
  leadId: number,
  request: DispatchApplicationRequest
): Promise<DispatchApplicationResponse> => {
  const response = await apiClient.post<DispatchApplicationResponse>(
    `/leads/${leadId}/create-dispatch`,
    request
  );
  return response.data;
};

export const createDispatchFromOpportunity = async (
  opportunityId: number,
  request: DispatchApplicationRequest
): Promise<DispatchApplicationResponse> => {
  const response = await apiClient.post<DispatchApplicationResponse>(
    `/opportunities/${opportunityId}/create-dispatch`,
    request
  );
  return response.data;
};

export const createDispatchFromProject = async (
  projectId: number,
  request: DispatchApplicationRequest
): Promise<DispatchApplicationResponse> => {
  const response = await apiClient.post<DispatchApplicationResponse>(
    `/projects/${projectId}/create-dispatch`,
    request
  );
  return response.data;
};