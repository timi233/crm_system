export interface DispatchApplicationRequest {
  technician_ids: number[];
  service_mode?: 'online' | 'offline';
  start_date?: string;
  start_period?: string;
  end_date?: string;
  end_period?: string;
  work_type?: string;
  notes?: string;
}

export interface DispatchApplicationResponse {
  success: boolean;
  message: string;
  work_order_id?: string;
  work_order_no?: string;
}

export type DispatchStatus = 'pending' | 'assigned' | 'in_progress' | 'completed' | 'cancelled';

export interface DispatchRecord {
  id: number;
  work_order_id: string;
  work_order_no: string;
  source_type: 'lead' | 'opportunity' | 'project';
  source_id: number;
  status: DispatchStatus;
  previous_status?: string;
  status_updated_at?: string;
  order_type: string;
  customer_name: string;
  priority: string;
  technician_ids?: number[];
  technician_names?: string[];
  estimated_start_date?: string;
  estimated_start_period?: string;
  estimated_end_date?: string;
  estimated_end_period?: string;
  description?: string;
  created_at: string;
  dispatched_at?: string;
  completed_at?: string;
}