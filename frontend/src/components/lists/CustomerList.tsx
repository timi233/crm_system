import React, { useState } from 'react';
import { Table, Button, Space, Tag, Card, Input, Select } from 'antd';
import { CustomerRead } from '../../types/customer';
import { useQuery } from '@tanstack/react-query';
import api from '../../services/api';
import { Link } from 'react-router-dom';

const { Search } = Input;
const { Option } = Select;

interface CustomerListProps {
  onSelectCustomer?: (customer: CustomerRead) => void;
}

const CustomerList: React.FC<CustomerListProps> = ({ onSelectCustomer }) => {
  const [searchText, setSearchText] = useState('');
  const [industryFilter, setIndustryFilter] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  
  const { data: customers = [], isLoading } = useQuery({
    queryKey: ['customers'],
    queryFn: () => api.get('/customers').then(res => res.data),
  });
  
  // Filter customers based on search and filters
  const filteredCustomers = customers.filter(customer => {
    const matchesSearch = !searchText || 
      customer.customer_name.toLowerCase().includes(searchText.toLowerCase()) ||
      customer.customer_nickname?.toLowerCase().includes(searchText.toLowerCase());
    
    const matchesIndustry = !industryFilter || customer.customer_industry === industryFilter;
    const matchesStatus = !statusFilter || customer.customer_status === statusFilter;
    
    return matchesSearch && matchesIndustry && matchesStatus;
  });
  
  const industryOptions: string[] = Array.from(
    new Set(customers.map((c: CustomerRead) => c.customer_industry))
  ).sort() as string[];
  
  const statusOptions: string[] = Array.from(
    new Set(customers.map((c: CustomerRead) => c.customer_status))
  ).sort() as string[];
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Active':
        return 'green';
      case 'Potential':
        return 'blue';
      case 'Existing':
        return 'gold';
      case 'Lost':
        return 'red';
      default:
        return 'default';
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
        <Link to={`/customers/${record.id}`}>
          {text}
        </Link>
      ),
    },
    {
      title: '简称',
      dataIndex: 'customer_nickname',
      key: 'customer_nickname',
      width: 100,
    },
    {
      title: '行业',
      dataIndex: 'customer_industry',
      key: 'customer_industry',
      width: 120,
    },
    {
      title: '区域',
      dataIndex: 'customer_region',
      key: 'customer_region',
      width: 100,
    },
    {
      title: '负责人',
      dataIndex: 'customer_owner_id',
      key: 'customer_owner_id',
      width: 100,
      // This would be populated with actual user names in a real implementation
      render: (userId: number) => `用户 ${userId}`,
    },
    {
      title: '状态',
      dataIndex: 'customer_status',
      key: 'customer_status',
      width: 100,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {status}
        </Tag>
      ),
    },
    {
      title: '维保到期',
      dataIndex: 'maintenance_expiry',
      key: 'maintenance_expiry',
      width: 120,
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: CustomerRead) => (
        <Space size="middle">
          <Button 
            type="link" 
            onClick={() => onSelectCustomer?.(record)}
          >
            编辑
          </Button>
          <Button type="link" danger>
            删除
          </Button>
        </Space>
      ),
    },
  ];
  
  return (
    <Card 
      title="终端客户列表"
      extra={
        <Link to="/customers/new">
          <Button type="primary">
            新建客户
          </Button>
        </Link>
      }
    >
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Search
            placeholder="搜索客户名称或简称"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 200 }}
          />
          <Select
            placeholder="筛选行业"
            value={industryFilter}
            onChange={setIndustryFilter}
            style={{ width: 150 }}
            allowClear
          >
            {industryOptions.map(industry => (
              <Option key={industry} value={industry}>
                {industry}
              </Option>
            ))}
          </Select>
          <Select
            placeholder="筛选状态"
            value={statusFilter}
            onChange={setStatusFilter}
            style={{ width: 150 }}
            allowClear
          >
            {statusOptions.map(status => (
              <Option key={status} value={status}>
                {status}
              </Option>
            ))}
          </Select>
        </Space>
      </div>
      
      <Table
        columns={columns}
        dataSource={filteredCustomers}
        rowKey="id"
        loading={isLoading}
        pagination={{ pageSize: 20 }}
        scroll={{ x: 1200 }}
      />
    </Card>
  );
};

export default CustomerList;