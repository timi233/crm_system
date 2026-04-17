import api from './api';
import type { 
  ProductInstallation, 
  ProductInstallationCreate, 
  ProductInstallationUpdate,
  ProductInstallationWithCredentials 
} from '../types/productInstallation';

export const getProductInstallationsByCustomer = async (customerId: number): Promise<ProductInstallation[]> => {
  const response = await api.get(`/product-installations/customer/${customerId}`);
  return response.data;
};

export const createProductInstallation = async (data: ProductInstallationCreate): Promise<ProductInstallation> => {
  const response = await api.post('/product-installations/', data);
  return response.data;
};

export const updateProductInstallation = async (id: number, data: ProductInstallationUpdate): Promise<ProductInstallation> => {
  const response = await api.put(`/product-installations/${id}`, data);
  return response.data;
};

export const deleteProductInstallation = async (id: number): Promise<void> => {
  await api.delete(`/product-installations/${id}`);
};

export const getProductInstallationCredentials = async (id: number): Promise<ProductInstallationWithCredentials> => {
  const response = await api.get(`/product-installations/${id}/credentials`);
  return response.data;
};