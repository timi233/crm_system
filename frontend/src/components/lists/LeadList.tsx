import React, { useState, useMemo } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select, Card, Tag, Checkbox, message, Dropdown, Empty, Typography, Descriptions, Drawer } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SwapOutlined, EyeOutlined, MenuOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useLeads, useCreateLead, useUpdateLead, useDeleteLead, useConvertLeadToOpportunity, Lead, LeadConvertRequest } from '../../hooks/useLeads';
import { useDictItems } from '../../hooks/useDictItems';
import { useCustomers } from '../../hooks/useCustomers';
import { useUsers } from '../../hooks/useUsers';
import { useChannels } from '../../hooks/useChannels';
import PageScaffold from '../../components/common/PageScaffold';

const { Title } = Typography;
const { Option } = Select;
const { Search } = Input;

const LEAD_STAGES = ['初步接触', '意向沟通', '需求挖掘中'];
const LEAD_GRADES = ['A', 'B', 'C', 'D'];

const LeadList: React.FC = () => {
  const navigate = useNavigate();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isConvertModalVisible, setIsConvertModalVisible] = useState(false);
  const [editingLead, setEditingLead] = useState<Lead | null>(null);
  const [convertingLead, setConvertingLead] = useState<Lead | null>(null);
  const [searchText, setSearchText] = useState('');
  const [stageFilter, setStageFilter] = useState<string | null>(null);
  const [showOwnerFilter, setShowOwnerFilter] = useState(false);
  const [ownerFilter, setOwnerFilter] = useState<number | null>(null);
  const [form] = Form.useForm();
  const [convertForm] = Form.useForm();

  const { data: leads = [], isLoading } = useLeads();
  const { data: sourceItems = [] } = useDictItems('商机来源');
  const { data: productItems = [] } = useDictItems('产品品牌');
  const { data: customers = [] } = useCustomers();
  const { data: users = [] } = useUsers();
  const { data: channels = [] } = useChannels();
  
  const sourceOptions = sourceItems.map(item => ({ value: item.name, label: item.name }));
  const customerOptions = customers.map(c => ({ value: c.id, label: c.customer_name }));
  const userOptions = users.map(u => ({ value: u.id, label: u.name }));
  const channelOptions = channels.map(c => ({ value: c.id, label: c.company_name }));

  const createMutation = useCreateLead();
  const updateMutation = useUpdateLead();
  const deleteMutation = useDeleteLead();
  const convertMutation = useConvertLeadToOpportunity();

  const filteredLeads = useMemo(() => leads.filter(lead => {
    const matchesSearch = !searchText ||
      lead.lead_name?.toLowerCase().includes(searchText.toLowerCase());
    const matchesStage = !stageFilter || lead.lead_stage === stageFilter;
    const matchesOwner = !showOwnerFilter || !ownerFilter || lead.sales_owner_id === ownerFilter;
    return matchesSearch && matchesStage && matchesOwner;
  }), [leads, searchText, stageFilter, showOwnerFilter, ownerFilter]);

  const getStageColor = (stage: string) => {
    switch (stage) {
      case '初步接触': return 'blue';
      case '意向沟通': return 'gold';
      case '需求挖掘中': return 'green';
      default: return 'default';
    }
  };

  const handleCustomerChange = (customerId: number) => {
    const customer = customers.find(c => c.id === customerId);
    if (customer) {
      form.setFieldsValue({
        contact_person: customer.main_contact || '',
        contact_phone: customer.phone || '',
      });
    }
  };

  const handleCreate = () => {
    setEditingLead(null);
    form.resetFields();
    form.setFieldsValue({ lead_stage: '初步接触', has_confirmed_requirement: false, has_confirmed_budget: false });
    setIsModalVisible(true);
  };

  const handleEdit = (lead: Lead) => {
    if (lead.converted_to_opportunity) {
      message.warning('已转商机的线索不能修改');
      return;
    }
    setEditingLead(lead);
    form.setFieldsValue(lead);
    setIsModalVisible(true);
  };

  const handleView = (lead: Lead) => {
    navigate(`/leads/${lead.id}/full`);
  };

  const handleDelete = (leadId: number) => {
    Modal.confirm({
      title: '确定删除该线索吗？',
      content: '此操作不可恢复',
      onOk: async () => {
        try {
          await deleteMutation.mutateAsync(leadId);
          message.success('线索删除成功');
        } catch (error: any) {
        }
      }
    });
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingLead) {
        await updateMutation.mutateAsync({ id: editingLead.id, lead: values });
      } else {
        await createMutation.mutateAsync(values);
      }
      
      setIsModalVisible(false);
      form.resetFields();
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  const handleConvertClick = (lead: Lead) => {
    if (lead.converted_to_opportunity) {
      message.info('该线索已转换为商机');
      return;
    }
    if (!lead.has_confirmed_requirement || !lead.has_confirmed_budget) {
      message.warning('需确认需求和预算后才能转商机');
      return;
    }
    setConvertingLead(lead);
    convertForm.resetFields();
    convertForm.setFieldsValue({ opportunity_name: lead.lead_name, lead_grade: 'B' });
    setIsConvertModalVisible(true);
  };

  const handleConvertOk = async () => {
    if (!convertingLead) return;
    
    try {
      const values = await convertForm.validateFields();
      await convertMutation.mutateAsync({ id: convertingLead.id, request: values });
      message.success('线索已成功转换为商机');
      setIsConvertModalVisible(false);
      convertForm.resetFields();
      setConvertingLead(null);
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  const columns = [
    {
      title: '线索编号',
      dataIndex: 'lead_code',
      key: 'lead_code',
      fixed: 'left' as const,
      width: 160,
    },
    {
      title: '线索名称',
      dataIndex: 'lead_name',
      key: 'lead_name',
      fixed: 'left' as const,
      width: 220,
    },
    {
      title: '客户',
      dataIndex: 'terminal_customer_name',
      key: 'terminal_customer_name',
      width: 180,
    },
    {
      title: '阶段',
      dataIndex: 'lead_stage',
      key: 'lead_stage',
      width: 100,
      render: (stage: string) => <Tag color={getStageColor(stage)}>{stage}</Tag>,
    },
    {
      title: '负责人',
      dataIndex: 'sales_owner_name',
      key: 'sales_owner_name',
      width: 100,
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right' as const,
      width: 80,
      render: (_: any, record: Lead) => (
        <Dropdown
          menu={{
            items: [
              { key: 'view', label: '查看', icon: <EyeOutlined /> },
              { key: 'edit', label: '编辑', icon: <EditOutlined /> },
              !record.converted_to_opportunity && { key: 'convert', label: '转商机', icon: <SwapOutlined /> },
              !record.converted_to_opportunity && { key: 'delete', label: '删除', icon: <DeleteOutlined />, danger: true },
            ].filter(Boolean),
            onClick: ({ key }) => {
              if (key === 'view') handleView(record);
              else if (key === 'edit') handleEdit(record);
              else if (key === 'convert') handleConvertClick(record);
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

  const expandedRowRender = (record: Lead) => (
    <Descriptions column={3} size="small">
      <Descriptions.Item label="产品">
        {record.products && record.products.length > 0 
          ? record.products.map(p => <Tag key={p} color="blue">{p}</Tag>) 
          : '-'}
      </Descriptions.Item>
      <Descriptions.Item label="联系人">{record.contact_person || '-'}</Descriptions.Item>
      <Descriptions.Item label="联系电话">{record.contact_phone || '-'}</Descriptions.Item>
      <Descriptions.Item label="预估预算">{record.estimated_budget ? `¥${record.estimated_budget.toLocaleString()}` : '-'}</Descriptions.Item>
      <Descriptions.Item label="线索来源">{record.lead_source || '-'}</Descriptions.Item>
      <Descriptions.Item label="来源渠道">{record.source_channel_name || '-'}</Descriptions.Item>
      <Descriptions.Item label="协同渠道">{record.channel_name || '-'}</Descriptions.Item>
      <Descriptions.Item label="备注">{record.notes || '-'}</Descriptions.Item>
    </Descriptions>
  );

  return (
    <PageScaffold
      title="线索管理"
      breadcrumbItems={[{ title: '首页' }, { title: '线索管理' }]}
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建线索
        </Button>
      }
    >
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Search
            placeholder="搜索线索名称"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 200 }}
          />
          <Select
            placeholder="阶段"
            value={stageFilter}
            onChange={setStageFilter}
            style={{ width: 120 }}
            allowClear
          >
            {LEAD_STAGES.map(stage => (
              <Option key={stage} value={stage}>{stage}</Option>
            ))}
          </Select>
          <Select
            placeholder="负责人"
            value={ownerFilter || undefined}
            onChange={(val) => setOwnerFilter(val || null)}
            style={{ width: 150 }}
            allowClear
          >
            {userOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>{opt.label}</Option>
            ))}
          </Select>
          <Checkbox
            checked={showOwnerFilter}
            onChange={(e) => setShowOwnerFilter(e.target.checked)}
          >
            只看我负责
          </Checkbox>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={filteredLeads}
        loading={isLoading}
        rowKey="id"
        pagination={{ pageSize: 10, showSizeChanger: true }}
        scroll={{ x: 800 }}
        expandable={{
          expandedRowRender,
          rowExpandable: () => true,
        }}
        locale={{ 
          emptyText: (
            <Empty description="暂无线索数据" image={Empty.PRESENTED_IMAGE_SIMPLE}>
              <Button type="primary" onClick={() => navigate('/leads/new')}>+ 新增第一条线索</Button>
            </Empty>
          )
        }}
      />

      <Drawer
        title={editingLead ? '编辑线索' : '新建线索'}
        open={isModalVisible}
        onClose={() => setIsModalVisible(false)}
        width={520}
        maskClosable={false}
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ flex: 1, overflow: 'auto' }}>
          <Form.Item 
            name="lead_name" 
            label="线索名称" 
            rules={[{ required: true, message: '请输入线索名称!' }]}
          >
            <Input />
          </Form.Item>
          
          <Form.Item 
            name="terminal_customer_id" 
            label="终端客户" 
            rules={[{ required: true, message: '请选择终端客户!' }]}
          >
            <Select placeholder="请选择终端客户" showSearch optionFilterProp="children" onChange={handleCustomerChange}>
              {customerOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item 
            name="sales_owner_id" 
            label="销售负责人" 
            rules={[{ required: true, message: '请选择销售负责人!' }]}
          >
            <Select placeholder="请选择销售负责人" showSearch optionFilterProp="children">
              {userOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item 
            name="lead_stage" 
            label="线索阶段" 
            rules={[{ required: true, message: '请选择线索阶段!' }]}
          >
            <Select placeholder="请选择线索阶段">
              {LEAD_STAGES.map(stage => (
                <Option key={stage} value={stage}>{stage}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item name="lead_source" label="线索来源">
            <Select placeholder="请选择线索来源" allowClear>
              {sourceOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item 
            name="source_channel_id" 
            label="来源渠道" 
            tooltip="归因渠道，创建后原则上不可修改"
            rules={[{ required: false }]}
          >
            <Select placeholder="请选择来源渠道" allowClear showSearch optionFilterProp="label" disabled={!!editingLead}>
              {channelOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item 
            name="channel_id" 
            label="协同渠道" 
            tooltip="当前协同渠道，可随时修改"
          >
            <Select placeholder="请选择协同渠道" allowClear showSearch optionFilterProp="label">
              {channelOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="products" label="产品">
            <Select mode="multiple" placeholder="请选择产品（可多选）" allowClear>
              {productItems.map(item => (
                <Option key={item.name} value={item.name}>{item.name}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="contact_person" label="联系人">
            <Input />
          </Form.Item>
          
          <Form.Item name="contact_phone" label="联系电话">
            <Input />
          </Form.Item>
          
          <Form.Item name="estimated_budget" label="预估预算">
            <Input type="number" />
          </Form.Item>
          
          <Space>
            <Form.Item name="has_confirmed_requirement" valuePropName="checked">
              <Checkbox>已确认需求</Checkbox>
            </Form.Item>
            <Form.Item name="has_confirmed_budget" valuePropName="checked">
              <Checkbox>已确认预算</Checkbox>
            </Form.Item>
          </Space>
          
          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={3} />
          </Form.Item>
          
          <Form.Item>
            <Button type="primary" onClick={handleModalOk} loading={createMutation.isPending || updateMutation.isPending} block>
              保存
            </Button>
          </Form.Item>
        </Form>
      </Drawer>

      <Drawer
        title="线索转商机"
        open={isConvertModalVisible}
        onClose={() => setIsConvertModalVisible(false)}
        width={480}
        maskClosable={false}
        destroyOnClose
      >
        <Form form={convertForm} layout="vertical" style={{ flex: 1, overflow: 'auto' }}>
          <Form.Item 
            name="opportunity_name" 
            label="商机名称" 
            rules={[{ required: true, message: '请输入商机名称!' }]}
          >
            <Input />
          </Form.Item>
          
          <Form.Item 
            name="expected_contract_amount" 
            label="预计合同金额" 
            rules={[{ required: true, message: '请输入预计合同金额!' }]}
          >
            <Input type="number" />
          </Form.Item>
          
          <Form.Item 
            name="lead_grade" 
            label="线索等级" 
            rules={[{ required: true, message: '请选择线索等级!' }]}
          >
            <Select>
              {LEAD_GRADES.map(grade => (
                <Option key={grade} value={grade}>{grade}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item name="opportunity_source" label="商机来源">
            <Select placeholder="请选择商机来源" allowClear>
              {sourceOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item>
            <Button type="primary" onClick={handleConvertOk} loading={convertMutation.isPending} block>
              确认转换
            </Button>
          </Form.Item>
        </Form>
      </Drawer>
    </PageScaffold>
  );
};

export default LeadList;
