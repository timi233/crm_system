-- Create CRM database schema for migration
-- This script should be run after creating the crm_migration database

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table: users (销售人员管理)
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'sales', 'business', 'finance')),
  sales_leader_id INTEGER REFERENCES users(id),
  sales_region VARCHAR(100)
);

-- Table: products (产品字典)
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  product_code VARCHAR(10) UNIQUE NOT NULL DEFAULT ('PRD-' || to_char(nextval('product_code_seq'), 'FM000')),
  product_name VARCHAR(100) NOT NULL,
  product_type VARCHAR(30) NOT NULL,
  brand_manufacturer VARCHAR(100) NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT true,
  notes TEXT
);

-- Table: terminal_customers (终端客户档案)
CREATE TABLE terminal_customers (
  id SERIAL PRIMARY KEY,
  customer_code VARCHAR(20) UNIQUE NOT NULL DEFAULT ('CUS-' || to_char(CURRENT_DATE, 'YYYYMM') || '-' || to_char(nextval('customer_code_seq'), 'FM000')),
  customer_name VARCHAR(255) NOT NULL,
  customer_nickname VARCHAR(100),
  customer_industry VARCHAR(50) NOT NULL,
  customer_region VARCHAR(100) NOT NULL,
  customer_owner_id INTEGER NOT NULL REFERENCES users(id),
  main_contact VARCHAR(100),
  phone VARCHAR(20),
  customer_status VARCHAR(20) NOT NULL,
  maintenance_expiry DATE,
  notes TEXT
);

-- Table: channels (渠道/交易对象档案)
CREATE TABLE channels (
  id SERIAL PRIMARY KEY,
  channel_code VARCHAR(20) UNIQUE NOT NULL DEFAULT ('CH-' || to_char(CURRENT_DATE, 'YYYYMM') || '-' || to_char(nextval('channel_code_seq'), 'FM000')),
  company_name VARCHAR(255) NOT NULL,
  channel_type VARCHAR(30) NOT NULL,
  main_contact VARCHAR(100),
  phone VARCHAR(20),
  billing_info TEXT,
  notes TEXT
);

-- Table: opportunities (商机管理)
CREATE TABLE opportunities (
  id SERIAL PRIMARY KEY,
  opportunity_code VARCHAR(20) UNIQUE NOT NULL DEFAULT ('OPP-' || to_char(CURRENT_DATE, 'YYYYMM') || '-' || to_char(nextval('opportunity_code_seq'), 'FM000')),
  opportunity_name VARCHAR(255) NOT NULL,
  terminal_customer_id INTEGER NOT NULL REFERENCES terminal_customers(id),
  opportunity_source VARCHAR(50) NOT NULL,
  product_ids INTEGER[],
  opportunity_stage VARCHAR(30) NOT NULL,
  lead_grade VARCHAR(10) NOT NULL,
  expected_contract_amount DECIMAL(15,2) NOT NULL,
  expected_close_date DATE,
  sales_owner_id INTEGER NOT NULL REFERENCES users(id),
  channel_id INTEGER REFERENCES channels(id),
  vendor_registration_status VARCHAR(30),
  vendor_discount DECIMAL(5,4),
  loss_reason VARCHAR(100),
  project_id INTEGER REFERENCES projects(id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  CONSTRAINT chk_loss_reason CHECK (
    (opportunity_stage <> 'Lost') OR (loss_reason IS NOT NULL)
  )
);

-- Table: projects (项目管理)
CREATE TABLE projects (
  id SERIAL PRIMARY KEY,
  project_code VARCHAR(25) UNIQUE NOT NULL DEFAULT ('PRJ-' || to_char(CURRENT_DATE, 'YYYYMM') || '-' || to_char(nextval('project_code_seq'), 'FM000')),
  project_name VARCHAR(255) NOT NULL,
  terminal_customer_id INTEGER NOT NULL REFERENCES terminal_customers(id),
  channel_id INTEGER REFERENCES channels(id),
  source_opportunity_id INTEGER REFERENCES opportunities(id),
  product_ids INTEGER[] NOT NULL,
  business_type VARCHAR(30) NOT NULL,
  project_status VARCHAR(30) NOT NULL,
  sales_owner_id INTEGER NOT NULL REFERENCES users(id),
  downstream_contract_amount DECIMAL(15,2) NOT NULL,
  upstream_procurement_amount DECIMAL(15,2),
  direct_project_investment DECIMAL(15,2),
  additional_investment DECIMAL(15,2),
  winning_date DATE,
  acceptance_date DATE,
  first_payment_date DATE,
  actual_payment_amount DECIMAL(15,2),
  notes TEXT,
  gross_margin DECIMAL(15,2)
);

-- Table: contracts (合同管理)
CREATE TABLE contracts (
  id SERIAL PRIMARY KEY,
  contract_code VARCHAR(100) NOT NULL,
  contract_name VARCHAR(255) NOT NULL,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  contract_direction VARCHAR(20) NOT NULL CHECK (contract_direction IN ('Downstream', 'Upstream')),
  contract_status VARCHAR(20) NOT NULL,
  counterparty_id INTEGER,
  contract_amount DECIMAL(15,2) NOT NULL,
  signing_date DATE,
  contract_file_url TEXT,
  notes TEXT
);

-- Table: follow_ups (跟进记录)
CREATE TABLE follow_ups (
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
  system_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT chk_oppty_or_project CHECK (
    (opportunity_id IS NOT NULL) <> (project_id IS NOT NULL)
  )
);

-- Sequences for auto-numbering
CREATE SEQUENCE IF NOT EXISTS customer_code_seq START 1;
CREATE SEQUENCE IF NOT EXISTS channel_code_seq START 1;
CREATE SEQUENCE IF NOT EXISTS opportunity_code_seq START 1;
CREATE SEQUENCE IF NOT EXISTS project_code_seq START 1;
CREATE SEQUENCE IF NOT EXISTS product_code_seq START 1;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_terminal_customers_owner_id ON terminal_customers (customer_owner_id);
CREATE INDEX IF NOT EXISTS idx_terminal_customers_code ON terminal_customers (customer_code);
CREATE INDEX IF NOT EXISTS idx_channels_code ON channels (channel_code);
CREATE INDEX IF NOT EXISTS idx_opportunities_terminal_customer_id ON opportunities (terminal_customer_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_sales_owner_id ON opportunities (sales_owner_id);
CREATE INDEX IF NOT EXISTS idx_projects_terminal_customer_id ON projects (terminal_customer_id);
CREATE INDEX IF NOT EXISTS idx_projects_sales_owner_id ON projects (sales_owner_id);
CREATE INDEX IF NOT EXISTS idx_contracts_project_id ON contracts (project_id);
CREATE INDEX IF NOT EXISTS idx_follow_ups_terminal_customer_id ON follow_ups (terminal_customer_id);

-- Insert default users
INSERT INTO users (name, email, role) VALUES 
('Admin User', 'admin@example.com', 'admin'),
('Sales User', 'sales@example.com', 'sales'),
('Business User', 'business@example.com', 'business'),
('Finance User', 'finance@example.com', 'finance');

-- Insert default product
INSERT INTO products (product_name, product_type, brand_manufacturer) VALUES 
('IPGuard', 'Endpoint Security', 'Beijing Yidun Technology');