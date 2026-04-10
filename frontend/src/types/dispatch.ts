export interface DispatchApplicationRequest {
  dispatch_api_url: string;
  dispatch_token: string;
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
  technician_ids?: string[];
  description?: string;
  created_at: string;
  dispatched_at?: string;
  completed_at?: string;
}