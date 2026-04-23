import React, { useState } from 'react';
import { App, Button, Card, Table, Space, Input, Select, Tag, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import type { RootState } from '../store/store';
import { useCustomers, useDeleteCustomer, useCreateCustomer, useUpdateCustomer } from '../hooks/useCustomers';
import { CustomerRead } from '../types/customer';
import CustomerDrawer from '../components/modals/CustomerDrawer';

const { Search } = Input;
const { Option } = Select;

const CustomerListPage: React.FC = () => {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const { capabilities } = useSelector((state: RootState) => state.auth);
  
  const [searchText, setSearchText] = useState('');
  const [filters, setFilters] = useState({ status: 'all' });
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<CustomerRead | null>(null);

  const { data: customers = [], isLoading, refetch } = useCustomers();
  const deleteMutation = useDeleteCustomer();
  const createCustomerMutation = useCreateCustomer();
  const updateCustomerMutation = useUpdateCustomer();

  const canManage = Boolean(capabilities['customer:manage']);

  const filteredCustomers = customers.filter(customer => {
    const matchesSearch = !searchText || 
      customer.customer_name.toLowerCase().includes(searchText.toLowerCase()) ||
      customer.customer_code.toLowerCase().includes(searchText.toLowerCase());
    const matchesStatus = filters.status === 'all' || customer.customer_status === filters.status;
    return matchesSearch && matchesStatus;
  });

  const handleCreate = () => {
    setEditingCustomer(null);
    setDrawerVisible(true);
  };

  const handleEdit = (customer: CustomerRead) => {
    setEditingCustomer(customer);
    setDrawerVisible(true);
  };

  const handleDelete = async (customerId: number, customerName: string) => {
    try {
      await deleteMutation.mutateAsync(customerId);
      message.success(`客户 ${customerName} 已删除`);
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  const handleSave = async (customerData: any) => {
    try {
      if (editingCustomer) {
        // 更新客户
        await updateCustomerMutation.mutateAsync({
          id: editingCustomer.id,
          customer: customerData
        });
        message.success('客户更新成功');
      } else {
        // 创建客户
        await createCustomerMutation.mutateAsync(customerData);
        message.success('客户创建成功');
      }
      setDrawerVisible(false);
      refetch();
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      } else {
        message.error('保存失败，请重试');
      }
    }
  };

  const columns = [
    {
      title: '客户编号',
      dataIndex: 'customer_code',
      key: 'customer_code',
      width: 120,
    },
    {
      title: '客户名称',
      dataIndex: 'customer_name',
      key: 'customer_name',
      render: (text: string, record: CustomerRead) => (
        <a onClick={() => navigate(`/customers/${record.id}/full`)}>{text}</a>
      ),
    },
    {
      title: '行业',
      dataIndex: 'customer_industry',
      key: 'customer_industry',
      width: 120,
    },
    {
      title: '状态',
      dataIndex: 'customer_status',
      key: 'customer_status',
      width: 100,
      render: (status: string) => (
        <Tag color={status === '活跃' ? 'green' : status === '潜在' ? 'blue' : 'default'}>
          {status}
        </Tag>
      ),
    },
    {
      title: '负责人',
      dataIndex: 'owner_name',
      key: 'owner_name',
      width: 120,
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      render: (_: any, record: CustomerRead) => (
        <Space size="middle">
          <Button 
            icon={<EyeOutlined />} 
            size="small" 
            onClick={() => navigate(`/customers/${record.id}/full`)}
          >
            查看
          </Button>
          {canManage && (
            <>
              <Button 
                icon={<EditOutlined />} 
                size="small" 
                onClick={() => handleEdit(record)}
              >
                编辑
              </Button>
              <Popconfirm
                title={`确定要删除客户 "${record.customer_name}" 吗？`}
                onConfirm={() => handleDelete(record.id, record.customer_name)}
                okText="确定"
                cancelText="取消"
              >
                <Button icon={<DeleteOutlined />} size="small" danger>
                  删除
                </Button>
              </Popconfirm>
            </>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title="客户管理"
        extra={
          canManage && (
            <Button 
              type="primary" 
              icon={<PlusOutlined />} 
              onClick={handleCreate}
            >
              新建客户
            </Button>
          )
        }
      >
        <div style={{ marginBottom: 16, display: 'flex', gap: 16 }}>
          <Search
            placeholder="搜索客户名称或编号"
            allowClear
            onSearch={setSearchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 300 }}
          />
          <Select
            value={filters.status}
            onChange={(value) => setFilters({ ...filters, status: value })}
            style={{ width: 150 }}
          >
            <Option value="all">全部状态</Option>
            <Option value="潜在">潜在</Option>
            <Option value="活跃">活跃</Option>
            <Option value="休眠">休眠</Option>
            <Option value="流失">流失</Option>
          </Select>
        </div>
        
        <Table
          columns={columns}
          dataSource={filteredCustomers}
          loading={isLoading}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1000 }}
        />
      </Card>

      <CustomerDrawer
        visible={drawerVisible}
        customer={editingCustomer}
        onSave={handleSave}
        onCancel={() => setDrawerVisible(false)}
      />
    </div>
  );
};

export default CustomerListPage;