import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

export const ENTITY_PRODUCTS_QUERY_KEY = 'entityProducts';

export type EntityProduct = {
  id: number;
  entity_type: string;
  entity_id: number;
  product_type_id: number;
  brand_id?: number;
  model_id?: number;
  product_type_name?: string;
  brand_name?: string;
  model_name?: string;
  created_at?: string;
};

export const useEntityProducts = (entityType?: string, entityId?: number) => {
  return useQuery({
    queryKey: [ENTITY_PRODUCTS_QUERY_KEY, entityType, entityId],
    queryFn: () =>
      api
        .get<EntityProduct[]>(`/entity-products`, {
          params: { entity_type: entityType, entity_id: entityId },
        })
        .then(res => res.data),
    enabled: !!entityType && !!entityId,
  });
};

export const useCreateEntityProduct = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (entityProduct: Omit<EntityProduct, 'id' | 'created_at'>) =>
      api
        .post<EntityProduct>('/entity-products', entityProduct)
        .then(res => res.data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: [ENTITY_PRODUCTS_QUERY_KEY, variables.entity_type, variables.entity_id],
      });
    },
  });
};

export const useUpdateEntityProduct = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      entityProduct,
    }: {
      id: number;
      entityProduct: Omit<EntityProduct, 'id' | 'created_at'>;
    }) =>
      api
        .put<EntityProduct>(`/entity-products/${id}`, entityProduct)
        .then(res => res.data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: [
          ENTITY_PRODUCTS_QUERY_KEY,
          variables.entityProduct.entity_type,
          variables.entityProduct.entity_id,
        ],
      });
      queryClient.invalidateQueries({
        queryKey: [ENTITY_PRODUCTS_QUERY_KEY, variables.id],
      });
    },
  });
};

export const useDeleteEntityProduct = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.delete(`/entity-products/${id}`),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [ENTITY_PRODUCTS_QUERY_KEY] });
    },
  });
};

export const useBrandsByProductType = (productTypeId?: number) => {
  return useQuery({
    queryKey: ['brands', productTypeId],
    queryFn: () =>
      api
        .get<{ id: number; code: string; name: string; parent_id: number }[]>(
          '/dict-items/brands',
          { params: { product_type_id: productTypeId } }
        )
        .then(res => res.data),
    enabled: !!productTypeId,
  });
};

export const useModelsByBrand = (brandId?: number) => {
  return useQuery({
    queryKey: ['models', brandId],
    queryFn: () =>
      api
        .get<{ id: number; code: string; name: string; parent_id: number }[]>(
          '/dict-items/models',
          { params: { brand_id: brandId } }
        )
        .then(res => res.data),
    enabled: !!brandId,
  });
};

export const useProductTypes = () => {
  return useQuery({
    queryKey: ['productTypes'],
    queryFn: () =>
      api
        .get<{ id: number; code: string; name: string; parent_id: number }[]>(
          '/dict-items/product-types'
        )
        .then(res => res.data),
  });
};
