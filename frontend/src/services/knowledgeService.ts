import api from './api';
import { Knowledge, KnowledgeCreate, KnowledgeUpdate } from '../types/knowledge';

export interface KnowledgeQueryParams {
  keyword?: string;
  problem_type?: string;
  source_type?: number;
}

export const getKnowledgeList = async (
  params?: KnowledgeQueryParams
): Promise<Knowledge[]> => {
  const response = await api.get<Knowledge[]>('/knowledge/', { params });
  return response.data;
};

export const getKnowledgeById = async (
  id: number
): Promise<Knowledge> => {
  const response = await api.get<Knowledge>(`/knowledge/detail/${id}`);
  return response.data;
};

export const createKnowledge = async (
  knowledge: KnowledgeCreate
): Promise<Knowledge> => {
  const response = await api.post<Knowledge>('/knowledge/', knowledge);
  return response.data;
};

export const updateKnowledge = async (
  id: number,
  knowledge: KnowledgeUpdate
): Promise<Knowledge> => {
  const response = await api.put<Knowledge>(`/knowledge/${id}`, knowledge);
  return response.data;
};

export const deleteKnowledge = async (
  id: number
): Promise<void> => {
  await api.delete(`/knowledge/${id}`);
};
