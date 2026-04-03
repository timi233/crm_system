import React, { useState } from 'react';
import { Table, Button, Space, Tag, Card, Input, Select, Modal, Form, DatePicker, Cascader, message } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { RootState } from '../../store/store';
import api from '../../services/api';
import { useRegionCascader, useDictItems } from '../../hooks/useDictItems';
import { useUsers } from '../../hooks/useUsers';
import { useChannels } from '../../hooks/useChannels';

const { Search } = Input;
const { Option } = Select;
const { confirm } = Modal;

type Customer = {
  id: number;
  customer_code: string;
  customer_name: string;
  credit_code: string;
  customer_industry: string;
  customer_region: string;
  customer_owner_id: number;
  customer_owner_name?: string;
  channel_id?: number;
  channel_name?: string;
  main_contact?: string;
  phone?: string;
  customer_status: string;
  maintenance_expiry?: string;
  notes?: string;
};

const checkCreditCodeExists = async (creditCode: string, excludeId?: number): Promise<boolean> => {
  try {
    const params = new URLSearchParams({ credit_code: creditCode });
    if (excludeId) params.append('exclude_id', String(excludeId));
    const response = await api.get(`/customers/check-credit-code?${params.toString()}`);
    return response.data.exists;
  } catch (error) {
    return false;
  }
};

const CustomerList: React.FC = () => {
  const navigate = useNavigate();
  const [searchText, setSearchText] = useState('');
  const [industryFilter, setIndustryFilter] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null);
  const [form] = Form.useForm();

  const { user } = useSelector((state: RootState) => state.auth);
  const isAdmin = user?.role === 'admin';

  const queryClient = useQueryClient();
  const { data: regionOptions = [] } = useRegionCascader();
  const { data: industryItems = [] } = useDictItems('客户行业');
  const { data: statusItems = [] } = useDictItems('客户状态');
  const { data: users = [] } = useUsers();
  const { data: channels = [] } = useChannels();

  const industryOptions = industryItems.map(item => ({ value: item.name, label: item.name }));
  const statusOptions = statusItems.map(item => ({ value: item.name, label: item.name }));
  const userOptions = users.map(user => ({ value: user.id, label: user.name }));
  const channelOptions = channels.map(channel => ({ value: channel.id, label: channel.company_name }));

  const { data: customers = [], isLoading } = useQuery({
    queryKey: ['customers'],
    queryFn: () => api.get<Customer[]>('/customers').then(res => res.data),
  });

  const createMutation = useMutation({
    mutationFn: (customer: Omit<Customer, 'id' | 'customer_code'>) => 
      api.post<Customer>('/customers', customer).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, customer }: { id: number; customer: Omit<Customer, 'id' | 'customer_code'> }) => 
      api.put<Customer>(`/customers/${id}`, customer).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/customers/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
    },
  });

  const filteredCustomers = customers.filter(customer => {
    const matchesSearch = !searchText || 
      customer.customer_name.toLowerCase().includes(searchText.toLowerCase()) ||
      customer.credit_code?.toLowerCase().includes(searchText.toLowerCase());
    
    const matchesIndustry = !industryFilter || customer.customer_industry === industryFilter;
    const matchesStatus = !statusFilter || customer.customer_status === statusFilter;
    
    return matchesSearch && matchesIndustry && matchesStatus;
  });
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case '成交客户':
        return 'green';
      case '潜在客户':
        return 'blue';
      case '意向客户':
        return 'gold';
      case '流失客户':
        return 'red';
      default:
        return 'default';
    }
  };

  const handleCreate = () => {
    setEditingCustomer(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (customer: Customer) => {
    setEditingCustomer(customer);
    const regionArray = customer.customer_region ? customer.customer_region.split('/') : [];
    form.setFieldsValue({
      ...customer,
      customer_region: regionArray.length > 0 ? regionArray : undefined,
    });
    setIsModalVisible(true);
  };

  const handleView = (customer: Customer) => {
    navigate(`/customers/${customer.id}/full`);
  };

  const handleDelete = (customerId: number) => {
    confirm({
      title: '确定删除该客户吗？',
      content: '此操作不可恢复',
      onOk: async () => {
        try {
          await deleteMutation.mutateAsync(customerId);
        } catch (error) {
          console.error('Failed to delete customer:', error);
        }
      }
    });
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      const submitData = {
        ...values,
        customer_region: values.customer_region ? values.customer_region.join('/') : '',
        maintenance_expiry: values.maintenance_expiry?.format('YYYY-MM-DD'),
      };
      
      if (editingCustomer) {
        await updateMutation.mutateAsync({ id: editingCustomer.id, customer: submitData });
      } else {
        await createMutation.mutateAsync(submitData);
      }
      
      setIsModalVisible(false);
      form.resetFields();
    } catch (error: any) {
      console.error('Failed to save customer:', error);
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };
  
  const baseColumns = [
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
    },
    {
      title: '统一社会信用代码',
      dataIndex: 'credit_code',
      key: 'credit_code',
      width: 180,
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
      dataIndex: 'customer_owner_name',
      key: 'customer_owner_name',
      width: 100,
    },
    {
      title: '关联渠道',
      dataIndex: 'channel_name',
      key: 'channel_name',
      width: 120,
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
      title: '操作',
      key: 'action',
      width: 200,
      render: (_: any, record: Customer) => (
        <Space size="small">
          <Button size="small" icon={<EyeOutlined />} onClick={() => handleView(record)}>
            查看
          </Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Button size="small" icon={<DeleteOutlined />} danger onClick={() => handleDelete(record.id)}>
            删除
          </Button>
        </Space>
      ),
    },
  ];

  const maintenanceColumn = {
    title: '维保到期',
    dataIndex: 'maintenance_expiry',
    key: 'maintenance_expiry',
    width: 120,
  };

  const columns = isAdmin
    ? [...baseColumns.slice(0, -1), maintenanceColumn, baseColumns[baseColumns.length - 1]]
    : baseColumns;

  return (
    <Card 
      title="终端客户列表"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建客户
        </Button>
      }
    >
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Search
            placeholder="搜索客户名称或信用代码"
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
            {industryOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>
                {opt.label}
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
            {statusOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>
                {opt.label}
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

      <Modal
        title={editingCustomer ? '编辑客户' : '新建客户'}
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
            name="customer_name" 
            label="客户名称" 
            rules={[{ required: true, message: '请输入客户名称!' }]}
          >
            <Input />
          </Form.Item>
          
          <Form.Item 
            name="credit_code" 
            label="统一社会信用代码" 
            rules={[
              { required: true, message: '请输入统一社会信用代码!' },
              { len: 18, message: '统一社会信用代码应为18位!' },
              {
                validator: async (_, value) => {
                  if (!value || value.length !== 18) return Promise.resolve();
                  const exists = await checkCreditCodeExists(value, editingCustomer?.id);
                  if (exists) {
                    return Promise.reject(new Error('该统一社会信用代码已存在!'));
                  }
                  return Promise.resolve();
                }
              }
            ]}
          >
            <Input placeholder="18位统一社会信用代码" maxLength={18} />
          </Form.Item>
          
          <Form.Item 
            name="customer_industry" 
            label="行业" 
            rules={[{ required: true, message: '请选择行业!' }]}
          >
            <Select placeholder="请选择行业" showSearch>
              {industryOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item 
            name="customer_region" 
            label="区域" 
            rules={[{ required: true, message: '请选择区域!' }]}
          >
            <Cascader
              options={regionOptions}
              placeholder="请选择省/市"
              showSearch
            />
          </Form.Item>
          
          <Form.Item 
            name="customer_owner_id" 
            label="负责人" 
            rules={[{ required: true, message: '请选择负责人!' }]}
          >
            <Select placeholder="请选择负责人" showSearch optionFilterProp="children">
              {userOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item name="channel_id" label="关联渠道">
            <Select placeholder="请选择渠道(可选)" showSearch optionFilterProp="children" allowClear>
              {channelOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item name="main_contact" label="主要联系人">
            <Input />
          </Form.Item>
          
          <Form.Item name="phone" label="电话">
            <Input />
          </Form.Item>
          
          <Form.Item 
            name="customer_status" 
            label="状态" 
            rules={[{ required: true, message: '请选择状态!' }]}
          >
            <Select placeholder="请选择状态">
              {statusOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>
          
          {isAdmin && (
            <Form.Item name="maintenance_expiry" label="维保到期日">
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
          )}
          
          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default CustomerList;