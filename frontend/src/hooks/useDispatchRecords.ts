import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getDispatchRecords, DispatchRecordQueryParams } from '../services/dispatchRecordService';

export const useDispatchRecords = (params: DispatchRecordQueryParams) => {
  const queryKey = ['dispatchRecords', params];

  return useQuery({
    queryKey,
    queryFn: () => getDispatchRecords(params),
    enabled: !!(params.lead_id || params.opportunity_id || params.project_id),
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
};

export const useInvalidateDispatchRecords = () => {
  const queryClient = useQueryClient();

  return (params: DispatchRecordQueryParams) => {
    const queryKey = ['dispatchRecords', params];
    queryClient.invalidateQueries({ queryKey });
  };
};
