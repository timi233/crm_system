export interface KnowledgeSourceType {
  id: number;
  name: string;
  value: string;
}

export interface Knowledge {
  id: number;
  title: string;
  problem: string;
  solution: string;
  problem_type: string;
  problem_type_name?: string;
  source_type?: string;
  source_type_name?: string;
  source_id?: number;
  view_count: number;
  tags?: string[];
  created_at?: string;
  updated_at?: string;
  created_by?: number;
  created_by_name?: string;
}

export interface KnowledgeCreate {
  title: string;
  problem: string;
  solution: string;
  problem_type?: string;
  source_type?: string;
  source_id?: number;
  tags?: string[];
}

export interface KnowledgeUpdate {
  title?: string;
  problem?: string;
  solution?: string;
  problem_type?: string;
  source_type?: string;
  source_id?: number;
  tags?: string[];
}
