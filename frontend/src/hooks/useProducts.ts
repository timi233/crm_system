import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

export const PRODUCTS_QUERY_KEY = 'products';

export type Product = {
  id: number;
  product_code: string;
  product_name: string;
  product_type: string;
  brand_manufacturer: string;
  is_active: boolean;
  notes?: string;
};

export const useProducts = () => {
  return useQuery({
    queryKey: [PRODUCTS_QUERY_KEY],
    queryFn: () => api.get<Product[]>('/products').then(res => res.data),
  });
};

export const useProduct = (id: number) => {
  return useQuery({
    queryKey: [PRODUCTS_QUERY_KEY, id],
    queryFn: () => api.get<Product>(`/products/${id}`).then(res => res.data),
    enabled: !!id,
  });
};

export const useCreateProduct = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (product: Omit<Product, 'id'>) => 
      api.post<Product>('/products', product).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [PRODUCTS_QUERY_KEY] });
    },
  });
};

export const useUpdateProduct = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, product }: { id: number; product: Omit<Product, 'id'> }) => 
      api.put<Product>(`/products/${id}`, product).then(res => res.data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [PRODUCTS_QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [PRODUCTS_QUERY_KEY, variables.id] });
    },
  });
};

export const useDeleteProduct = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.delete(`/products/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [PRODUCTS_QUERY_KEY] });
    },
  });
};
