import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

export const TODOS_KEY = 'todos';

export type Todo = {
  key: string;
  type: string;
  title: string;
  description: string | null;
  priority: string;
  due_date: string | null;
  entity_type: string | null;
  entity_id: number | null;
  link: string | null;
  source: string;
  status: string;
};

export type TodoListResponse = {
  items: Todo[];
  total: number;
};

export type TodosParams = {
  type?: string;
  priority?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
  skip?: number;
  limit?: number;
};

export const useTodos = (params?: TodosParams, enabled: boolean = true) => {
  return useQuery({
    queryKey: [TODOS_KEY, params],
    queryFn: () => {
      const p = new URLSearchParams();
      if (params?.type) p.append('type', params.type);
      if (params?.priority) p.append('priority', params.priority);
      if (params?.status) p.append('status', params.status);
      if (params?.date_from) p.append('date_from', params.date_from);
      if (params?.date_to) p.append('date_to', params.date_to);
      if (params?.skip !== undefined) p.append('skip', String(params.skip));
      if (params?.limit !== undefined) p.append('limit', String(params.limit));
      return api.get<TodoListResponse>(`/todos?${p.toString()}`).then((r) => r.data);
    },
    enabled,
  });
};