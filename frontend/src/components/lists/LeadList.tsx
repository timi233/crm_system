import React, { useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select, Card, Tag, Checkbox, message, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SwapOutlined, EyeOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useLeads, useCreateLead, useUpdateLead, useDeleteLead, useConvertLeadToOpportunity, Lead, LeadConvertRequest } from '../../hooks/useLeads';
import { useDictItems } from '../../hooks/useDictItems';
import { useCustomers } from '../../hooks/useCustomers';
import { useUsers } from '../../hooks/useUsers';

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
  const [form] = Form.useForm();
  const [convertForm] = Form.useForm();

  const { data: leads = [], isLoading } = useLeads();
  const { data: sourceItems = [] } = useDictItems('商机来源');
  const { data: customers = [] } = useCustomers();
  const { data: users = [] } = useUsers();
  
  const sourceOptions = sourceItems.map(item => ({ value: item.name, label: item.name }));
  const customerOptions = customers.map(c => ({ value: c.id, label: c.customer_name }));
  const userOptions = users.map(u => ({ value: u.id, label: u.name }));

  const createMutation = useCreateLead();
  const updateMutation = useUpdateLead();
  const deleteMutation = useDeleteLead();
  const convertMutation = useConvertLeadToOpportunity();

  const filteredLeads = leads.filter(lead => {
    const matchesSearch = !searchText ||
      lead.lead_name?.toLowerCase().includes(searchText.toLowerCase());
    const matchesStage = !stageFilter || lead.lead_stage === stageFilter;
    return matchesSearch && matchesStage;
  });

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

  const handleDelete = async (leadId: number) => {
    try {
      await deleteMutation.mutateAsync(leadId);
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
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
      width: 180,
    },
    {
      title: '线索名称',
      dataIndex: 'lead_name',
      key: 'lead_name',
    },
    {
      title: '终端客户',
      dataIndex: 'terminal_customer_name',
      key: 'terminal_customer_name',
    },
    {
      title: '阶段',
      dataIndex: 'lead_stage',
      key: 'lead_stage',
      render: (stage: string) => <Tag color={getStageColor(stage)}>{stage}</Tag>,
    },
    {
      title: '需求确认',
      dataIndex: 'has_confirmed_requirement',
      key: 'has_confirmed_requirement',
      render: (v: boolean) => v ? <Tag color="green">已确认</Tag> : <Tag>未确认</Tag>,
    },
    {
      title: '预算确认',
      dataIndex: 'has_confirmed_budget',
      key: 'has_confirmed_budget',
      render: (v: boolean) => v ? <Tag color="green">已确认</Tag> : <Tag>未确认</Tag>,
    },
    {
      title: '销售负责人',
      dataIndex: 'sales_owner_name',
      key: 'sales_owner_name',
    },
    {
      title: '状态',
      dataIndex: 'converted_to_opportunity',
      key: 'converted_to_opportunity',
      render: (v: boolean, record: Lead) => 
        v ? <Tag color="blue">已转商机 #{record.opportunity_id}</Tag> : <Tag color="orange">跟进中</Tag>,
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Lead) => (
        <Space size="small">
          <Button size="small" icon={<EyeOutlined />} onClick={() => handleView(record)}>
            查看
          </Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          {!record.converted_to_opportunity && (
            <Button size="small" type="primary" icon={<SwapOutlined />} onClick={() => handleConvertClick(record)}>
              转商机
            </Button>
          )}
          {!record.converted_to_opportunity && (
            <Popconfirm
              title="确定删除该线索吗？"
              onConfirm={() => handleDelete(record.id)}
            >
              <Button size="small" danger icon={<DeleteOutlined />}>
                删除
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <Card
      title="线索管理列表"
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
            placeholder="筛选阶段"
            value={stageFilter}
            onChange={setStageFilter}
            style={{ width: 150 }}
            allowClear
          >
            {LEAD_STAGES.map(stage => (
              <Option key={stage} value={stage}>{stage}</Option>
            ))}
          </Select>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={filteredLeads}
        loading={isLoading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        scroll={{ x: 1200 }}
      />

      <Modal
        title={editingLead ? '编辑线索' : '新建线索'}
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
        </Form>
      </Modal>

      <Modal
        title="线索转商机"
        open={isConvertModalVisible}
        onOk={handleConvertOk}
        onCancel={() => setIsConvertModalVisible(false)}
        okText="确认转换"
        cancelText="取消"
        width={500}
        confirmLoading={convertMutation.isPending}
      >
        <Form form={convertForm} layout="vertical">
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
        </Form>
      </Modal>
    </Card>
  );
};

export default LeadList;