import api from './api';
import { DispatchRecord, DispatchStatus } from '../types/dispatch';

export interface DispatchRecordQueryParams {
  lead_id?: number;
  opportunity_id?: number;
  project_id?: number;
}

export const getDispatchRecords = async (
  params: DispatchRecordQueryParams
): Promise<DispatchRecord[]> => {
  let endpoint = '';
  
  if (params.lead_id) {
    endpoint = `/leads/${params.lead_id}/dispatch-history`;
  } else if (params.opportunity_id) {
    endpoint = `/opportunities/${params.opportunity_id}/dispatch-history`;
  } else if (params.project_id) {
    endpoint = `/projects/${params.project_id}/dispatch-history`;
  } else {
    throw new Error('Must provide one of: lead_id, opportunity_id, or project_id');
  }

  const response = await api.get<DispatchRecord[]>(endpoint);
  return response.data;
};
