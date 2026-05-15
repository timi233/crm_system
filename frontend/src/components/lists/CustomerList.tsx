import React, { useState } from 'react';
import { App, Table, Button, Space, Tag, Input, Select, Modal, Form, DatePicker, Cascader, Dropdown, Descriptions, Empty, Row, Col } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, MenuOutlined } from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from '../../store/store';
import { useCustomers, useCreateCustomer, useUpdateCustomer, useDeleteCustomer } from '../../hooks/useCustomers';
import api from '../../services/api';
import { useRegionCascader, useDictItems } from '../../hooks/useDictItems';
import { useUsers } from '../../hooks/useUsers';
import { useChannels } from '../../hooks/useChannels';
import PageScaffold from '../../components/common/PageScaffold';
import PageModal from '../../components/common/PageModal';

const { Option } = Select;

const CustomerList: React.FC = () => {
  const { message, modal } = App.useApp();
  const navigate = useNavigate();
  const location = useLocation();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<any>(null);
  const [searchText, setSearchText] = useState('');
  const [industryFilter, setIndustryFilter] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [form] = Form.useForm();

  const isCreateRoute = location.pathname === '/customers/new';
  React.useEffect(() => {
    if (isCreateRoute) {
      handleCreate();
    }
  }, [isCreateRoute]);

  const { data: customers = [], isLoading } = useCustomers();
  const { data: industryItems = [] } = useDictItems('客户行业');
  const { data: statusItems = [] } = useDictItems('客户状态');
  const { data: regionOptions = [] } = useRegionCascader();
  const { data: users = [] } = useUsers();
  const { data: channels = [] } = useChannels();

  const industryOptions = industryItems.map(item => ({ value: item.name, label: item.name }));
  const statusOptions = statusItems.map(item => ({ value: item.name, label: item.name }));
  const userOptions = users.map(u => ({ value: u.id, label: u.name }));
  const channelOptions = channels.map(ch => ({ value: ch.id, label: ch.company_name }));

  const { capabilities } = useSelector((state: RootState) => state.auth);
  const canCreateCustomer = Boolean(capabilities['customer:create']);
  const canManageCustomers = Boolean(capabilities['customer:manage']);
  const canEditAdvancedCustomerFields = Boolean(capabilities['customer:edit_advanced']);

  const createMutation = useCreateCustomer();
  const updateMutation = useUpdateCustomer();
  const deleteMutation = useDeleteCustomer();

  const checkCreditCodeExists = async (code: string, excludeId?: number) => {
    try {
      const response = await api.get<{ exists: boolean }>(`/customers/check-credit-code?code=${code}${excludeId ? `&exclude_id=${excludeId}` : ''}`);
      return response.data.exists;
    } catch {
      return false;
    }
  };

  const filteredCustomers = customers.filter(c => {
    const matchesSearch = !searchText ||
      c.customer_name.toLowerCase().includes(searchText.toLowerCase()) ||
      (c.credit_code && c.credit_code.toLowerCase().includes(searchText.toLowerCase()));

    const matchesIndustry = !industryFilter || c.customer_industry === industryFilter;
    const matchesStatus = !statusFilter || c.customer_status === statusFilter;

    return matchesSearch && matchesIndustry && matchesStatus;
  });

  const handleCreate = () => {
    setEditingCustomer(null);
    form.resetFields();
    form.setFieldsValue({ customer_status: '意向客户' });
    setIsDrawerOpen(true);
  };

  const handleEdit = (customer: any) => {
    setEditingCustomer(customer);
    form.setFieldsValue(customer);
    setIsDrawerOpen(true);
  };

  const handleView = (customer: any) => {
    navigate(`/customers/${customer.id}/full`);
  };

  const handleDelete = (customerId: number) => {
    modal.confirm({
      title: '确定删除该客户吗？',
      content: '此操作不可恢复，关联的线索和商机可能会受到影响。',
      okType: 'danger',
      onOk: async () => {
        try {
          await deleteMutation.mutateAsync(customerId);
          message.success('客户已删除');
        } catch (error) {
        }
      }
    });
  };

  const handleDrawerOk = async () => {
    try {
      const values = await form.validateFields();
      if (editingCustomer) {
        await updateMutation.mutateAsync({ id: editingCustomer.id, customer: values });
        message.success('客户信息已更新');
      } else {
        await createMutation.mutateAsync(values);
        message.success('客户已创建');
      }
      setIsDrawerOpen(false);
      form.resetFields();
      if (isCreateRoute) {
        navigate('/customers');
      }
    } catch (error) {
    }
  };

  const baseColumns = [
    {
      title: '客户名称',
      dataIndex: 'customer_name',
      key: 'customer_name',
      width: 220,
      fixed: 'left' as const,
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
      width: 150,
      render: (region: string[]) => Array.isArray(region) ? region.join(' / ') : region,
    },
    {
      title: '状态',
      dataIndex: 'customer_status',
      key: 'customer_status',
      width: 100,
      render: (status: string) => (
        <Tag color={status === '成交客户' ? 'success' : status === '意向客户' ? 'processing' : 'default'} style={{ border: 'none' }}>
          {status}
        </Tag>
      ),
    },
    {
      title: '负责人',
      dataIndex: 'customer_owner_name',
      key: 'customer_owner_name',
      width: 100,
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      fixed: 'right' as const,
      render: (_: any, record: any) => (
        <Dropdown
          menu={{
            items: [
              { key: 'view', label: '查看详情', icon: <EyeOutlined /> },
              { key: 'edit', label: '编辑客户', icon: <EditOutlined /> },
              { key: 'delete', label: '删除客户', icon: <DeleteOutlined />, danger: true },
            ],
            onClick: ({ key }) => {
              if (key === 'view') handleView(record);
              else if (key === 'edit') handleEdit(record);
              else if (key === 'delete') handleDelete(record.id);
            },
          }}
          trigger={['click']}
        >
          <Button size="small" icon={<MenuOutlined />}>操作</Button>
        </Dropdown>
      ),
    },
  ];

  const expandedRowRender = (record: any) => (
    <Descriptions column={3} size="small" style={{ padding: '8px 24px' }}>
      <Descriptions.Item label="信用代码">{record.credit_code || '-'}</Descriptions.Item>
      <Descriptions.Item label="联系人">{record.main_contact || '-'}</Descriptions.Item>
      <Descriptions.Item label="电话">{record.phone || '-'}</Descriptions.Item>
      <Descriptions.Item label="关联渠道">{record.channel_name || '-'}</Descriptions.Item>
      <Descriptions.Item label="备注" span={2}>{record.notes || '-'}</Descriptions.Item>
    </Descriptions>
  );

  return (
    <PageScaffold
      title="终端客户"
      breadcrumbItems={[{ title: '首页' }, { title: '终端客户' }]}
      extra={
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleCreate}
          disabled={!canCreateCustomer}
          size="large"
          className="btn--gradient"
          style={{ height: '40px', padding: '0 20px' }}
        >
          新建客户
        </Button>
      }
      filters={
        <Space size={16} wrap>
          <Input.Search
            placeholder="搜索客户名称或信用代码"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 280 }}
            allowClear
            size="middle"
          />
          <Select
            placeholder="筛选行业"
            value={industryFilter}
            onChange={setIndustryFilter}
            style={{ width: 180 }}
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
            style={{ width: 180 }}
            allowClear
          >
            {statusOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>
                {opt.label}
              </Option>
            ))}
          </Select>
        </Space>
      }
    >
      <Table
        columns={baseColumns}
        dataSource={filteredCustomers}
        rowKey="id"
        loading={isLoading}
        pagination={{
          pageSize: 20,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条数据`,
        }}
        scroll={{ x: 700 }}
        expandable={{
          expandedRowRender,
          rowExpandable: () => true,
        }}
        className="customer-table"
        bordered={false}
        locale={{
          emptyText: (
            <Empty description="暂无客户数据" image={Empty.PRESENTED_IMAGE_SIMPLE}>
              <Button type="primary" onClick={handleCreate} disabled={!canCreateCustomer}>+ 新增第一条客户</Button>
            </Empty>
          )
        }}
      />

      <PageModal
        title={editingCustomer ? '编辑客户资料' : '建立新客户档案'}
        open={isDrawerOpen}
        onClose={() => {
          setIsDrawerOpen(false);
          form.resetFields();
          setEditingCustomer(null);
          if (isCreateRoute) {
            navigate('/customers');
          }
        }}
        width={680}
        footer={[
          <Button key="cancel" onClick={() => setIsDrawerOpen(false)}>
            取消
          </Button>,
          <Button
            key="submit"
            type="primary"
            className="btn--gradient"
            onClick={handleDrawerOk}
            loading={updateMutation.isPending || createMutation.isPending}
          >
            保存并同步
          </Button>
        ]}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="customer_name"
            label="客户全称"
            rules={[{ required: true, message: '请输入客户全称!' }]}
          >
            <Input placeholder="请录入公司或单位完整名称" />
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

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="customer_industry"
                label="所属行业"
                rules={[{ required: true, message: '请选择行业!' }]}
              >
                <Select placeholder="选择所属行业" showSearch>
                  {industryOptions.map(opt => (
                    <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="customer_status"
                label="跟进状态"
                rules={[{ required: true, message: '请选择状态!' }]}
              >
                <Select placeholder="请选择当前状态">
                  {statusOptions.map(opt => (
                    <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="customer_region"
            label="所在区域"
            rules={[{ required: true, message: '请选择区域!' }]}
          >
            <Cascader
              options={regionOptions}
              placeholder="请选择省/市"
              showSearch
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="customer_owner_id"
                label="客户负责人"
                rules={[{ required: true, message: '请选择负责人!' }]}
              >
                <Select placeholder="请选择内部负责人" showSearch optionFilterProp="children">
                  {userOptions.map(opt => (
                    <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="channel_id" label="协同渠道">
                <Select placeholder="请选择协同渠道(可选)" showSearch optionFilterProp="children" allowClear>
                  {channelOptions.map(opt => (
                    <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="main_contact" label="主要联系人">
                <Input placeholder="姓名" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="phone" label="联系电话">
                <Input placeholder="手机或座机" />
              </Form.Item>
            </Col>
          </Row>

          {canEditAdvancedCustomerFields && (
            <Form.Item name="maintenance_expiry" label="维保到期日期">
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
          )}

          <Form.Item name="notes" label="其他备注">
            <Input.TextArea rows={3} placeholder="如有其他补充信息请录入..." />
          </Form.Item>
        </Form>
      </PageModal>
    </PageScaffold>
  );
};

export default CustomerList;
