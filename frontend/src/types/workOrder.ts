export type WorkOrderStatus = 'PENDING' | 'ACCEPTED' | 'IN_SERVICE' | 'DONE' | 'CANCELLED' | 'REJECTED';

export type WorkOrderPriority = 'NORMAL' | 'URGENT' | 'VERY_URGENT';

export type OrderType = 'CF' | 'CO' | 'MF' | 'MO';

export type SourceType = 'lead' | 'opportunity' | 'project';

export interface WorkOrder {
  id: number;
  cuid_id?: string;
  work_order_no: string;
  order_type: OrderType;
  submitter_id: number;
  related_sales_id?: number;
  customer_name: string;
  customer_contact?: string;
  customer_phone?: string;
  has_channel: boolean;
  channel_id?: number;
  channel_name?: string;
  channel_contact?: string;
  channel_phone?: string;
  manufacturer_contact?: string;
  work_type?: string;
  priority: WorkOrderPriority;
  description: string;
  status: WorkOrderStatus;
  estimated_start_date?: string;
  estimated_start_period?: string;
  estimated_end_date?: string;
  estimated_end_period?: string;
  accepted_at?: string;
  started_at?: string;
  completed_at?: string;
  service_summary?: string;
  cancel_reason?: string;
  source_type?: SourceType;
  lead_id?: number;
  opportunity_id?: number;
  project_id?: number;
  created_at?: string;
  updated_at?: string;
  submitter_name?: string;
  related_sales_name?: string;
  channel_name_display?: string;
  technician_names: string[];
}

export interface WorkOrderCreate {
  order_type?: OrderType;
  submitter_id: number;
  related_sales_id?: number;
  customer_name: string;
  customer_contact?: string;
  customer_phone?: string;
  has_channel?: boolean;
  channel_id?: number;
  channel_name?: string;
  channel_contact?: string;
  channel_phone?: string;
  manufacturer_contact?: string;
  work_type?: string;
  priority?: WorkOrderPriority;
  description: string;
  estimated_start_date?: string;
  estimated_start_period?: string;
  estimated_end_date?: string;
  estimated_end_period?: string;
  service_summary?: string;
  cancel_reason?: string;
  source_type?: SourceType;
  lead_id?: number;
  opportunity_id?: number;
  project_id?: number;
}

export interface WorkOrderUpdate {
  work_order_no?: string;
  order_type?: OrderType;
  related_sales_id?: number;
  customer_name?: string;
  customer_contact?: string;
  customer_phone?: string;
  has_channel?: boolean;
  channel_id?: number;
  channel_name?: string;
  channel_contact?: string;
  channel_phone?: string;
  manufacturer_contact?: string;
  work_type?: string;
  priority?: WorkOrderPriority;
  description?: string;
  estimated_start_date?: string;
  estimated_start_period?: string;
  estimated_end_date?: string;
  estimated_end_period?: string;
  service_summary?: string;
  cancel_reason?: string;
  source_type?: SourceType;
  lead_id?: number;
  opportunity_id?: number;
  project_id?: number;
}

export interface WorkOrderStatusUpdate {
  status: WorkOrderStatus;
  service_summary?: string;
  cancel_reason?: string;
}

export interface WorkOrderAssignRequest {
  technician_ids: number[];
}

export interface Evaluation {
  id: number;
  work_order_id: number;
  quality_rating: number;
  response_rating: number;
  customer_feedback?: string;
  improvement_suggestion?: string;
  recommend: boolean;
  evaluator_id: number;
  created_at?: string;
  work_order_no?: string;
  work_order_info?: Record<string, any>;
}

export interface EvaluationCreate {
  work_order_id: number;
  quality_rating: number;
  response_rating: number;
  customer_feedback?: string;
  improvement_suggestion?: string;
  recommend: boolean;
}
