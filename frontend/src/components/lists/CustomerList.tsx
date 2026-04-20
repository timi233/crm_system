import React, { useState } from 'react';
import { Table, Button, Space, Tag, Input, Select, Modal, Form, DatePicker, Cascader, message, Dropdown, Descriptions, Empty } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, MenuOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { RootState } from '../../store/store';
import api from '../../services/api';
import { useRegionCascader, useDictItems } from '../../hooks/useDictItems';
import { useUsers } from '../../hooks/useUsers';
import { useChannels } from '../../hooks/useChannels';
import PageScaffold from '../../components/common/PageScaffold';
import PageDrawer from '../../components/common/PageDrawer';

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
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null);
  const [form] = Form.useForm();

  const { user } = useSelector((state: RootState) => state.auth);
  const isAdmin = user?.role === 'admin';

  const queryClient = useQueryClient();
  const { data: regionOptions = [] } = useRegionCascader();
  const { data: industryItems = [] } = useDictItems('行业');
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
    navigate('/customers/new');
  };

  const handleEdit = (customer: Customer) => {
    setEditingCustomer(customer);
    const regionArray = customer.customer_region ? customer.customer_region.split('/') : [];
    form.setFieldsValue({
      ...customer,
      customer_region: regionArray.length > 0 ? regionArray : undefined,
    });
    setIsDrawerOpen(true);
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

  const handleDrawerOk = async () => {
    try {
      const values = await form.validateFields();
      const submitData = {
        ...values,
        customer_region: values.customer_region ? values.customer_region.join('/') : '',
        maintenance_expiry: values.maintenance_expiry?.format('YYYY-MM-DD'),
      };
      
      if (editingCustomer) {
        await updateMutation.mutateAsync({ id: editingCustomer.id, customer: submitData });
      }
      
      setIsDrawerOpen(false);
      form.resetFields();
      setEditingCustomer(null);
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
      width: 140,
    },
    {
      title: '客户名称',
      dataIndex: 'customer_name',
      key: 'customer_name',
      width: 200,
    },
    {
      title: '行业',
      dataIndex: 'customer_industry',
      key: 'customer_industry',
      width: 120,
    },
    {
      title: '负责人',
      dataIndex: 'customer_owner_name',
      key: 'customer_owner_name',
      width: 100,
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
      width: 80,
      render: (_: any, record: Customer) => (
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

  const expandedRowRender = (record: Customer) => (
    <Descriptions column={3} size="small">
      <Descriptions.Item label="统一社会信用代码">{record.credit_code || '-'}</Descriptions.Item>
      <Descriptions.Item label="区域">{record.customer_region || '-'}</Descriptions.Item>
      <Descriptions.Item label="关联渠道">{record.channel_name || '-'}</Descriptions.Item>
      <Descriptions.Item label="主要联系人">{record.main_contact || '-'}</Descriptions.Item>
      <Descriptions.Item label="电话">{record.phone || '-'}</Descriptions.Item>
      <Descriptions.Item label="维保到期">{record.maintenance_expiry || '-'}</Descriptions.Item>
      <Descriptions.Item label="备注">{record.notes || '-'}</Descriptions.Item>
    </Descriptions>
  );

  return (
    <PageScaffold
      title="终端客户"
      breadcrumbItems={[{ title: '首页' }, { title: '终端客户' }]}
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建客户
        </Button>
      }
    >
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Input.Search
            placeholder="搜索客户名称或信用代码"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 200 }}
            allowClear
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
        columns={baseColumns}
        dataSource={filteredCustomers}
        rowKey="id"
        loading={isLoading}
        pagination={{ pageSize: 20 }}
        scroll={{ x: 700 }}
        expandable={{
          expandedRowRender,
          rowExpandable: () => true,
        }}
        locale={{
          emptyText: (
            <Empty description="暂无客户数据" image={Empty.PRESENTED_IMAGE_SIMPLE}>
              <Button type="primary" onClick={handleCreate}>+ 新增第一条客户</Button>
            </Empty>
          )
        }}
      />

      <PageDrawer
        title="编辑客户"
        open={isDrawerOpen}
        onClose={() => {
          setIsDrawerOpen(false);
          setEditingCustomer(null);
          form.resetFields();
        }}
        width={520}
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
          
          <Button type="primary" onClick={handleDrawerOk} loading={updateMutation.isPending} block>
            保存
          </Button>
        </Form>
      </PageDrawer>
    </PageScaffold>
  );
};

export default CustomerList;