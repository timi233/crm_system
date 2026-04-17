import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getProductInstallationsByCustomer,
  createProductInstallation,
  updateProductInstallation,
  deleteProductInstallation,
  getProductInstallationCredentials,
} from '../services/productInstallationService';
import type { ProductInstallationCreate, ProductInstallationUpdate } from '../types/productInstallation';

export const useProductInstallations = (customerId: number) => {
  return useQuery({
    queryKey: ['product-installations', customerId],
    queryFn: () => getProductInstallationsByCustomer(customerId),
    enabled: customerId > 0,
  });
};

export const useCreateProductInstallation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ProductInstallationCreate) => createProductInstallation(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['product-installations', variables.customer_id] });
    },
  });
};

export const useUpdateProductInstallation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ProductInstallationUpdate }) => 
      updateProductInstallation(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['product-installations'] });
    },
  });
};

export const useDeleteProductInstallation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteProductInstallation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['product-installations'] });
    },
  });
};

export const useProductInstallationCredentials = (id: number, enabled: boolean = false) => {
  return useQuery({
    queryKey: ['product-installation-credentials', id],
    queryFn: () => getProductInstallationCredentials(id),
    enabled: enabled && id > 0,
  });
};