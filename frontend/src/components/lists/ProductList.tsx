import React, { useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select, Card, Cascader } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useProducts, useCreateProduct, useUpdateProduct, useDeleteProduct } from '../../hooks/useProducts';
import { useProductTypeCascader, useDictItems } from '../../hooks/useDictItems';

const { Option } = Select;
const { Search } = Input;
const { confirm } = Modal;

const ProductList: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingProduct, setEditingProduct] = useState<any>(null);
  const [searchText, setSearchText] = useState('');
  const [productTypeFilter, setProductTypeFilter] = useState<string | null>(null);
  const [isActiveFilter, setIsActiveFilter] = useState<boolean | null>(null);
  const [form] = Form.useForm();

  const { data: products = [], isLoading } = useProducts();
  const { data: productTypeOptions = [] } = useProductTypeCascader();
  const { data: brandItems = [] } = useDictItems('产品品牌');
  
  const brandOptions = brandItems.map(item => ({
    value: item.name,
    label: item.name,
  }));
  
  const filteredProducts = products.filter(product => {
    const matchesSearch = !searchText ||
      product.product_name?.toLowerCase().includes(searchText.toLowerCase());

    const matchesProductType = !productTypeFilter || 
      product.product_type?.includes(productTypeFilter);
    const matchesIsActive = isActiveFilter === null || product.is_active === isActiveFilter;

    return matchesSearch && matchesProductType && matchesIsActive;
  });
  
  const productTypeLeafOptions = productTypeOptions.flatMap(level1 => 
    (level1.children || []).flatMap(level2 => 
      (level2.children || []).map(level3 => ({
        value: level3.value,
        label: `${level1.label} / ${level2.label} / ${level3.label}`,
      }))
    )
  );
  
  const createMutation = useCreateProduct();
  const updateMutation = useUpdateProduct();
  const deleteMutation = useDeleteProduct();

  const handleCreate = () => {
    setEditingProduct(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (product: any) => {
    setEditingProduct(product);
    const typeArray = product.product_type ? product.product_type.split(' / ') : [];
    form.setFieldsValue({
      ...product,
      product_type: typeArray.length > 0 ? typeArray : undefined,
    });
    setIsModalVisible(true);
  };

  const handleDelete = (productId: number) => {
    confirm({
      title: '确定删除该产品吗？',
      content: '此操作不可恢复',
      onOk: async () => {
        try {
          await deleteMutation.mutateAsync(productId);
        } catch (error) {
          console.error('Failed to delete product:', error);
        }
      }
    });
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      const submitData = {
        ...values,
        product_type: values.product_type ? values.product_type.join(' / ') : '',
      };
      
      if (editingProduct) {
        await updateMutation.mutateAsync({ id: editingProduct.id, product: submitData });
      } else {
        await createMutation.mutateAsync(submitData);
      }
      
      setIsModalVisible(false);
      form.resetFields();
    } catch (error) {
      console.error('Failed to save product:', error);
    }
  };

  const columns = [
    {
      title: '产品编号',
      dataIndex: 'product_code',
      key: 'product_code',
    },
    {
      title: '产品名称',
      dataIndex: 'product_name',
      key: 'product_name',
    },
    {
      title: '产品类型',
      dataIndex: 'product_type',
      key: 'product_type',
      width: 200,
    },
    {
      title: '品牌',
      dataIndex: 'brand_manufacturer',
      key: 'brand_manufacturer',
    },
    {
      title: '销售价格',
      dataIndex: 'sales_price',
      key: 'sales_price',
      render: (price: number) => price?.toLocaleString() || '-',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space size="middle">
          <Button icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Button icon={<DeleteOutlined />} danger onClick={() => handleDelete(record.id)}>
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <Card
      title="产品字典列表"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建产品
        </Button>
      }
    >
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Search
            placeholder="搜索产品名称"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 200 }}
          />
          <Select
            placeholder="筛选产品类型"
            value={productTypeFilter}
            onChange={setProductTypeFilter}
            style={{ width: 200 }}
            allowClear
            showSearch
          >
            {productTypeLeafOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>
                {opt.label}
              </Option>
            ))}
          </Select>
          <Select
            placeholder="筛选状态"
            value={isActiveFilter}
            onChange={setIsActiveFilter}
            style={{ width: 150 }}
            allowClear
          >
            <Option value={true}>激活</Option>
            <Option value={false}>停用</Option>
          </Select>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={filteredProducts}
        loading={isLoading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />
      
      <Modal
        title={editingProduct ? '编辑产品' : '新建产品'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => setIsModalVisible(false)}
        okText="保存"
        cancelText="取消"
        width={600}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
      >
        <Form form={form} layout="vertical">
          <Form.Item 
            name="product_name" 
            label="产品名称" 
            rules={[{ required: true, message: '请输入产品名称!' }]}
          >
            <Input />
          </Form.Item>
          
          <Form.Item 
            name="product_type" 
            label="产品类型" 
            rules={[{ required: true, message: '请选择产品类型!' }]}
          >
            <Cascader
              options={productTypeOptions}
              placeholder="请选择产品类型"
              showSearch
            />
          </Form.Item>
          
          <Form.Item 
            name="brand_manufacturer" 
            label="品牌" 
            rules={[{ required: true, message: '请选择品牌!' }]}
          >
            <Select placeholder="请选择品牌" showSearch>
              {brandOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>
                  {opt.label}
                </Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item name="unit" label="单位">
            <Input placeholder="例如：套、个、年等" />
          </Form.Item>
          
          <Form.Item name="sales_price" label="销售价格">
            <Input type="number" />
          </Form.Item>
          
          <Form.Item name="description" label="产品描述">
            <Input.TextArea rows={4} />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default ProductList;
