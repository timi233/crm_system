export interface ProductInstallation {
  id: number;
  customer_id: number;
  customer_name?: string;
  manufacturer: string;
  product_type: string;
  product_model?: string;
  license_scale?: string;
  system_version?: string;
  online_date?: string;
  maintenance_expiry?: string;
  username?: string;
  password?: string;
  login_url?: string;
  notes?: string;
  created_at: string;
  updated_at?: string;
  created_by_id?: number;
  created_by_name?: string;
  can_view_credentials: boolean;
}

export interface ProductInstallationCreate {
  customer_id: number;
  manufacturer: string;
  product_type: string;
  product_model?: string;
  license_scale?: string;
  system_version?: string;
  online_date?: string;
  maintenance_expiry?: string;
  username?: string;
  password?: string;
  login_url?: string;
  notes?: string;
}

export interface ProductInstallationUpdate {
  manufacturer?: string;
  product_type?: string;
  product_model?: string;
  license_scale?: string;
  system_version?: string;
  online_date?: string;
  maintenance_expiry?: string;
  username?: string;
  password?: string;
  login_url?: string;
  notes?: string;
}

export interface ProductInstallationWithCredentials extends ProductInstallation {
  username_actual?: string;
  password_actual?: string;
  login_url_actual?: string;
}