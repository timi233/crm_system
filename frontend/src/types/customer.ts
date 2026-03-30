export interface CustomerBase {
  customer_name: string;
  customer_nickname?: string;
  customer_industry: string;
  customer_region: string;
  customer_owner_id: number;
  main_contact?: string;
  phone?: string;
  customer_status: string;
  maintenance_expiry?: string;
  notes?: string;
}

export interface CustomerCreate extends CustomerBase {}

export interface CustomerRead extends CustomerBase {
  id: number;
  customer_code: string;
}