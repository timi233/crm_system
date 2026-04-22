import React, { useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select, DatePicker, Tag, InputNumber, App, Dropdown, Descriptions, Empty } from 'antd';
import PageDrawer from '../../components/common/PageDrawer';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, MenuOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import { useContracts, useCreateContract, useUpdateContract, useDeleteContract, Contract, ContractCreate } from '../../hooks/useContracts';
import { useProjects } from '../../hooks/useProjects';
import { useCustomers } from '../../hooks/useCustomers';
import { useChannels } from '../../hooks/useChannels';
import PageScaffold from '../../components/common/PageScaffold';

const { Option } = Select;
const { Search } = Input;

const CONTRACT_DIRECTIONS = [
  { value: 'Downstream', label: '下游合同（销售）' },
  { value: 'Upstream', label: '上游合同（采购）' },
];

const CONTRACT_STATUSES = [
  { value: 'draft', label: '草稿', color: 'default' },
  { value: 'pending', label: '审批中', color: 'processing' },
  { value: 'signed', label: '已签署', color: 'success' },
  { value: 'archived', label: '已归档', color: 'cyan' },
  { value: 'rejected', label: '已驳回', color: 'error' },
];

const ContractList: React.FC = () => {
  const { message, modal } = App.useApp();
  const navigate = useNavigate();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [editingContract, setEditingContract] = useState<Contract | null>(null);
  const [searchText, setSearchText] = useState('');
  const [directionFilter, setDirectionFilter] = useState<string | null>(null);
  const [form] = Form.useForm();

  const { data: contracts = [], isLoading } = useContracts();
  const { data: projects = [] } = useProjects();
  const { data: customers = [] } = useCustomers();
  const { data: channels = [] } = useChannels();

  const createMutation = useCreateContract();
  const updateMutation = useUpdateContract();
  const deleteMutation = useDeleteContract();

  const contractDirection = Form.useWatch('contract_direction', form);

  const projectOptions = projects.map(p => ({ value: p.id, label: `${p.project_code} - ${p.project_name}` }));
  const customerOptions = customers.map(c => ({ value: c.id, label: c.customer_name }));
  const channelOptions = channels.map(ch => ({ value: ch.id, label: ch.company_name }));

  const filteredContracts = contracts.filter(contract => {
    const matchesSearch = !searchText ||
      contract.contract_name?.toLowerCase().includes(searchText.toLowerCase()) ||
      contract.contract_code?.toLowerCase().includes(searchText.toLowerCase());
    const matchesDirection = !directionFilter || contract.contract_direction === directionFilter;
    return matchesSearch && matchesDirection;
  });

  const getStatusConfig = (status: string) => {
    return CONTRACT_STATUSES.find(s => s.value === status) || CONTRACT_STATUSES[0];
  };

  const handleCreate = () => {
    navigate('/contracts/new');
  };

  const handleEdit = (contract: Contract) => {
    setEditingContract(contract);
    form.setFieldsValue({
      ...contract,
      signing_date: contract.signing_date ? dayjs(contract.signing_date) : null,
      effective_date: contract.effective_date ? dayjs(contract.effective_date) : null,
      expiry_date: contract.expiry_date ? dayjs(contract.expiry_date) : null,
      products: contract.products || [],
      payment_plans: (contract.payment_plans || []).map(p => ({
        ...p,
        plan_date: p.plan_date ? dayjs(p.plan_date) : null,
        actual_date: p.actual_date ? dayjs(p.actual_date) : null,
      })),
    });
    setIsDrawerOpen(true);
  };

  const handleView = (contract: Contract) => {
    navigate(`/contracts/${contract.id}/full`);
  };

  const handleDelete = async (contractId: number) => {
    modal.confirm({
      title: '确定删除该合同吗？',
      content: '此操作不可恢复',
      onOk: async () => {
        try {
          await deleteMutation.mutateAsync(contractId);
          message.success('合同删除成功');
        } catch (error: any) {
          message.error(error?.response?.data?.detail || '删除失败');
        }
      }
    });
  };

  const handleDrawerOk = async () => {
    try {
      const values = await form.validateFields();
      const payload: ContractCreate = {
        ...values,
        signing_date: values.signing_date?.format?.('YYYY-MM-DD'),
        effective_date: values.effective_date?.format?.('YYYY-MM-DD'),
        expiry_date: values.expiry_date?.format?.('YYYY-MM-DD'),
        products: values.products?.map((p: any) => ({
          ...p,
          amount: p.quantity * p.unit_price * (p.discount || 1),
        })),
        payment_plans: values.payment_plans?.map((p: any) => ({
          ...p,
          plan_date: p.plan_date?.format?.('YYYY-MM-DD'),
        })),
      };

      if (editingContract) {
        await updateMutation.mutateAsync({ id: editingContract.id, contract: payload });
        message.success('合同更新成功');
      } else {
        await createMutation.mutateAsync(payload);
        message.success('合同创建成功');
      }

      setIsDrawerOpen(false);
      form.resetFields();
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  const baseColumns = [
    {
      title: '合同编号',
      dataIndex: 'contract_code',
      key: 'contract_code',
      width: 180,
    },
    {
      title: '合同名称',
      dataIndex: 'contract_name',
      key: 'contract_name',
      width: 200,
    },
    {
      title: '合同类型',
      dataIndex: 'contract_direction',
      key: 'contract_direction',
      width: 100,
      render: (dir: string) => (
        <Tag color={dir === 'Downstream' ? 'blue' : 'orange'}>
          {dir === 'Downstream' ? '下游合同' : '上游合同'}
        </Tag>
      ),
    },
    {
      title: '合同金额',
      dataIndex: 'contract_amount',
      key: 'contract_amount',
      width: 120,
      render: (amount: number) => `¥${amount?.toLocaleString() || 0}`,
    },
    {
      title: '状态',
      dataIndex: 'contract_status',
      key: 'contract_status',
      width: 90,
      render: (status: string) => {
        const config = getStatusConfig(status);
        return <Tag color={config.color}>{config.label}</Tag>;
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: any, record: Contract) => (
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

  const expandedRowRender = (record: Contract) => (
    <Descriptions column={3} size="small">
      <Descriptions.Item label="关联项目">{record.project_name || `ID: ${record.project_id}`}</Descriptions.Item>
      <Descriptions.Item label="签订日期">{record.signing_date || '-'}</Descriptions.Item>
      <Descriptions.Item label="生效日期">{record.effective_date || '-'}</Descriptions.Item>
      <Descriptions.Item label="到期日期">{record.expiry_date || '-'}</Descriptions.Item>
      <Descriptions.Item label="产品数">{record.products?.length || 0}</Descriptions.Item>
      <Descriptions.Item label="回款进度">
        {record.contract_direction === 'Downstream' && record.payment_plans?.length ? 
          `${record.payment_plans.reduce((sum, p) => sum + (p.actual_amount || 0), 0).toLocaleString()}` : '-'}
      </Descriptions.Item>
      <Descriptions.Item label="备注">{record.notes || '-'}</Descriptions.Item>
    </Descriptions>
  );

  return (
    <PageScaffold
      title="合同归档管理"
      breadcrumbItems={[{ title: '首页' }, { title: '合同归档管理' }]}
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建合同
        </Button>
      }
    >
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Search
            placeholder="搜索合同名称或编号"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 250 }}
          />
          <Select
            placeholder="筛选合同类型"
            value={directionFilter}
            onChange={setDirectionFilter}
            style={{ width: 180 }}
            allowClear
          >
            {CONTRACT_DIRECTIONS.map(opt => (
              <Option key={opt.value} value={opt.value}>{opt.label}</Option>
            ))}
          </Select>
        </Space>
      </div>

      <Table
        columns={baseColumns}
        dataSource={filteredContracts}
        loading={isLoading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        scroll={{ x: 800 }}
        expandable={{
          expandedRowRender,
          rowExpandable: () => true,
        }}
        locale={{ emptyText: <Empty description="暂无合同数据" image={Empty.PRESENTED_IMAGE_SIMPLE}>
          <Button type="primary" onClick={handleCreate}>+ 新建第一条合同</Button>
        </Empty> }}
      />

      <PageDrawer
        title={editingContract ? '编辑合同' : '新建合同'}
        open={isDrawerOpen}
        onClose={() => {
          setIsDrawerOpen(false);
          form.resetFields();
          setEditingContract(null);
        }}
        width={680}
      >
        <Form form={form} layout="vertical">
          <Form.Item 
            name="contract_name" 
            label="合同名称" 
            rules={[{ required: true, message: '请输入合同名称!' }]}
          >
            <Input placeholder="请输入合同名称" />
          </Form.Item>

          <Form.Item 
            name="project_id" 
            label="关联项目" 
            rules={[{ required: true, message: '请选择关联项目!' }]}
          >
            <Select placeholder="请选择项目" showSearch optionFilterProp="children">
              {projectOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>

          <Space style={{ width: '100%' }} size="large">
            <Form.Item 
              name="contract_direction" 
              label="合同类型" 
              rules={[{ required: true }]}
              style={{ width: 200 }}
            >
              <Select>
                {CONTRACT_DIRECTIONS.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item 
              name="contract_status" 
              label="合同状态" 
              style={{ width: 150 }}
            >
              <Select>
                {CONTRACT_STATUSES.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item 
              name="contract_amount" 
              label="合同金额" 
              rules={[{ required: true }]}
              style={{ width: 150 }}
            >
              <InputNumber placeholder="金额" style={{ width: '100%' }} min={0} />
            </Form.Item>
          </Space>

          {contractDirection === 'Downstream' && (
            <Form.Item 
              name="terminal_customer_id" 
              label="终端客户" 
              rules={[{ required: true, message: '下游合同必须关联客户!' }]}
            >
              <Select placeholder="请选择终端客户" showSearch optionFilterProp="children">
                {customerOptions.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>
          )}

          {contractDirection === 'Upstream' && (
            <Form.Item 
              name="channel_id" 
              label="渠道/供应商" 
              rules={[{ required: true, message: '上游合同必须关联供应商!' }]}
            >
              <Select placeholder="请选择渠道/供应商" showSearch optionFilterProp="children">
                {channelOptions.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>
          )}

          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="signing_date" label="签订日期" style={{ width: 150 }}>
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="effective_date" label="生效日期" style={{ width: 150 }}>
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="expiry_date" label="到期日期" style={{ width: 150 }}>
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
          </Space>

          <Button type="primary" onClick={handleDrawerOk} loading={createMutation.isPending || updateMutation.isPending} block>
            保存
          </Button>
        </Form>
      </PageDrawer>
    </PageScaffold>
  );
};

export default ContractList;
