-- 创建实体产品关联表
CREATE TABLE IF NOT EXISTS entity_products (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(20) NOT NULL,  -- lead, opportunity, project
    entity_id INTEGER NOT NULL,
    product_type_id INTEGER REFERENCES dict_items(id),
    brand_id INTEGER REFERENCES dict_items(id),
    model_id INTEGER REFERENCES dict_items(id),
    created_at DATE DEFAULT CURRENT_DATE
);

-- 创建索引
CREATE INDEX idx_entity_products_entity ON entity_products(entity_type, entity_id);
CREATE INDEX idx_entity_products_product_type ON entity_products(product_type_id);
CREATE INDEX idx_entity_products_brand ON entity_products(brand_id);
CREATE INDEX idx_entity_products_model ON entity_products(model_id);

-- 插入产品字典示例数据
-- 产品类型
INSERT INTO dict_items (dict_type, item_name, item_value, sort_order, is_active) VALUES
('product_type', '服务器', 'server', 1, true),
('product_type', '存储设备', 'storage', 2, true),
('product_type', '网络设备', 'network', 3, true),
('product_type', '安全设备', 'security', 4, true),
('product_type', '软件', 'software', 5, true);

-- 品牌（关联到产品类型）
INSERT INTO dict_items (dict_type, item_name, item_value, parent_id, sort_order, is_active)
SELECT 'brand', 'Dell', 'dell', id, 1, true FROM dict_items WHERE dict_type='product_type' AND item_value='server'
UNION ALL
SELECT 'brand', 'HP', 'hp', id, 2, true FROM dict_items WHERE dict_type='product_type' AND item_value='server'
UNION ALL
SELECT 'brand', 'Lenovo', 'lenovo', id, 3, true FROM dict_items WHERE dict_type='product_type' AND item_value='server'
UNION ALL
SELECT 'brand', '华为', 'huawei', id, 1, true FROM dict_items WHERE dict_type='product_type' AND item_value='storage'
UNION ALL
SELECT 'brand', 'NetApp', 'netapp', id, 2, true FROM dict_items WHERE dict_type='product_type' AND item_value='storage'
UNION ALL
SELECT 'brand', '思科', 'cisco', id, 1, true FROM dict_items WHERE dict_type='product_type' AND item_value='network'
UNION ALL
SELECT 'brand', '华为', 'huawei', id, 2, true FROM dict_items WHERE dict_type='product_type' AND item_value='network';

-- 型号（关联到品牌）
INSERT INTO dict_items (dict_type, item_name, item_value, parent_id, sort_order, is_active)
SELECT 'model', 'PowerEdge R740', 'r740', b.id, 1, true 
FROM dict_items b 
WHERE b.dict_type='brand' AND b.item_value='dell' 
AND EXISTS (SELECT 1 FROM dict_items pt WHERE pt.id = b.parent_id AND pt.item_value='server')
UNION ALL
SELECT 'model', 'PowerEdge R640', 'r640', b.id, 2, true 
FROM dict_items b 
WHERE b.dict_type='brand' AND b.item_value='dell' 
AND EXISTS (SELECT 1 FROM dict_items pt WHERE pt.id = b.parent_id AND pt.item_value='server')
UNION ALL
SELECT 'model', 'ProLiant DL380', 'dl380', b.id, 1, true 
FROM dict_items b 
WHERE b.dict_type='brand' AND b.item_value='hp' 
AND EXISTS (SELECT 1 FROM dict_items pt WHERE pt.id = b.parent_id AND pt.item_value='server');

-- 注释说明
COMMENT ON TABLE entity_products IS '实体产品关联表 - 线索/商机/项目的产品信息';
COMMENT ON COLUMN entity_products.entity_type IS '实体类型: lead/opportunity/project';
COMMENT ON COLUMN entity_products.entity_id IS '关联的实体ID';
COMMENT ON COLUMN entity_products.product_type_id IS '产品类型ID（关联dict_items）';
COMMENT ON COLUMN entity_products.brand_id IS '品牌ID（关联dict_items，可为空）';
COMMENT ON COLUMN entity_products.model_id IS '型号ID（关联dict_items，可为空）';