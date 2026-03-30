-- ---------------------------------------------
-- Sequences for Auto-numbering
-- ---------------------------------------------
CREATE SEQUENCE customer_code_seq START 1;
CREATE SEQUENCE channel_code_seq START 1;
CREATE SEQUENCE opportunity_code_seq START 1;
CREATE SEQUENCE project_code_seq START 1;
CREATE SEQUENCE product_code_seq START 1;

-- ---------------------------------------------
-- Table: users (销售人员管理)
-- ---------------------------------------------
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  sales_leader_id INTEGER REFERENCES users(id),
  sales_region VARCHAR(100)
);

-- ---------------------------------------------
-- Table: products (产品字典)
-- ---------------------------------------------
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  product_code VARCHAR(10) UNIQUE NOT NULL DEFAULT ('PRD-' || to_char(nextval('product_code_seq'), 'FM000')), -- Format: PRD-001
  product_name VARCHAR(100) NOT NULL, -- e.g., IPGuard, Aisino, NSFOCUS, Sangfor, Huorong, etc.
  product_type VARCHAR(30) NOT NULL,  -- Endpoint Security, Data Backup, Network Security, Maintenance Service (SVC), Other
  brand_manufacturer VARCHAR(100) NOT NULL, -- Corresponding vendor/manufacturer name
  is_active BOOLEAN NOT NULL DEFAULT true, -- In sale or discontinued
  notes TEXT
);

-- ---------------------------------------------
-- Table: terminal_customers (终端客户档案)
-- ---------------------------------------------
CREATE TABLE terminal_customers (
  id SERIAL PRIMARY KEY,
  customer_code VARCHAR(20) UNIQUE NOT NULL DEFAULT ('CUS-' || to_char(CURRENT_DATE, 'YYYYMM') || '-' || to_char(nextval('customer_code_seq'), 'FM000')), -- Format: CUS-YYYYMM-001
  customer_name VARCHAR(255) NOT NULL, -- Business registration name
  customer_nickname VARCHAR(100), -- Short name for daily use
  customer_industry VARCHAR(50) NOT NULL, -- Manufacturing, Finance, Government, Healthcare, Education, Energy, Other
  customer_region VARCHAR(100) NOT NULL, -- City names like Jinan, Qingdao, etc.
  customer_owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL, -- Sales owner
  main_contact VARCHAR(100), -- Main contact person name
  phone VARCHAR(20), -- Contact phone
  customer_status VARCHAR(20) NOT NULL, -- Potential, Active, Existing, Lost
  maintenance_expiry DATE, -- Maintenance contract expiry date
  notes TEXT
);

-- ---------------------------------------------
-- Table: channels (渠道/交易对象档案)
-- ---------------------------------------------
CREATE TABLE channels (
  id SERIAL PRIMARY KEY,
  channel_code VARCHAR(20) UNIQUE NOT NULL DEFAULT ('CH-' || to_char(CURRENT_DATE, 'YYYYMM') || '-' || to_char(nextval('channel_code_seq'), 'FM000')), -- Format: CH-YYYYMM-001
  company_name VARCHAR(255) NOT NULL, -- Business registration name
  channel_type VARCHAR(30) NOT NULL, -- Primary Channel, Secondary Channel, Direct Terminal Customer
  main_contact VARCHAR(100),
  phone VARCHAR(20),
  billing_info TEXT, -- Tax ID, address, bank info
  notes TEXT
);

-- ---------------------------------------------
-- Table: opportunities (商机管理)
-- ---------------------------------------------
CREATE TABLE opportunities (
  id SERIAL PRIMARY KEY,
  opportunity_code VARCHAR(20) UNIQUE NOT NULL DEFAULT ('OPP-' || to_char(CURRENT_DATE, 'YYYYMM') || '-' || to_char(nextval('opportunity_code_seq'), 'FM000')), -- Format: OPP-YYYYMM-001
  opportunity_name VARCHAR(255) NOT NULL,
  terminal_customer_id INTEGER NOT NULL REFERENCES terminal_customers(id) ON DELETE CASCADE,
  opportunity_source VARCHAR(50) NOT NULL, -- Direct Sales, Channel, Customer Referral, Renewal/Expansion
  product_ids INTEGER[], -- Array of product dictionary IDs (multi-select)
  opportunity_stage VARCHAR(30) NOT NULL, -- Initial Contact, Needs Confirmation, Proposal, Vendor Registration, Decision Pending, Won→Project, Lost
  lead_grade VARCHAR(10) NOT NULL, -- A (High), B (Medium), C (Low)
  expected_contract_amount DECIMAL(15,2) NOT NULL, -- In RMB
  expected_close_date DATE,
  sales_owner_id INTEGER NOT NULL REFERENCES users(id),
  channel_id INTEGER REFERENCES channels(id), -- Optional for channel-sourced opportunities
  vendor_registration_status VARCHAR(30),
  vendor_discount DECIMAL(5,4), -- e.g., 0.8500 for 85% discount
  loss_reason VARCHAR(100), -- Required when stage = 'Lost'
  project_id INTEGER REFERENCES projects(id), -- Optional, populated when converted to project
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT chk_loss_reason CHECK (
    (opportunity_stage <> 'Lost') OR (loss_reason IS NOT NULL)
  )
);

-- ---------------------------------------------
-- Table: projects (项目管理)
-- ---------------------------------------------
CREATE TABLE projects (
  id SERIAL PRIMARY KEY,
  project_code VARCHAR(25) UNIQUE NOT NULL DEFAULT ('PRJ-' || to_char(CURRENT_DATE, 'YYYYMM') || '-' || to_char(nextval('project_code_seq'), 'FM000')), -- Format: PRJ-YYYYMM-001 or PRJ-YYYYMM-001-SVC
  project_name VARCHAR(255) NOT NULL,
  terminal_customer_id INTEGER NOT NULL REFERENCES terminal_customers(id) ON DELETE CASCADE,
  channel_id INTEGER REFERENCES channels(id), -- Optional
  source_opportunity_id INTEGER REFERENCES opportunities(id), -- Optional
  product_ids INTEGER[] NOT NULL, -- Array of product dictionary IDs
  business_type VARCHAR(30) NOT NULL, -- New Project, Renewal/Maintenance, Expansion, Additional Purchase
  project_status VARCHAR(30) NOT NULL, -- Initiating, Executing, Pending Acceptance, Accepted, Paid, Terminated
  sales_owner_id INTEGER NOT NULL REFERENCES users(id),
  downstream_contract_amount DECIMAL(15,2) NOT NULL, -- Total contract amount with customer/channel
  upstream_procurement_amount DECIMAL(15,2), -- Total procurement amount from vendors
  direct_project_investment DECIMAL(15,2), -- Direct project investment costs
  additional_investment DECIMAL(15,2), -- Additional implicit costs
  winning_date DATE, -- Project won/bid date
  acceptance_date DATE, -- Customer acceptance date
  first_payment_date DATE, -- First payment received date
  actual_payment_amount DECIMAL(15,2), -- Actual payment received
  notes TEXT,
  gross_margin DECIMAL(15,2) -- computed via trigger
);

-- Trigger function to maintain gross_margin = downstream_contract_amount - upstream_procurement_amount
CREATE OR REPLACE FUNCTION compute_project_gross_margin() RETURNS trigger AS $$
BEGIN
  NEW.gross_margin := COALESCE(NEW.downstream_contract_amount, 0) - COALESCE(NEW.upstream_procurement_amount, 0);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_compute_gross_margin
BEFORE INSERT OR UPDATE ON projects
FOR EACH ROW
EXECUTE FUNCTION compute_project_gross_margin();

-- ---------------------------------------------
-- Table: contracts (合同管理)
-- ---------------------------------------------
CREATE TABLE contracts (
  id SERIAL PRIMARY KEY,
  contract_code VARCHAR(100) NOT NULL, -- Must match contract document number
  contract_name VARCHAR(255) NOT NULL,
  project_id INTEGER REFERENCES projects(id) NOT NULL,
  contract_direction VARCHAR(20) NOT NULL, -- Downstream (sales to customer), Upstream (procurement from vendor)
  contract_status VARCHAR(20) NOT NULL, -- Draft, Signing, Effective, Terminated
  counterparty_id INTEGER, -- References channels.id for downstream, or vendor name for upstream (see notes below)
  contract_amount DECIMAL(15,2) NOT NULL, -- Tax-inclusive amount in RMB
  signing_date DATE,
  contract_file_url TEXT, -- URL to contract file storage
  notes TEXT
);

-- Constraint: downstream should reference a channel if counterparty_id is set; upstream uses NULL in this simplified schema.
ALTER TABLE contracts
ADD CONSTRAINT chk_counterparty_direction
CHECK (
  (contract_direction = 'Downstream' AND counterparty_id IS NOT NULL) OR
  (contract_direction = 'Upstream' AND counterparty_id IS NULL)
);

-- Create FK for downstream case
ALTER TABLE contracts
ADD CONSTRAINT fk_contract_counterparty_channel
FOREIGN KEY (counterparty_id) REFERENCES channels(id);

-- ---------------------------------------------
-- Table: follow_ups (跟进记录)
-- ---------------------------------------------
CREATE TABLE follow_ups (
  id SERIAL PRIMARY KEY,
  terminal_customer_id INTEGER NOT NULL REFERENCES terminal_customers(id) ON DELETE CASCADE,
  opportunity_id INTEGER REFERENCES opportunities(id),
  project_id INTEGER REFERENCES projects(id),
  follow_up_date DATE NOT NULL, -- Actual follow-up date
  follow_up_method VARCHAR(20) NOT NULL, -- Phone, Visit, WeChat, Email, Meeting
  follow_up_content TEXT NOT NULL, -- Main content of communication
  follow_up_conclusion VARCHAR(30) NOT NULL, -- Progressing Well, Needs Support, Customer Hesitant, Pause Progress, Lost Deal
  next_action VARCHAR(255), -- Specific next action plan
  next_follow_up_date DATE,
  follower_id INTEGER NOT NULL REFERENCES users(id),
  system_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  -- Constraint: Exactly one of opportunity_id or project_id must be set
  CONSTRAINT chk_oppty_or_project
  CHECK (
    (opportunity_id IS NOT NULL) <> (project_id IS NOT NULL)
  )
);

-- ---------------------------------------------
-- Indexes (for performance)
-- ---------------------------------------------
-- FK indexes (explicitly add for performance; PostgreSQL creates implicit indexes on FK columns in some setups)
CREATE INDEX IF NOT EXISTS idx_terminal_customers_owner_id ON terminal_customers (customer_owner_id);
CREATE INDEX IF NOT EXISTS idx_term_customers_code ON terminal_customers (customer_code);

CREATE INDEX IF NOT EXISTS idx_channels_code ON channels (channel_code);
CREATE INDEX IF NOT EXISTS idx_channels_type ON channels (channel_type);

CREATE INDEX IF NOT EXISTS idx_opportunities_terminal_customer_id ON opportunities (terminal_customer_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_sales_owner_id ON opportunities (sales_owner_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_channel_id ON opportunities (channel_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_opportunity_stage ON opportunities (opportunity_stage);

CREATE INDEX IF NOT EXISTS idx_projects_terminal_customer_id ON projects (terminal_customer_id);
CREATE INDEX IF NOT EXISTS idx_projects_sales_owner_id ON projects (sales_owner_id);
CREATE INDEX IF NOT EXISTS idx_projects_project_status ON projects (project_status);
CREATE INDEX IF NOT EXISTS idx_projects_source_opportunity_id ON projects (source_opportunity_id);
CREATE INDEX IF NOT EXISTS idx_projects_channel_id ON projects (channel_id);
CREATE INDEX IF NOT EXISTS idx_projects_code ON projects (project_code);

CREATE INDEX IF NOT EXISTS idx_contracts_project_id ON contracts (project_id);
CREATE INDEX IF NOT EXISTS idx_contracts_counterparty_id ON contracts (counterparty_id);

CREATE INDEX IF NOT EXISTS idx_follow_ups_terminal_customer_id ON follow_ups (terminal_customer_id);
CREATE INDEX IF NOT EXISTS idx_follow_ups_opportunity_id ON follow_ups (opportunity_id);
CREATE INDEX IF NOT EXISTS idx_follow_ups_project_id ON follow_ups (project_id);
CREATE INDEX IF NOT EXISTS idx_follow_ups_follower_id ON follow_ups (follower_id);
CREATE INDEX IF NOT EXISTS idx_follow_ups_date ON follow_ups (follow_up_date);

-- Optional composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_projects_customer_status ON projects (terminal_customer_id, project_status);
CREATE INDEX IF NOT EXISTS idx_opportunities_stage_grade ON opportunities (opportunity_stage, lead_grade);

-- ---------------------------------------------
-- Data Migration Considerations
-- Notes for migrating from crm_schema_dump.json and existing Feishu data
-- - Ensure unique constraints are respected to handle duplicate customers
-- - Use product_ids arrays to map to the product dictionary by product_id
-- - For product name standardization, reference the products table and replace ad-hoc strings with product_code entries
-- - Migration tooling should map existing relationships to the new FK-driven schema (customer_owner_id -> users.id, etc.)
-- - If existing contract records reference upstream vendors, you may need to normalize vendor references into the channels table or extend processes to capture upstream vendor data
-- - The default code generators (CUS-*, CH-*, OPP-*, PRJ-*, PRD-*) rely on the dedicated sequences created at the top; ensure no pre-existing IDs collide
-- ---------------------------------------------

-- End of schema