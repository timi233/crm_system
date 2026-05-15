import React, { useState } from 'react';
import { App, Button, Table, Space, Input, Select, Tag, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import type { RootState } from '../store/store';
import { useCustomers, useDeleteCustomer, useCreateCustomer, useUpdateCustomer } from '../hooks/useCustomers';
import CustomerModal from '../components/modals/CustomerModal';
import PageScaffold from '../components/common/PageScaffold';

const { Option } = Select;

const CustomerListPage: React.FC = () => {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const { capabilities } = useSelector((state: RootState) => state.auth);

  const [searchText, setSearchText] = useState('');
  const [filters, setFilters] = useState({ status: 'all' });
  const [modalVisible, setModalVisible] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<any | null>(null);

  const { data: customers = [], isLoading, refetch } = useCustomers();
  const deleteMutation = useDeleteCustomer();
  const createMutation = useCreateCustomer();
  const updateMutation = useUpdateCustomer();

  const canManage = Boolean(capabilities['customer:manage']);

  const filteredCustomers = customers.filter(customer => {
    const matchesSearch = !searchText ||
      customer.customer_name.toLowerCase().includes(searchText.toLowerCase()) ||
      (customer.customer_code && customer.customer_code.toLowerCase().includes(searchText.toLowerCase()));
    const matchesStatus = filters.status === 'all' || customer.customer_status === filters.status;
    return matchesSearch && matchesStatus;
  });

  const handleCreate = () => {
    setEditingCustomer(null);
    setModalVisible(true);
  };

  const handleEdit = (customer: any) => {
    setEditingCustomer(customer);
    setModalVisible(true);
  };

  const handleDelete = async (customerId: number, customerName: string) => {
    try {
      await deleteMutation.mutateAsync(customerId);
      message.success(`客户 ${customerName} 已删除`);
      refetch();
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  const handleSave = async (customerData: any) => {
    try {
      if (editingCustomer) {
        await updateMutation.mutateAsync({
          id: editingCustomer.id,
          customer: customerData
        });
        message.success('客户信息更新成功');
      } else {
        await createMutation.mutateAsync(customerData);
        message.success('客户创建成功');
      }
      setModalVisible(false);
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
      width: 140,
    },
    {
      title: '客户名称',
      dataIndex: 'customer_name',
      key: 'customer_name',
      render: (text: string, record: any) => (
        <a onClick={() => navigate(`/customers/${record.id}/full`)} style={{ fontWeight: 600 }}>{text}</a>
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
        <Tag color={status === '成交客户' || status === '活跃' ? 'success' : status === '意向客户' || status === '潜在' ? 'processing' : 'default'} style={{ border: 'none' }}>
          {status}
        </Tag>
      ),
    },
    {
      title: '负责人',
      dataIndex: 'customer_owner_name',
      key: 'customer_owner_name',
      width: 120,
      render: (name: string, record: any) => name || record.owner_name || '-',
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      render: (_: any, record: any) => (
        <Space size="middle">
          <Button
            icon={<EyeOutlined />}
            size="small"
            onClick={() => navigate(`/customers/${record.id}/full`)}
          >
            详情
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
                okButtonProps={{ danger: true }}
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
    <PageScaffold
      title="终端客户管理"
      breadcrumbItems={[{ title: '首页' }, { title: '终端客户' }]}
      extra={
        canManage && (
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreate}
            size="large"
            className="btn--gradient"
            style={{ height: '40px', padding: '0 20px' }}
          >
            新建客户
          </Button>
        )
      }
      filters={
        <Space size={16} wrap>
          <Input.Search
            placeholder="搜索客户名称或编号"
            allowClear
            onSearch={setSearchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 280 }}
            size="middle"
          />
          <Select
            value={filters.status}
            onChange={(value) => setFilters({ ...filters, status: value })}
            style={{ width: 180 }}
            size="middle"
          >
            <Option value="all">全部状态</Option>
            <Option value="潜在">潜在</Option>
            <Option value="活跃">活跃</Option>
            <Option value="意向客户">意向客户</Option>
            <Option value="成交客户">成交客户</Option>
            <Option value="休眠">休眠</Option>
            <Option value="流失">流失</Option>
          </Select>
        </Space>
      }
    >
      <Table
        columns={columns}
        dataSource={filteredCustomers}
        loading={isLoading}
        rowKey="id"
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条数据`,
        }}
        scroll={{ x: 1000 }}
        className="customer-table"
        bordered={false}
      />

      <CustomerModal
        visible={modalVisible}
        customer={editingCustomer}
        onSave={handleSave}
        onCancel={() => setModalVisible(false)}
      />
    </PageScaffold>
  );
};

export default CustomerListPage;
