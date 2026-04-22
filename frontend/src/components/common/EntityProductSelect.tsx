import React, { useEffect } from 'react';
import { App, Card, Form, Select, Button, Space, InputNumber } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { useProductTypes, useBrandsByProductType, useModelsByBrand } from '../../hooks/useEntityProducts';

const { Option } = Select;

interface EntityProductSelectProps {
  entityType: 'lead' | 'opportunity' | 'project';
  entityId: number;
  level?: 1 | 2 | 3;
  onChange?: (products: Array<{
    product_type_id: number;
    brand_id?: number;
    model_id?: number;
    quantity?: number;
    unit_price?: number;
  }>) => void;
}

const EntityProductSelect: React.FC<EntityProductSelectProps> = ({
  entityType,
  entityId,
  level = 1,
  onChange,
}) => {
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const [products, setProducts] = React.useState<
    Array<{
      key: number;
      product_type_id: number | undefined;
      brand_id: number | undefined;
      model_id: number | undefined;
      quantity: number | undefined;
      unit_price: number | undefined;
    }>
  >([]);

  const { data: productTypes = [] } = useProductTypes();
  const { data: brands = [] } = useBrandsByProductType(products[0]?.product_type_id);
  const { data: models = [] } = useModelsByBrand(products[0]?.brand_id);

  const productTypeOptions = productTypes.map((item) => ({
    value: item.id,
    label: item.name,
  }));

  const brandOptions = brands.map((item) => ({
    value: item.id,
    label: item.name,
  }));

  const modelOptions = models.map((item) => ({
    value: item.id,
    label: item.name,
  }));

  useEffect(() => {
    if (onChange) {
      onChange(
        products
          .filter((p) => p.product_type_id && p.product_type_id > 0)
          .map((p) => ({
            product_type_id: p.product_type_id!,
            brand_id: level >= 2 ? p.brand_id : undefined,
            model_id: level >= 3 ? p.model_id : undefined,
            quantity: p.quantity,
            unit_price: p.unit_price,
          }))
      );
    }
  }, [products, level, onChange]);

  const addProduct = () => {
    const newProduct = {
      key: Date.now(),
      product_type_id: undefined,
      brand_id: undefined,
      model_id: undefined,
      quantity: 1,
      unit_price: 0,
    };
    setProducts([...products, newProduct]);
  };

  const removeProduct = (key: number) => {
    setProducts(products.filter((p) => p.key !== key));
  };

  const handleProductTypeChange = (key: number, value: number) => {
    setProducts(
      products.map((p) => {
        if (p.key === key) {
          return {
            ...p,
            product_type_id: value,
            brand_id: undefined,
            model_id: undefined,
          };
        }
        return p;
      })
    );
  };

  const handleBrandChange = (key: number, value: number) => {
    setProducts(
      products.map((p) => {
        if (p.key === key) {
          return { ...p, brand_id: value, model_id: undefined };
        }
        return p;
      })
    );
  };

  const handleModelChange = (key: number, value: number) => {
    setProducts(
      products.map((p) => {
        if (p.key === key) {
          return { ...p, model_id: value };
        }
        return p;
      })
    );
  };

  const handleQuantityChange = (key: number, value: number | null) => {
    setProducts(
      products.map((p) => {
        if (p.key === key) {
          return { ...p, quantity: value ?? 1 };
        }
        return p;
      })
    );
  };

  const handleUnitPriceChange = (key: number, value: number | null) => {
    setProducts(
      products.map((p) => {
        if (p.key === key) {
          return { ...p, unit_price: value ?? 0 };
        }
        return p;
      })
    );
  };

  const getBrandOptions = (productTypeId: number) => {
    return brands
      .filter((brand) => brand.parent_id === productTypeId)
      .map((item) => ({
        value: item.id,
        label: item.name,
      }));
  };

  const getModelOptions = (brandId: number) => {
    return models
      .filter((model) => model.parent_id === brandId)
      .map((item) => ({
        value: item.id,
        label: item.name,
      }));
  };

  return (
    <Card title="产品信息" style={{ marginBottom: 16 }}>
      {products.map((product, index) => (
        <Space
          key={product.key}
          style={{
            display: 'flex',
            flexDirection: 'row',
            alignItems: 'flex-start',
            marginBottom: 12,
            padding: 12,
            backgroundColor: '#f5f5f5',
            borderRadius: 4,
          }}
          split={<div style={{ width: 1, height: 40, backgroundColor: '#e0e0e0' }} />}
        >
          <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
            <Form.Item
              style={{ marginBottom: 4 }}
              rules={[{ required: true, message: '请选择产品类型' }]}
            >
              <Select
                placeholder="产品类型"
                style={{ width: '100%' }}
                value={product.product_type_id}
                onChange={(value) => handleProductTypeChange(product.key, value)}
                disabled={level < 1}
              >
                {productTypeOptions.map((opt) => (
                  <Option key={opt.value} value={opt.value}>
                    {opt.label}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            {level >= 2 && (
              <Form.Item style={{ marginBottom: 4 }}>
                <Select
                  placeholder="品牌"
                  style={{ width: '100%' }}
                  value={product.brand_id}
                  onChange={(value) => handleBrandChange(product.key, value)}
                  disabled={!product.product_type_id || level < 2}
                >
                  {getBrandOptions(product.product_type_id!).map((opt) => (
                    <Option key={opt.value} value={opt.value}>
                      {opt.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            )}

            {level >= 3 && (
              <Form.Item style={{ marginBottom: 4 }}>
                <Select
                  placeholder="型号"
                  style={{ width: '100%' }}
                  value={product.model_id}
                  onChange={(value) => handleModelChange(product.key, value)}
                  disabled={!product.brand_id || level < 3}
                >
                  {getModelOptions(product.brand_id!).map((opt) => (
                    <Option key={opt.value} value={opt.value}>
                      {opt.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            )}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', width: 120 }}>
            <Form.Item style={{ marginBottom: 4 }}>
              <InputNumber
                placeholder="数量"
                style={{ width: '100%' }}
                min={1}
                value={product.quantity}
                onChange={(value) => handleQuantityChange(product.key, value)}
              />
            </Form.Item>

            <Form.Item style={{ marginBottom: 4 }}>
              <InputNumber
                placeholder="单价"
                style={{ width: '100%' }}
                min={0}
                precision={2}
                value={product.unit_price}
                onChange={(value) => handleUnitPriceChange(product.key, value)}
              />
            </Form.Item>
          </div>

          {index > 0 && (
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => removeProduct(product.key)}
              style={{ marginTop: 8 }}
            />
          )}
        </Space>
      ))}

      <Button type="dashed" onClick={addProduct} icon={<PlusOutlined />}>
        添加产品
      </Button>
    </Card>
  );
};

export default EntityProductSelect;
