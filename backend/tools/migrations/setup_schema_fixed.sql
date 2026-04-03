-- Create CRM database schema
-- Run sequences first

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Sequences for auto-numbering (must be created before tables)
CREATE SEQUENCE IF NOT EXISTS customer_code_seq START 1;
CREATE SEQUENCE IF NOT EXISTS channel_code_seq START 1;
CREATE SEQUENCE IF NOT EXISTS opportunity_code_seq START 1;
CREATE SEQUENCE IF NOT EXISTS project_code_seq START 1;
CREATE SEQUENCE IF NOT EXISTS product_code_seq START 1;

-- Table: users
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'sales' CHECK (role IN ('admin', 'sales', 'business', 'finance')),
  sales_leader_id INTEGER REFERENCES users(id),
  sales_region VARCHAR(100),
  is_active BOOLEAN NOT NULL DEFAULT true
);

-- Table: products
CREATE TABLE IF NOT EXISTS products (
  id SERIAL PRIMARY KEY,
  product_code VARCHAR(10) UNIQUE NOT NULL,
  product_name VARCHAR(100) NOT NULL,
  product_type VARCHAR(30) NOT NULL,
  brand_manufacturer VARCHAR(100) NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT true,
  notes TEXT
);

-- Table: terminal_customers
CREATE TABLE IF NOT EXISTS terminal_customers (
  id SERIAL PRIMARY KEY,
  customer_code VARCHAR(20) UNIQUE NOT NULL,
  customer_name VARCHAR(255) NOT NULL,
  customer_nickname VARCHAR(100),
  customer_industry VARCHAR(50) NOT NULL,
  customer_region VARCHAR(100) NOT NULL,
  customer_owner_id INTEGER NOT NULL REFERENCES users(id),
  main_contact VARCHAR(100),
  phone VARCHAR(20),
  customer_status VARCHAR(20) NOT NULL DEFAULT 'active',
  maintenance_expiry DATE,
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: channels
CREATE TABLE IF NOT EXISTS channels (
  id SERIAL PRIMARY KEY,
  channel_code VARCHAR(20) UNIQUE NOT NULL,
  company_name VARCHAR(255) NOT NULL,
  channel_type VARCHAR(30) NOT NULL,
  main_contact VARCHAR(100),
  phone VARCHAR(20),
  billing_info TEXT,
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: projects (created before opportunities due to foreign key)
CREATE TABLE IF NOT EXISTS projects (
  id SERIAL PRIMARY KEY,
  project_code VARCHAR(25) UNIQUE NOT NULL,
  project_name VARCHAR(255) NOT NULL,
  terminal_customer_id INTEGER NOT NULL REFERENCES terminal_customers(id),
  channel_id INTEGER REFERENCES channels(id),
  source_opportunity_id INTEGER,
  product_ids INTEGER[] NOT NULL DEFAULT '{}',
  business_type VARCHAR(30) NOT NULL,
  project_status VARCHAR(30) NOT NULL DEFAULT 'pending',
  sales_owner_id INTEGER NOT NULL REFERENCES users(id),
  downstream_contract_amount DECIMAL(15,2) NOT NULL DEFAULT 0,
  upstream_procurement_amount DECIMAL(15,2),
  direct_project_investment DECIMAL(15,2),
  additional_investment DECIMAL(15,2),
  winning_date DATE,
  acceptance_date DATE,
  first_payment_date DATE,
  actual_payment_amount DECIMAL(15,2),
  notes TEXT,
  gross_margin DECIMAL(15,2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: opportunities
CREATE TABLE IF NOT EXISTS opportunities (
  id SERIAL PRIMARY KEY,
  opportunity_code VARCHAR(20) UNIQUE NOT NULL,
  opportunity_name VARCHAR(255) NOT NULL,
  terminal_customer_id INTEGER NOT NULL REFERENCES terminal_customers(id),
  opportunity_source VARCHAR(50) NOT NULL,
  product_ids INTEGER[] DEFAULT '{}',
  opportunity_stage VARCHAR(30) NOT NULL DEFAULT 'initial',
  lead_grade VARCHAR(10) NOT NULL DEFAULT 'C',
  expected_contract_amount DECIMAL(15,2) NOT NULL DEFAULT 0,
  expected_close_date DATE,
  sales_owner_id INTEGER NOT NULL REFERENCES users(id),
  channel_id INTEGER REFERENCES channels(id),
  vendor_registration_status VARCHAR(30),
  vendor_discount DECIMAL(5,4),
  loss_reason VARCHAR(100),
  project_id INTEGER REFERENCES projects(id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add foreign key for projects.source_opportunity_id
ALTER TABLE projects DROP CONSTRAINT IF EXISTS projects_source_opportunity_id_fkey;
ALTER TABLE projects ADD CONSTRAINT projects_source_opportunity_id_fkey 
  FOREIGN KEY (source_opportunity_id) REFERENCES opportunities(id);

-- Table: contracts
CREATE TABLE IF NOT EXISTS contracts (
  id SERIAL PRIMARY KEY,
  contract_code VARCHAR(100) NOT NULL,
  contract_name VARCHAR(255) NOT NULL,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  contract_direction VARCHAR(20) NOT NULL DEFAULT 'Downstream' CHECK (contract_direction IN ('Downstream', 'Upstream')),
  contract_status VARCHAR(20) NOT NULL DEFAULT 'draft',
  counterparty_id INTEGER,
  contract_amount DECIMAL(15,2) NOT NULL DEFAULT 0,
  signing_date DATE,
  contract_file_url TEXT,
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: follow_ups
CREATE TABLE IF NOT EXISTS follow_ups (
  id SERIAL PRIMARY KEY,
  terminal_customer_id INTEGER NOT NULL REFERENCES terminal_customers(id),
  opportunity_id INTEGER REFERENCES opportunities(id),
  project_id INTEGER REFERENCES projects(id),
  follow_up_date DATE NOT NULL,
  follow_up_method VARCHAR(20) NOT NULL,
  follow_up_content TEXT NOT NULL,
  follow_up_conclusion VARCHAR(30) NOT NULL,
  next_action VARCHAR(255),
  next_follow_up_date DATE,
  follower_id INTEGER NOT NULL REFERENCES users(id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_terminal_customers_owner_id ON terminal_customers (customer_owner_id);
CREATE INDEX IF NOT EXISTS idx_terminal_customers_code ON terminal_customers (customer_code);
CREATE INDEX IF NOT EXISTS idx_channels_code ON channels (channel_code);
CREATE INDEX IF NOT EXISTS idx_opportunities_owner ON opportunities (sales_owner_id);
CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects (sales_owner_id);

-- Insert default admin user
INSERT INTO users (name, email, hashed_password, role, is_active) 
VALUES ('Admin User', 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.flLWrYLYqVQZiK', 'admin', true)
ON CONFLICT (email) DO NOTHING;

-- Sample products
INSERT INTO products (product_code, product_name, product_type, brand_manufacturer) VALUES
('PRD-001', '服务器 A1', '服务器', 'Dell'),
('PRD-002', '交换机 S1', '网络设备', 'Cisco'),
('PRD-003', '存储设备 M1', '存储', 'NetApp')
ON CONFLICT (product_code) DO NOTHING;