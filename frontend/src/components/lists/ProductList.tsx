import React, { useEffect } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';

const { Option } = Select;
const { confirm } = Modal;

const ProductList: React.FC = () => {
  const [products, setProducts] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [isModalVisible, setIsModalVisible] = React.useState(false);
  const [editingProduct, setEditingProduct] = React.useState<any>(null);
  const [form] = Form.useForm();

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8001/products', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setProducts(data);
      }
    } catch (error) {
      console.error('Failed to fetch products:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const handleCreate = () => {
    setEditingProduct(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (product: any) => {
    setEditingProduct(product);
    form.setFieldsValue(product);
    setIsModalVisible(true);
  };

  const handleDelete = (productId: number) => {
    confirm({
      title: '确定删除该产品吗？',
      content: '此操作不可恢复',
      onOk: async () => {
        try {
          const token = localStorage.getItem('token');
          await fetch(`http://localhost:8001/products/${productId}`, {
            method: 'DELETE',
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          fetchProducts();
        } catch (error) {
          console.error('Failed to delete product:', error);
        }
      }
    });
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      const token = localStorage.getItem('token');
      
      if (editingProduct) {
        // Update existing product
        await fetch(`http://localhost:8001/products/${editingProduct.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(values)
        });
      } else {
        // Create new product
        await fetch('http://localhost:8001/products', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(values)
        });
      }
      
      setIsModalVisible(false);
      fetchProducts();
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
    },
    {
      title: '单位',
      dataIndex: 'unit',
      key: 'unit',
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
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2>产品字典列表</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建产品
        </Button>
      </div>
      
      <Table 
        columns={columns} 
        dataSource={products} 
        loading={loading}
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
            <Select>
              <Option value="软件">软件</Option>
              <Option value="硬件">硬件</Option>
              <Option value="服务">服务</Option>
              <Option value="其他">其他</Option>
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
    </div>
  );
};

export default ProductList;