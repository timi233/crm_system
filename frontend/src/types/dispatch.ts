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