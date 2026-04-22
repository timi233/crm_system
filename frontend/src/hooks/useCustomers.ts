import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { CustomerRead, CustomerCreate } from '../types/customer';

export const CUSTOMERS_QUERY_KEY = 'customers';

export const useCustomers = (enabled: boolean = true) => {
  return useQuery({
    queryKey: [CUSTOMERS_QUERY_KEY],
    queryFn: () => api.get<CustomerRead[]>('/customers/').then(res => res.data),
    enabled,
  });
};

export const useCustomer = (id: number) => {
  return useQuery({
    queryKey: [CUSTOMERS_QUERY_KEY, id],
    queryFn: () => api.get<CustomerRead>(`/customers/${id}`).then(res => res.data),
    enabled: !!id,
  });
};

export const useCreateCustomer = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (customer: CustomerCreate) => 
      api.post<CustomerRead>('/customers/', customer).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CUSTOMERS_QUERY_KEY] });
    },
  });
};

export const useUpdateCustomer = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, customer }: { id: number; customer: CustomerCreate }) => 
      api.put<CustomerRead>(`/customers/${id}`, customer).then(res => res.data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [CUSTOMERS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [CUSTOMERS_QUERY_KEY, variables.id] });
    },
  });
};

export const useDeleteCustomer = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.delete(`/customers/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CUSTOMERS_QUERY_KEY] });
    },
  });
};
