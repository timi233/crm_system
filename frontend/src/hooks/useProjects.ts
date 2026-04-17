import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

export const PROJECTS_QUERY_KEY = 'projects';

export type Project = {
  id: number;
  project_code: string;
  project_name: string;
  terminal_customer_id: number;
  terminal_customer_name?: string;
  sales_owner_id: number;
  sales_owner_name?: string;
  business_type: string;
  project_status: string;
  products?: string[];
  downstream_contract_amount?: number;
  upstream_procurement_amount?: number;
  gross_margin?: number;
  description?: string;
  notes?: string;
};

export const useProjects = () => {
  return useQuery({
    queryKey: [PROJECTS_QUERY_KEY],
    queryFn: () => api.get<Project[]>('/projects').then(res => res.data),
  });
};

export const useProject = (id: number) => {
  return useQuery({
    queryKey: [PROJECTS_QUERY_KEY, id],
    queryFn: () => api.get<Project>(`/projects/${id}`).then(res => res.data),
    enabled: !!id,
  });
};

export const useCreateProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (project: Omit<Project, 'id'>) => 
      api.post<Project>('/projects', project).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [PROJECTS_QUERY_KEY] });
    },
  });
};

export const useUpdateProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, project }: { id: number; project: Omit<Project, 'id'> }) => 
      api.put<Project>(`/projects/${id}`, project).then(res => res.data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [PROJECTS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [PROJECTS_QUERY_KEY, variables.id] });
    },
  });
};

export const useDeleteProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.delete(`/projects/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [PROJECTS_QUERY_KEY] });
    },
  });
};
