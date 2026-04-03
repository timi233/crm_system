import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

export interface DictItem {
  id: number;
  dict_type: string;
  code: string;
  name: string;
  parent_id: number | null;
  sort_order: number;
  is_active: boolean;
  extra_data: Record<string, any> | null;
}

export interface DictItemCreate {
  dict_type: string;
  code: string;
  name: string;
  parent_id?: number;
  sort_order?: number;
  is_active?: boolean;
  extra_data?: Record<string, any>;
}

export interface TreeNode extends DictItem {
  children?: TreeNode[];
  value: string;
  label: string;
}

export const useDictItems = (dictType?: string, parentId?: number) => {
  return useQuery({
    queryKey: ['dictItems', dictType, parentId],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (dictType) params.append('dict_type', dictType);
      if (parentId !== undefined) params.append('parent_id', String(parentId));
      const response = await api.get<DictItem[]>(`/dict/items?${params.toString()}`);
      return response.data;
    },
  });
};

export const useDictTypes = () => {
  return useQuery({
    queryKey: ['dictTypes'],
    queryFn: async () => {
      const response = await api.get<{ types: string[] }>('/dict/types');
      return response.data.types;
    },
  });
};

export const useDictTree = (dictType: string) => {
  return useQuery({
    queryKey: ['dictTree', dictType],
    queryFn: async (): Promise<TreeNode[]> => {
      const response = await api.get<DictItem[]>(`/dict/items?dict_type=${dictType}`);
      const items = response.data;
      
      const buildTree = (items: DictItem[]): TreeNode[] => {
        const itemMap = new Map<number, TreeNode>();
        const roots: TreeNode[] = [];

        items.forEach(item => {
          itemMap.set(item.id, { 
            ...item, 
            children: [],
            value: item.name,
            label: item.name,
          });
        });

        items.forEach(item => {
          const node = itemMap.get(item.id)!;
          if (item.parent_id === null) {
            roots.push(node);
          } else {
            const parent = itemMap.get(item.parent_id);
            if (parent) {
              parent.children = parent.children || [];
              parent.children.push(node);
            }
          }
        });

        const sortChildren = (nodes: TreeNode[]) => {
          nodes.sort((a, b) => a.sort_order - b.sort_order);
          nodes.forEach(node => {
            if (node.children && node.children.length > 0) {
              sortChildren(node.children);
            }
          });
        };
        sortChildren(roots);

        return roots;
      };

      return buildTree(items);
    },
    enabled: !!dictType,
  });
};

export const useRegionCascader = () => {
  return useQuery({
    queryKey: ['regionCascader'],
    queryFn: async () => {
      const response = await api.get<DictItem[]>(`/dict/items?dict_type=地区`);
      const items = response.data;
      
      const provinces: { value: string; label: string; code: string; children: { value: string; label: string; code: string }[] }[] = [];
      
      items.filter(i => i.parent_id === null).forEach(province => {
        const cities = items
          .filter(i => i.parent_id === province.id)
          .sort((a, b) => a.sort_order - b.sort_order)
          .map(city => ({
            value: city.name,
            label: city.name,
            code: city.code,
          }));
        
        provinces.push({
          value: province.name,
          label: province.name,
          code: province.code,
          children: cities,
        });
      });
      
      return provinces;
    },
  });
};

export const useProductTypeCascader = () => {
  return useQuery({
    queryKey: ['productTypeCascader'],
    queryFn: async () => {
      const response = await api.get<DictItem[]>(`/dict/items?dict_type=产品类型`);
      const items = response.data;
      
      interface CascaderOption {
        value: string;
        label: string;
        code: string;
        children?: CascaderOption[];
      }
      
      const buildTree = (parentId: number | null): CascaderOption[] => {
        return items
          .filter(i => i.parent_id === parentId)
          .sort((a, b) => a.sort_order - b.sort_order)
          .map(item => ({
            value: item.name,
            label: item.name,
            code: item.code,
            children: buildTree(item.id).length > 0 ? buildTree(item.id) : undefined,
          }));
      };
      
      return buildTree(null);
    },
  });
};

export const useCreateDictItem = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (item: DictItemCreate) => {
      const response = await api.post<DictItem>('/dict/items', item);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dictItems'] });
      queryClient.invalidateQueries({ queryKey: ['dictTypes'] });
    },
  });
};

export const useUpdateDictItem = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, item }: { id: number; item: Partial<DictItemCreate> }) => {
      const response = await api.put<DictItem>(`/dict/items/${id}`, item);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dictItems'] });
    },
  });
};

export const useDeleteDictItem = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/dict/items/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dictItems'] });
      queryClient.invalidateQueries({ queryKey: ['dictTypes'] });
    },
  });
};