import React, { useState } from 'react';
import { App, Button, Table, Space, Tag, Input, Select, Dropdown, Descriptions, Empty } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, MenuOutlined } from '@ant-design/icons';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useSelector } from 'react-redux';
import type { RootState } from '../store/store';
import { useCustomers, useDeleteCustomer } from '../hooks/useCustomers';
import { CustomerRead } from '../types/customer';
import PageScaffold from '../components/common/PageScaffold';
import CustomerForm from '../components/forms/CustomerForm';

const { Option } = Select;

const CustomerListPage: React.FC = () => {
  const { message, modal } = App.useApp();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { capabilities } = useSelector((state: RootState) => state.auth);
  
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(searchParams.get('new') === 'true');

  const canCreateCustomer = Boolean(capabilities['customer:create']);

  const { data: customers = [], isLoading } = useCustomers();
  const deleteMutation = useDeleteCustomer();

  const filteredCustomers = customers.filter(customer => {
    const matchesSearch = !searchText || 
      customer.customer_name.toLowerCase().includes(searchText.toLowerCase()) ||
      customer.customer_code.toLowerCase().includes(searchText.toLowerCase());
    const matchesStatus = !statusFilter || customer.customer_status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case '成交客户': return 'green';
      case '潜在客户': return 'blue';
      case '意向客户': return 'gold';
      case '流失客户': return 'red';
      default: return 'default';
    }
  };

  const handleCreate = () => {
    setIsDrawerOpen(true);
  };

  const handleView = (customer: CustomerRead) => {
    navigate(`/customers/${customer.id}/full`);
  };

  const handleEdit = (customer: CustomerRead) => {
    navigate(`/customers/${customer.id}/full`);
  };

  const handleDelete = (customerId: number) => {
    modal.confirm({
      title: '确定删除该客户吗？',
      content: '此操作不可恢复',
      onOk: async () => {
        try {
          await deleteMutation.mutateAsync(customerId);
          message.success('客户删除成功');
        } catch (error: any) {
          if (error?.response?.data?.detail) {
            message.error(error.response.data.detail);
          }
        }
      }
    });
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
      width: 200,
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
      title: '负责人',
      dataIndex: 'owner_name',
      key: 'owner_name',
      width: 100,
    },
    {
      title: '状态',
      dataIndex: 'customer_status',
      key: 'customer_status',
      width: 100,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>{status}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: any, record: CustomerRead) => (
        <Dropdown
          menu={{
            items: [
              { key: 'view', label: '查看', icon: <EyeOutlined /> },
              { key: 'edit', label: '编辑', icon: <EditOutlined /> },
              { key: 'delete', label: '删除', icon: <DeleteOutlined />, danger: true },
            ],
            onClick: ({ key }) => {
              if (key === 'view') handleView(record);
              else if (key === 'edit') handleEdit(record);
              else if (key === 'delete') handleDelete(record.id);
            },
          }}
          trigger={['click']}
        >
          <Button size="small" icon={<MenuOutlined />} />
        </Dropdown>
      ),
    },
  ];

  return (
    <PageScaffold
      title="终端客户"
      breadcrumbItems={[{ title: '首页', href: '/dashboard' }, { title: '终端客户' }]}
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate} disabled={!canCreateCustomer}>
          新建客户
        </Button>
      }
    >
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Input.Search
            placeholder="搜索客户名称或编号"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 200 }}
            allowClear
          />
          <Select
            placeholder="筛选状态"
            value={statusFilter}
            onChange={setStatusFilter}
            style={{ width: 150 }}
            allowClear
          >
            <Option value="成交客户">成交客户</Option>
            <Option value="潜在客户">潜在客户</Option>
            <Option value="意向客户">意向客户</Option>
            <Option value="流失客户">流失客户</Option>
          </Select>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={filteredCustomers}
        rowKey="id"
        loading={isLoading}
        pagination={{ pageSize: 20 }}
        scroll={{ x: 700 }}
        locale={{
          emptyText: (
            <Empty description="暂无客户数据" image={Empty.PRESENTED_IMAGE_SIMPLE}>
              <Button type="primary" onClick={handleCreate} disabled={!canCreateCustomer}>+ 新增第一条客户</Button>
            </Empty>
          )
        }}
      />
      <CustomerForm open={isDrawerOpen} onCancel={() => setIsDrawerOpen(false)} />
    </PageScaffold>
  );
};

export default CustomerListPage;