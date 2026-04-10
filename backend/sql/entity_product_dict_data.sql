-- Entity Product Dictionary Data

-- Product Types (产品类型)
INSERT INTO dict_items (dict_type, code, name, sort_order, is_active) VALUES
('product_type', 'server', '服务器', 1, true),
('product_type', 'storage', '存储设备', 2, true),
('product_type', 'network', '网络设备', 3, true),
('product_type', 'software', '软件系统', 4, true),
('product_type', 'security', '安全设备', 5, true);

-- Brands for Servers (服务器品牌)
INSERT INTO dict_items (dict_type, code, name, parent_id, sort_order, is_active)
SELECT 'brand', 'dell', 'Dell', 
  (SELECT id FROM dict_items WHERE dict_type='product_type' AND code='server'), 1, true;

INSERT INTO dict_items (dict_type, code, name, parent_id, sort_order, is_active)
SELECT 'brand', 'hp', 'HP', 
  (SELECT id FROM dict_items WHERE dict_type='product_type' AND code='server'), 2, true;

INSERT INTO dict_items (dict_type, code, name, parent_id, sort_order, is_active)
SELECT 'brand', 'lenovo', '联想', 
  (SELECT id FROM dict_items WHERE dict_type='product_type' AND code='server'), 3, true;

INSERT INTO dict_items (dict_type, code, name, parent_id, sort_order, is_active)
SELECT 'brand', 'huawei', '华为', 
  (SELECT id FROM dict_items WHERE dict_type='product_type' AND code='server'), 4, true;

-- Brands for Storage (存储设备品牌)
INSERT INTO dict_items (dict_type, code, name, parent_id, sort_order, is_active)
SELECT 'brand', 'netapp', 'NetApp', 
  (SELECT id FROM dict_items WHERE dict_type='product_type' AND code='storage'), 1, true;

INSERT INTO dict_items (dict_type, code, name, parent_id, sort_order, is_active)
SELECT 'brand', 'dellemc', 'Dell EMC', 
  (SELECT id FROM dict_items WHERE dict_type='product_type' AND code='storage'), 2, true;

-- Models for Servers (服务器型号 - Dell)
INSERT INTO dict_items (dict_type, code, name, parent_id, sort_order, is_active)
SELECT 'model', 'dell_r740', 'Dell PowerEdge R740', 
  (SELECT id FROM dict_items WHERE code='dell' AND dict_type='brand'), 1, true;

INSERT INTO dict_items (dict_type, code, name, parent_id, sort_order, is_active)
SELECT 'model', 'dell_r750', 'Dell PowerEdge R750', 
  (SELECT id FROM dict_items WHERE code='dell' AND dict_type='brand'), 2, true;

INSERT INTO dict_items (dict_type, code, name, parent_id, sort_order, is_active)
SELECT 'model', 'dell_r940', 'Dell PowerEdge R940', 
  (SELECT id FROM dict_items WHERE code='dell' AND dict_type='brand'), 3, true;

-- Models for HP Servers
INSERT INTO dict_items (dict_type, code, name, parent_id, sort_order, is_active)
SELECT 'model', 'hp_dl380', 'HP ProLiant DL380', 
  (SELECT id FROM dict_items WHERE code='hp' AND dict_type='brand'), 1, true;

INSERT INTO dict_items (dict_type, code, name, parent_id, sort_order, is_active)
SELECT 'model', 'hp_dl360', 'HP ProLiant DL360', 
  (SELECT id FROM dict_items WHERE code='hp' AND dict_type='brand'), 2, true;

-- Models for Storage (网络存储)
INSERT INTO dict_items (dict_type, code, name, parent_id, sort_order, is_active)
SELECT 'model', 'netapp_fas', 'NetApp FAS系列', 
  (SELECT id FROM dict_items WHERE code='netapp' AND dict_type='brand'), 1, true;

INSERT INTO dict_items (dict_type, code, name, parent_id, sort_order, is_active)
SELECT 'model', 'dellemc_powervault', 'Dell EMC PowerVault', 
  (SELECT id FROM dict_items WHERE code='dellemc' AND dict_type='brand'), 1, true;

-- Sample Entity Products for testing
INSERT INTO entity_products (entity_type, entity_id, product_type_id, brand_id, model_id, created_at)
SELECT 'project', 1, 
  (SELECT id FROM dict_items WHERE code='server' AND dict_type='product_type'),
  (SELECT id FROM dict_items WHERE code='dell' AND dict_type='brand'),
  (SELECT id FROM dict_items WHERE code='dell_r740' AND dict_type='model'),
  CURRENT_DATE;
