import React, { useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select, Card, Cascader, Row, Col, App, Tag } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useProducts, useCreateProduct, useUpdateProduct, useDeleteProduct } from '../../hooks/useProducts';
import { useProductTypeCascader, useDictItems } from '../../hooks/useDictItems';
import PageScaffold from '../../components/common/PageScaffold';
import PageModal from '../../components/common/PageModal';

const { Option } = Select;

const ProductList: React.FC = () => {
  const { message, modal } = App.useApp();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingProduct, setEditingProduct] = useState<any>(null);
  const [searchText, setSearchText] = useState('');
  const [productTypeFilter, setProductTypeFilter] = useState<string | null>(null);
  const [isActiveFilter, setIsActiveFilter] = useState<boolean | null>(null);
  const [form] = Form.useForm();

  const { data: productTypeOptions = [] } = useProductTypeCascader();
  const { data: brandItems = [] } = useDictItems('产品品牌');
  const { data: products = [], isLoading } = useProducts();

  const createMutation = useCreateProduct();
  const updateMutation = useUpdateProduct();
  const deleteMutation = useDeleteProduct();

  const filteredProducts = products.filter(p => {
    const matchesSearch = !searchText || p.product_name.toLowerCase().includes(searchText.toLowerCase());
    const matchesType = !productTypeFilter || p.product_type === productTypeFilter;
    const matchesActive = isActiveFilter === null || p.is_active === isActiveFilter;
    return matchesSearch && matchesType && matchesActive;
  });

  const productTypeLeafOptions: { label: string; value: string }[] = [];
  const findLeafOptions = (options: any[]) => {
    options.forEach(opt => {
      if (!opt.children || opt.children.length === 0) {
        productTypeLeafOptions.push({ label: opt.label, value: opt.value });
      } else {
        findLeafOptions(opt.children);
      }
    });
  };
  findLeafOptions(productTypeOptions);

  const handleCreate = () => {
    setEditingProduct(null);
    form.resetFields();
    form.setFieldsValue({ is_active: true });
    setIsModalVisible(true);
  };

  const handleEdit = (product: any) => {
    setEditingProduct(product);
    form.setFieldsValue(product);
    setIsModalVisible(true);
  };

  const handleDelete = (id: number) => {
    modal.confirm({
      title: '确定删除该产品吗？',
      content: '此操作不可恢复',
      okType: 'danger',
      onOk: async () => {
        try {
          await deleteMutation.mutateAsync(id);
          message.success('产品已删除');
        } catch (error) {}
      }
    });
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      if (editingProduct) {
        await updateMutation.mutateAsync({ id: editingProduct.id, product: values });
        message.success('产品信息已更新');
      } else {
        await createMutation.mutateAsync(values);
        message.success('产品已创建');
      }
      setIsModalVisible(false);
      form.resetFields();
    } catch (error) {}
  };

  const columns = [
    {
      title: '产品名称',
      dataIndex: 'product_name',
      key: 'product_name',
    },
    {
      title: '产品类型',
      dataIndex: 'product_type',
      key: 'product_type',
      render: (type: string) => <Tag color="blue" style={{ border: 'none' }}>{type}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (
        <Tag color={active ? 'success' : 'default'} style={{ border: 'none' }}>
          {active ? '激活' : '停用'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: any) => (
        <Space size="middle">
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)}>删除</Button>
        </Space>
      ),
    },
  ];

  return (
    <PageScaffold
      title="产品字典"
      breadcrumbItems={[{ title: '首页' }, { title: '产品字典' }]}
      extra={
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleCreate}
          size="large"
          className="btn--gradient"
          style={{ height: '40px', padding: '0 20px' }}
        >
          新建产品
        </Button>
      }
      filters={
        <Space size={16} wrap>
          <Input.Search
            placeholder="搜索产品名称"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 280 }}
            size="middle"
          />
          <Select
            placeholder="筛选产品类型"
            value={productTypeFilter}
            onChange={setProductTypeFilter}
            style={{ width: 220 }}
            allowClear
            showSearch
          >
            {productTypeLeafOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>{opt.label}</Option>
            ))}
          </Select>
          <Select
            placeholder="状态筛选"
            value={isActiveFilter}
            onChange={setIsActiveFilter}
            style={{ width: 150 }}
            allowClear
          >
            <Option value={true}>激活</Option>
            <Option value={false}>停用</Option>
          </Select>
        </Space>
      }
    >
      <Table
        columns={columns}
        dataSource={filteredProducts}
        loading={isLoading}
        rowKey="id"
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条数据`,
        }}
        className="customer-table"
        bordered={false}
      />

      <PageModal
        title={editingProduct ? '编辑产品信息' : '添加新产品字典'}
        open={isModalVisible}
        onClose={() => setIsModalVisible(false)}
        width={560}
        footer={[
          <Button key="cancel" onClick={() => setIsModalVisible(false)}>
            取消
          </Button>,
          <Button
            key="submit"
            type="primary"
            className="btn--gradient"
            onClick={handleSave}
            loading={createMutation.isPending || updateMutation.isPending}
          >
            确认并保存
          </Button>
        ]}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="product_name"
            label="产品名称"
            rules={[{ required: true, message: '请输入产品名称!' }]}
          >
            <Input placeholder="输入产品或服务全称" />
          </Form.Item>

          <Form.Item
            name="product_type"
            label="产品分类"
            rules={[{ required: true, message: '请选择产品分类!' }]}
          >
            <Select placeholder="选择所属分类" showSearch>
              {productTypeLeafOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="is_active" label="当前状态" valuePropName="checked">
            <Select>
              <Option value={true}>激活 (正常使用)</Option>
              <Option value={false}>停用 (暂时下架)</Option>
            </Select>
          </Form.Item>

          <Form.Item name="notes" label="规格说明">
            <Input.TextArea rows={3} placeholder="录入产品详细参数或业务说明..." />
          </Form.Item>
        </Form>
      </PageModal>
    </PageScaffold>
  );
};

export default ProductList;
