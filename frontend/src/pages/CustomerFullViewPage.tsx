import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { App, Card, Descriptions, Tag, Table, Tabs, Skeleton, Button, Space, Statistic, Row, Col, Typography, Popconfirm, Dropdown, Modal, Form, Input, Select, DatePicker, InputNumber, Alert, Result, Drawer, Cascader } from 'antd';
import type { MenuProps } from 'antd';
import type { RootState } from '../store/store';
import { ArrowLeftOutlined, UserOutlined, ShopOutlined, PhoneOutlined, FileTextOutlined, PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, MoreOutlined, ClockCircleOutlined } from '@ant-design/icons';
import PageScaffold from '../components/common/PageScaffold';
import dayjs from 'dayjs';
import { useCustomerFullView, RelatedFollowUp, CustomerFullView, CustomerFinanceView } from '../hooks/useCustomerFullView';
import { useCustomerChannelLinks, CustomerChannelLink } from '../hooks/useCustomerChannelLinks';
import { useProductInstallations, useCreateProductInstallation, useUpdateProductInstallation, useDeleteProductInstallation } from '../hooks/useProductInstallations';
import type { ProductInstallation, ProductInstallationCreate, ProductInstallationUpdate } from '../types/productInstallation';
import type { FollowUpCreate } from '../hooks/useFollowUps';
import { useCreateFollowUp, useUpdateFollowUp, useDeleteFollowUp } from '../hooks/useFollowUps';
import { useCreateLead } from '../hooks/useLeads';
import { useCreateOpportunity } from '../hooks/useOpportunities';
import { useCreateProject } from '../hooks/useProjects';
import { useProductTypeCascader } from '../hooks/useDictItems';
import { useChannels } from '../hooks/useChannels';

const { Title } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const MANUFACTURERS = ['爱数', '安恒', 'IPG', '绿盟', '深信服', '其他'];
const PRODUCTS = ['爱数', '安恒', 'IPG', '绿盟', '深信服', '其他'];
const FOLLOW_UP_METHODS = ['电话', '邮件', '拜访', '微信', '其他'];
const FOLLOW_UP_CONCLUSIONS = ['有效', '无效', '待跟进'];
const LEAD_STAGES = ['初步接触', '需求确认', '方案报价', '商务谈判', '已转化', '已流失'];
const LEAD_SOURCES = ['电话营销', '网络推广', '客户介绍', '渠道合作', '展会', '地推陌拜', '其他'];
const OPPORTUNITY_STAGES = ['需求方案', '需求确认', '报价投标', '合同签订', '已成交', '已流失'];
const OPPORTUNITY_SOURCES = ['主动开发', '渠道推荐', '客户介绍', '老客户续签', '其他'];
const BUSINESS_TYPES = ['软件开发', '系统集成', '运维服务', '技术咨询', '产品销售', '其他'];
const PROJECT_STATUS = ['进行中', '已完成', '已暂停', '已取消'];

interface LeadRecord { id: number; lead_code: string; lead_name: string; lead_stage: string; lead_source: string; estimated_budget?: number; sales_owner_name: string; converted_to_opportunity: boolean; }
interface OpportunityRecord { id: number; opportunity_code: string; opportunity_name: string; opportunity_stage: string; expected_contract_amount?: number; sales_owner_name: string; channel_name?: string; project_id?: number; }
interface ProjectRecord { id: number; project_code: string; project_name: string; project_status: string; business_type: string; downstream_contract_amount?: number; sales_owner_name: string; }

const CustomerFullViewPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { message } = App.useApp();
  const customerId = Number(id);
  const { user } = useSelector((state: RootState) => state.auth);
  const { data, isLoading, refetch } = useCustomerFullView(customerId);
  const { data: productInstallations = [], isLoading: piLoading } = useProductInstallations(customerId);
  const { data: channelLinks = [], isLoading: clLoading } = useCustomerChannelLinks(customerId);
  
  const createPIMutation = useCreateProductInstallation();
  const updatePIMutation = useUpdateProductInstallation();
  const deletePIMutation = useDeleteProductInstallation();
  const createFollowUpMutation = useCreateFollowUp();
  const updateFollowUpMutation = useUpdateFollowUp();
  const deleteFollowUpMutation = useDeleteFollowUp();
  const createLeadMutation = useCreateLead();
  const createOpportunityMutation = useCreateOpportunity();
  const createProjectMutation = useCreateProject();
  const { data: productTypeOptions = [] } = useProductTypeCascader();
  const { data: channels = [] } = useChannels();
  const channelOptions = channels.map(c => ({ value: c.id, label: c.company_name }));
  
  const [piModalVisible, setPiModalVisible] = useState(false);
  const [editingPI, setEditingPI] = useState<ProductInstallation | null>(null);
  const [piForm] = Form.useForm();
  const [followUpModalVisible, setFollowUpModalVisible] = useState(false);
  const [editingFollowUp, setEditingFollowUp] = useState<RelatedFollowUp | null>(null);
  const [followUpForm] = Form.useForm();
  const [leadModalVisible, setLeadModalVisible] = useState(false);
  const [leadForm] = Form.useForm();
  const [opportunityModalVisible, setOpportunityModalVisible] = useState(false);
  const [opportunityForm] = Form.useForm();
  const [projectModalVisible, setProjectModalVisible] = useState(false);
  const [projectForm] = Form.useForm();
  const [contractModalVisible, setContractModalVisible] = useState(false);
  const [contractForm] = Form.useForm();

  if (isLoading) {
    return <Skeleton active paragraph={{ rows: 10 }} />;
  }

  if (!data) {
    return (
      <Result
        status="404"
        title="客户不存在"
        subTitle="该客户可能已被删除或您无权查看"
        extra={<Button type="primary" onClick={() => navigate('/customers')}>返回客户列表</Button>}
      />
    );
  }

  const isFinanceView = 'customer_id' in data;
  const customerName = isFinanceView ? data.customer_name : data.customer.customer_name;
  const customerIdNum = customerId;

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = { '意向客户': 'blue', '潜在客户': 'cyan', '成交客户': 'green', '流失客户': 'red' };
    return colors[status] || 'default';
  };

  const getStageColor = (stage: string) => {
    const colors: Record<string, string> = { '初步接触': 'blue', '需求确认': 'cyan', '方案报价': 'gold', '商务谈判': 'purple', '已转化': 'green', '已流失': 'red' };
    return colors[stage] || 'default';
  };

  const getOppStageColor = (stage: string) => {
    const colors: Record<string, string> = { '需求方案': 'blue', '需求确认': 'cyan', '报价投标': 'gold', '合同签订': 'purple', '已成交': 'green', '已流失': 'red' };
    return colors[stage] || 'default';
  };

  const handleAddPI = () => { setEditingPI(null); piForm.resetFields(); setPiModalVisible(true); };
  const handleEditPI = (record: ProductInstallation) => {
    setEditingPI(record);
    const productTypeArray = record.product_type ? record.product_type.split(' / ') : [];
    piForm.setFieldsValue({ 
      ...record, 
      product_type: productTypeArray.length > 0 ? productTypeArray : undefined,
      online_date: record.online_date ? dayjs(record.online_date) : null, 
      maintenance_expiry: record.maintenance_expiry ? dayjs(record.maintenance_expiry) : null 
    });
    setPiModalVisible(true);
  };
  const handleDeletePI = async (recordId: number) => { try { await deletePIMutation.mutateAsync(recordId); message.success('删除成功'); } catch (e: any) { } };
  const handlePIModalOk = async () => {
    try {
      const values = await piForm.validateFields();
      const submitData = { 
        ...values, 
        customer_id: customerId, 
        product_type: values.product_type ? values.product_type.join(' / ') : '',
        online_date: values.online_date?.format('YYYY-MM-DD'), 
        maintenance_expiry: values.maintenance_expiry?.format('YYYY-MM-DD') 
      };
      if (editingPI) { await updatePIMutation.mutateAsync({ id: editingPI.id, data: submitData as ProductInstallationUpdate }); message.success('更新成功'); }
      else { await createPIMutation.mutateAsync(submitData as ProductInstallationCreate); message.success('创建成功'); }
      setPiModalVisible(false); piForm.resetFields();
    } catch (e: any) { }
  };

  const handleAddLead = () => {
    leadForm.resetFields();
    leadForm.setFieldsValue({ lead_stage: '初步接触', has_confirmed_requirement: false, has_confirmed_budget: false });
    setLeadModalVisible(true);
  };
  const handleViewLead = (record: LeadRecord) => navigate(`/leads/${record.id}/full`);
  const handleLeadModalOk = async () => {
    try {
      const values = await leadForm.validateFields();
      const submitData = { ...values, terminal_customer_id: customerIdNum, sales_owner_id: user?.id };
      await createLeadMutation.mutateAsync(submitData);
      message.success('线索创建成功');
      setLeadModalVisible(false);
      leadForm.resetFields();
      refetch();
    } catch (e: any) { }
  };

const handleAddOpportunity = () => {
    opportunityForm.resetFields();
    opportunityForm.setFieldsValue({ opportunity_stage: '需求方案', opportunity_source: '主动开发' });
    setOpportunityModalVisible(true);
  };
 const handleViewOpportunity = (record: OpportunityRecord) => navigate(`/opportunities/${record.id}/full`);
  const handleOpportunityModalOk = async () => {
    try {
      const values = await opportunityForm.validateFields();
      const submitData = { ...values, terminal_customer_id: customerIdNum, sales_owner_id: user?.id };
      await createOpportunityMutation.mutateAsync(submitData);
      message.success('商机创建成功');
      setOpportunityModalVisible(false);
      opportunityForm.resetFields();
      refetch();
    } catch (e: any) { }
  };

  const handleAddProject = () => {
    projectForm.resetFields();
    projectForm.setFieldsValue({ project_status: '进行中', business_type: '系统集成' });
    setProjectModalVisible(true);
  };
  const handleViewProject = (record: ProjectRecord) => navigate(`/projects/${record.id}/full`);
  const handleProjectModalOk = async () => {
    try {
      const values = await projectForm.validateFields();
      const submitData = { ...values, terminal_customer_id: customerIdNum, sales_owner_id: user?.id };
      await createProjectMutation.mutateAsync(submitData);
      message.success('项目创建成功');
      setProjectModalVisible(false);
      projectForm.resetFields();
      refetch();
    } catch (e: any) { }
  };

  const handleAddFollowUp = () => { setEditingFollowUp(null); followUpForm.resetFields(); followUpForm.setFieldsValue({ follow_up_date: dayjs(), follow_up_method: '电话', follow_up_conclusion: '有效' }); setFollowUpModalVisible(true); };
  const handleEditFollowUp = (record: RelatedFollowUp) => { setEditingFollowUp(record); followUpForm.setFieldsValue({ ...record, follow_up_date: record.follow_up_date ? dayjs(record.follow_up_date) : null }); setFollowUpModalVisible(true); };
  const handleDeleteFollowUp = async (recordId: number) => { try { await deleteFollowUpMutation.mutateAsync(recordId); message.success('删除成功'); refetch(); } catch (e: any) { } };
  const handleFollowUpModalOk = async () => {
    try {
      const values = await followUpForm.validateFields();
      const submitData = { ...values, terminal_customer_id: customerId, follow_up_date: values.follow_up_date?.format('YYYY-MM-DD') };
      if (editingFollowUp) { await updateFollowUpMutation.mutateAsync({ id: editingFollowUp.id, data: submitData }); message.success('更新成功'); }
      else { await createFollowUpMutation.mutateAsync(submitData); message.success('创建成功'); }
      setFollowUpModalVisible(false); followUpForm.resetFields(); refetch();
    } catch (e: any) { }
  };

  const piColumns = [
    { title: '厂商', dataIndex: 'manufacturer', key: 'manufacturer', width: 80, render: (v: string) => <Tag color="blue">{v}</Tag> },
    { title: '产品类型', dataIndex: 'product_type', key: 'product_type', width: 100 },
    { title: '产品型号', dataIndex: 'product_model', key: 'product_model', width: 100, render: (v: string) => v || '-' },
    { title: '授权规模', dataIndex: 'license_scale', key: 'license_scale', width: 80, render: (v: string) => v || '-' },
    { title: '系统版本', dataIndex: 'system_version', key: 'system_version', width: 80, render: (v: string) => v || '-' },
    { title: '上线时间', dataIndex: 'online_date', key: 'online_date', width: 100, render: (v: string) => v || '-' },
    { title: '维保到期', dataIndex: 'maintenance_expiry', key: 'maintenance_expiry', width: 100, render: (v: string) => v || '-' },
    { title: '用户名', dataIndex: 'username', key: 'username', width: 100, render: (v: string) => v || '-' },
    { title: '密码', dataIndex: 'password', key: 'password', width: 80, render: (v: string) => v || '-' },
    { title: '登录地址', dataIndex: 'login_url', key: 'login_url', width: 150, ellipsis: true, render: (v: string) => v || '-' },
    { title: '操作', key: 'action', width: 60, render: (_: any, record: ProductInstallation) => {
      const items: MenuProps['items'] = [
        { key: 'edit', icon: <EditOutlined />, label: '编辑', onClick: () => handleEditPI(record) },
        { key: 'delete', icon: <DeleteOutlined />, label: <Popconfirm title="确认删除?" onConfirm={() => handleDeletePI(record.id)} okText="确认" cancelText="取消"><span style={{ color: '#ff4d4f' }}>删除</span></Popconfirm> },
      ];
      return <Dropdown menu={{ items }} trigger={['click']}><Button size="small" icon={<MoreOutlined />} /></Dropdown>;
    }},
  ];

  const leadColumns = [
    { title: '线索编号', dataIndex: 'lead_code', key: 'lead_code', width: 150 },
    { title: '线索名称', dataIndex: 'lead_name', key: 'lead_name' },
    { title: '阶段', dataIndex: 'lead_stage', key: 'lead_stage', width: 100, render: (s: string) => <Tag color={getStageColor(s)}>{s}</Tag> },
    { title: '来源', dataIndex: 'lead_source', key: 'lead_source', width: 100 },
    { title: '预计预算/元', dataIndex: 'estimated_budget', key: 'estimated_budget', width: 120, render: (v: number) => v ? `¥${v.toLocaleString()}` : '-' },
    { title: '负责人', dataIndex: 'sales_owner_name', key: 'sales_owner_name', width: 100 },
    { title: '状态', dataIndex: 'converted_to_opportunity', key: 'converted_to_opportunity', width: 100, render: (v: boolean) => v ? <Tag color="green">已转化</Tag> : <Tag color="blue">跟进中</Tag> },
    { title: '操作', key: 'action', width: 60, render: (_: any, record: LeadRecord) => {
      const items: MenuProps['items'] = [
        { key: 'view', icon: <EyeOutlined />, label: '查看', onClick: () => handleViewLead(record) },
      ];
      return <Dropdown menu={{ items }} trigger={['click']}><Button size="small" icon={<MoreOutlined />} /></Dropdown>;
    }},
  ];

  const opportunityColumns = [
    { title: '商机编号', dataIndex: 'opportunity_code', key: 'opportunity_code', width: 150 },
    { title: '商机名称', dataIndex: 'opportunity_name', key: 'opportunity_name' },
    { title: '阶段', dataIndex: 'opportunity_stage', key: 'opportunity_stage', width: 100, render: (s: string) => <Tag color={getOppStageColor(s)}>{s}</Tag> },
    { title: '预计金额/元', dataIndex: 'expected_contract_amount', key: 'expected_contract_amount', width: 120, render: (v: number) => v ? `¥${v.toLocaleString()}` : '-' },
    { title: '负责人', dataIndex: 'sales_owner_name', key: 'sales_owner_name', width: 100 },
    { title: '渠道', dataIndex: 'channel_name', key: 'channel_name', width: 100, render: (v: string) => v || '-' },
    { title: '项目', dataIndex: 'project_id', key: 'project_id', width: 80, render: (v: number) => v ? <Tag color="blue">已转项目</Tag> : '-' },
    { title: '操作', key: 'action', width: 60, render: (_: any, record: OpportunityRecord) => {
      const items: MenuProps['items'] = [
        { key: 'view', icon: <EyeOutlined />, label: '查看', onClick: () => handleViewOpportunity(record) },
      ];
      return <Dropdown menu={{ items }} trigger={['click']}><Button size="small" icon={<MoreOutlined />} /></Dropdown>;
    }},
  ];

  const projectColumns = [
    { title: '项目编号', dataIndex: 'project_code', key: 'project_code', width: 150 },
    { title: '项目名称', dataIndex: 'project_name', key: 'project_name' },
    { title: '状态', dataIndex: 'project_status', key: 'project_status', width: 100, render: (s: string) => <Tag color="blue">{s}</Tag> },
    { title: '业务类型', dataIndex: 'business_type', key: 'business_type', width: 100 },
    { title: '合同金额/元', dataIndex: 'downstream_contract_amount', key: 'downstream_contract_amount', width: 120, render: (v: number) => v ? `¥${v.toLocaleString()}` : '-' },
    { title: '负责人', dataIndex: 'sales_owner_name', key: 'sales_owner_name', width: 100 },
    { title: '操作', key: 'action', width: 60, render: (_: any, record: ProjectRecord) => {
      const items: MenuProps['items'] = [
        { key: 'view', icon: <EyeOutlined />, label: '查看', onClick: () => handleViewProject(record) },
      ];
      return <Dropdown menu={{ items }} trigger={['click']}><Button size="small" icon={<MoreOutlined />} /></Dropdown>;
    }},
  ];

  const followUpColumns = [
    { title: '跟进日期', dataIndex: 'follow_up_date', key: 'follow_up_date', width: 120 },
    { title: '方式', dataIndex: 'follow_up_method', key: 'follow_up_method', width: 80 },
    { title: '内容', dataIndex: 'follow_up_content', key: 'follow_up_content', ellipsis: true },
    { title: '结论', dataIndex: 'follow_up_conclusion', key: 'follow_up_conclusion', width: 80, render: (s: string) => <Tag color="blue">{s}</Tag> },
    { title: '跟进人', dataIndex: 'follower_name', key: 'follower_name', width: 100 },
    { title: '操作', key: 'action', width: 60, render: (_: any, record: RelatedFollowUp) => {
      const items: MenuProps['items'] = [
        { key: 'edit', icon: <EditOutlined />, label: '编辑', onClick: () => handleEditFollowUp(record) },
        { key: 'delete', icon: <DeleteOutlined />, label: <Popconfirm title="确认删除?" onConfirm={() => handleDeleteFollowUp(record.id)} okText="确认" cancelText="取消"><span style={{ color: '#ff4d4f' }}>删除</span></Popconfirm> },
      ];
      return <Dropdown menu={{ items }} trigger={['click']}><Button size="small" icon={<MoreOutlined />} /></Dropdown>;
    }},
  ];

  const contractColumns = [
    { title: '合同编号', dataIndex: 'contract_code', key: 'contract_code', width: 150 },
    { title: '合同名称', dataIndex: 'contract_name', key: 'contract_name' },
    { title: '类型', dataIndex: 'contract_direction', key: 'contract_direction', width: 80, render: (d: string) => <Tag color={d === 'Downstream' ? 'blue' : 'orange'}>{d === 'Downstream' ? '下游' : '上游'}</Tag> },
    { title: '状态', dataIndex: 'contract_status', key: 'contract_status', width: 80, render: (s: string) => <Tag>{s}</Tag> },
    { title: '金额', dataIndex: 'contract_amount', key: 'contract_amount', width: 120, render: (v: number) => v ? `¥${v.toLocaleString()}` : '-' },
    { title: '签订日期', dataIndex: 'signing_date', key: 'signing_date', width: 110 },
  ];

  const channelLinkColumns = [
    { title: '渠道名称', dataIndex: 'channel_name', key: 'channel_name', width: 150 },
    { title: '渠道编号', dataIndex: 'channel_code', key: 'channel_code', width: 120 },
    { title: '角色', dataIndex: 'role', key: 'role', width: 100, render: (r: string) => <Tag color={r === '主渠道' ? 'green' : r === '协作渠道' ? 'blue' : 'default'}>{r}</Tag> },
    { title: '折扣率', dataIndex: 'discount_rate', key: 'discount_rate', width: 80, render: (v: number) => `${v}%` },
    { title: '生效日期', dataIndex: 'start_date', key: 'start_date', width: 110 },
    { title: '失效日期', dataIndex: 'end_date', key: 'end_date', width: 110 },
    { title: '备注', dataIndex: 'notes', key: 'notes', ellipsis: true },
  ];

  const tabItems = !isFinanceView ? [
    { key: 'product_installations', label: `产品装机 (${productInstallations.length})`, children: <div><Button type="primary" icon={<PlusOutlined />} style={{ marginBottom: 16 }} onClick={handleAddPI}>新增装机记录</Button><Table columns={piColumns} dataSource={productInstallations} rowKey="id" loading={piLoading} pagination={{ pageSize: 10 }} size="small" scroll={{ x: 1200 }} /></div> },
    { key: 'leads', label: `线索 (${(data as CustomerFullView).summary.leads_count})`, children: <div><Button type="primary" icon={<PlusOutlined />} style={{ marginBottom: 16 }} onClick={handleAddLead}>新增线索</Button><Table columns={leadColumns} dataSource={(data as CustomerFullView).leads} rowKey="id" pagination={{ pageSize: 10 }} size="small" /></div> },
    { key: 'opportunities', label: `商机 (${(data as CustomerFullView).summary.opportunities_count})`, children: <div><Button type="primary" icon={<PlusOutlined />} style={{ marginBottom: 16 }} onClick={handleAddOpportunity}>新增商机</Button><Table columns={opportunityColumns} dataSource={(data as CustomerFullView).opportunities} rowKey="id" pagination={{ pageSize: 10 }} size="small" /></div> },
    { key: 'projects', label: `项目 (${(data as CustomerFullView).summary.projects_count})`, children: <div><Button type="primary" icon={<PlusOutlined />} style={{ marginBottom: 16 }} onClick={handleAddProject}>新增项目</Button><Table columns={projectColumns} dataSource={(data as CustomerFullView).projects} rowKey="id" pagination={{ pageSize: 10 }} size="small" /></div> },
    { key: 'follow_ups', label: `跟进记录 (${(data as CustomerFullView).summary.follow_ups_count})`, children: <div><Button type="primary" icon={<PlusOutlined />} style={{ marginBottom: 16 }} onClick={handleAddFollowUp}>新增跟进</Button><Table columns={followUpColumns} dataSource={(data as CustomerFullView).follow_ups} rowKey="id" pagination={{ pageSize: 10 }} size="small" /></div> },
    { key: 'contracts', label: `合同 (${(data as CustomerFullView).summary.contracts_count})`, children: <Table columns={contractColumns} dataSource={(data as CustomerFullView).contracts} rowKey="id" pagination={{ pageSize: 10 }} size="small" /> },
    { key: 'channel_links', label: `合作渠道 (${channelLinks.length})`, children: <Table columns={channelLinkColumns} dataSource={channelLinks} rowKey="id" loading={clLoading} pagination={{ pageSize: 10 }} size="small" /> },
  ] : [];

  return (
    <PageScaffold
      title={`${isFinanceView ? data.customer_code : data.customer.customer_code} - ${customerName}`}
      breadcrumbItems={[
        { title: '首页', href: '/dashboard' },
        { title: '终端客户', href: '/customers' },
        { title: isFinanceView ? data.customer_code : data.customer.customer_code },
      ]}
      extra={<Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>返回</Button>}
    >
      {isFinanceView ? (
        <FinanceViewContent data={data as CustomerFinanceView} />
      ) : (
        <FullViewContent 
          data={data as CustomerFullView} 
          getStatusColor={getStatusColor}
          tabItems={tabItems}
        />
      )}

      {/* 产品装机 Drawer */}
      <Drawer title={editingPI ? '编辑产品装机' : '新增产品装机'} open={piModalVisible} onClose={() => setPiModalVisible(false)} width={520} maskClosable={false} destroyOnClose>
        <Alert message={`客户：${customerName}`} type="info" style={{ marginBottom: 16 }} />
        <Form form={piForm} layout="vertical">
          <Row gutter={16}>
            <Col span={12}><Form.Item name="manufacturer" label="厂商" rules={[{ required: true, message: '请选择厂商' }]}><Select placeholder="请选择厂商">{MANUFACTURERS.map(m => <Option key={m} value={m}>{m}</Option>)}</Select></Form.Item></Col>
            <Col span={12}><Form.Item name="product_type" label="产品类型" rules={[{ required: true, message: '请选择产品类型' }]}><Cascader options={productTypeOptions} placeholder="请选择产品类型" showSearch /></Form.Item></Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="product_model" label="产品型号"><Input placeholder="请输入产品型号" /></Form.Item></Col>
            <Col span={12}><Form.Item name="license_scale" label="授权规模"><Input placeholder="请输入授权规模" /></Form.Item></Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="system_version" label="系统版本"><Input placeholder="请输入系统版本" /></Form.Item></Col>
            <Col span={6}><Form.Item name="online_date" label="上线时间"><DatePicker style={{ width: '100%' }} /></Form.Item></Col>
            <Col span={6}><Form.Item name="maintenance_expiry" label="维保到期"><DatePicker style={{ width: '100%' }} /></Form.Item></Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}><Form.Item name="username" label="用户名"><Input placeholder="请输入用户名" /></Form.Item></Col>
            <Col span={8}><Form.Item name="password" label="密码"><Input.Password placeholder="请输入密码" /></Form.Item></Col>
            <Col span={8}><Form.Item name="login_url" label="登录地址"><Input placeholder="请输入登录地址" /></Form.Item></Col>
          </Row>
          <Form.Item name="notes" label="备注"><TextArea rows={3} placeholder="请输入备注" /></Form.Item>
          <Form.Item><Button type="primary" onClick={handlePIModalOk} loading={createPIMutation.isPending || updatePIMutation.isPending} block>保存</Button></Form.Item>
        </Form>
      </Drawer>

      {/* 线索 Drawer */}
      <Drawer title="新增线索" open={leadModalVisible} onClose={() => setLeadModalVisible(false)} width={520} maskClosable={false} destroyOnClose>
        <Alert message={`客户：${customerName}`} type="info" style={{ marginBottom: 16 }} />
        <Form form={leadForm} layout="vertical">
          <Form.Item name="lead_name" label="线索名称" rules={[{ required: true, message: '请输入线索名称' }]}><Input placeholder="请输入线索名称" /></Form.Item>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="lead_stage" label="阶段" rules={[{ required: true, message: '请选择阶段' }]}><Select placeholder="请选择阶段">{LEAD_STAGES.map(s => <Option key={s} value={s}>{s}</Option>)}</Select></Form.Item></Col>
            <Col span={12}><Form.Item name="lead_source" label="来源"><Select placeholder="请选择来源" allowClear>{LEAD_SOURCES.map(s => <Option key={s} value={s}>{s}</Option>)}</Select></Form.Item></Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="source_channel_id" label="来源渠道" tooltip="归因渠道，创建后原则上不可修改"><Select placeholder="选择来源渠道" allowClear options={channelOptions} /></Form.Item></Col>
            <Col span={12}><Form.Item name="channel_id" label="协同渠道" tooltip="当前协同渠道，可随时修改"><Select placeholder="选择协同渠道" allowClear options={channelOptions} /></Form.Item></Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="estimated_budget" label="预计预算/元"><InputNumber style={{ width: '100%' }} placeholder="请输入预计预算" min={0} /></Form.Item></Col>
            <Col span={12}><Form.Item name="contact_person" label="联系人"><Input placeholder="请输入联系人" /></Form.Item></Col>
          </Row>
          <Form.Item name="contact_phone" label="联系电话"><Input placeholder="请输入联系电话" /></Form.Item>
          <Form.Item name="products" label="产品"><Select mode="multiple" placeholder="请选择产品" allowClear>{PRODUCTS.map(p => <Option key={p} value={p}>{p}</Option>)}</Select></Form.Item>
          <Form.Item name="notes" label="备注"><TextArea rows={3} placeholder="请输入备注" /></Form.Item>
          <Form.Item><Button type="primary" onClick={handleLeadModalOk} loading={createLeadMutation.isPending} block>保存</Button></Form.Item>
        </Form>
      </Drawer>

      {/* 商机 Drawer */}
      <Drawer title="新增商机" open={opportunityModalVisible} onClose={() => setOpportunityModalVisible(false)} width={520} maskClosable={false} destroyOnClose>
        <Alert message={`客户：${customerName}`} type="info" style={{ marginBottom: 16 }} />
        <Form form={opportunityForm} layout="vertical">
          <Form.Item name="opportunity_name" label="商机名称" rules={[{ required: true, message: '请输入商机名称' }]}><Input placeholder="请输入商机名称" /></Form.Item>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="opportunity_stage" label="阶段" rules={[{ required: true, message: '请选择阶段' }]}><Select placeholder="请选择阶段">{OPPORTUNITY_STAGES.map(s => <Option key={s} value={s}>{s}</Option>)}</Select></Form.Item></Col>
            <Col span={12}><Form.Item name="opportunity_source" label="来源"><Select placeholder="请选择来源" allowClear>{OPPORTUNITY_SOURCES.map(s => <Option key={s} value={s}>{s}</Option>)}</Select></Form.Item></Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="expected_contract_amount" label="预计金额/元"><InputNumber style={{ width: '100%' }} placeholder="请输入预计金额" min={0} /></Form.Item></Col>
            <Col span={12}><Form.Item name="expected_close_date" label="预计成交日期"><DatePicker style={{ width: '100%' }} /></Form.Item></Col>
          </Row>
          <Form.Item name="products" label="产品"><Select mode="multiple" placeholder="请选择产品" allowClear>{PRODUCTS.map(p => <Option key={p} value={p}>{p}</Option>)}</Select></Form.Item>
          <Form.Item name="notes" label="备注"><TextArea rows={3} placeholder="请输入备注" /></Form.Item>
          <Form.Item><Button type="primary" onClick={handleOpportunityModalOk} loading={createOpportunityMutation.isPending} block>保存</Button></Form.Item>
        </Form>
      </Drawer>

      {/* 项目 Drawer */}
      <Drawer title="新增项目" open={projectModalVisible} onClose={() => setProjectModalVisible(false)} width={520} maskClosable={false} destroyOnClose>
        <Alert message={`客户：${customerName}`} type="info" style={{ marginBottom: 16 }} />
        <Form form={projectForm} layout="vertical">
          <Form.Item name="project_name" label="项目名称" rules={[{ required: true, message: '请输入项目名称' }]}><Input placeholder="请输入项目名称" /></Form.Item>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="project_status" label="状态" rules={[{ required: true, message: '请选择状态' }]}><Select placeholder="请选择状态">{PROJECT_STATUS.map(s => <Option key={s} value={s}>{s}</Option>)}</Select></Form.Item></Col>
            <Col span={12}><Form.Item name="business_type" label="业务类型" rules={[{ required: true, message: '请选择业务类型' }]}><Select placeholder="请选择业务类型">{BUSINESS_TYPES.map(t => <Option key={t} value={t}>{t}</Option>)}</Select></Form.Item></Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="downstream_contract_amount" label="合同金额/元"><InputNumber style={{ width: '100%' }} placeholder="请输入合同金额" min={0} /></Form.Item></Col>
            <Col span={12}><Form.Item name="upstream_procurement_amount" label="采购金额/元"><InputNumber style={{ width: '100%' }} placeholder="请输入采购金额" min={0} /></Form.Item></Col>
          </Row>
          <Form.Item name="products" label="产品"><Select mode="multiple" placeholder="请选择产品" allowClear>{PRODUCTS.map(p => <Option key={p} value={p}>{p}</Option>)}</Select></Form.Item>
          <Form.Item name="description" label="项目描述"><TextArea rows={3} placeholder="请输入项目描述" /></Form.Item>
          <Form.Item name="notes" label="备注"><TextArea rows={2} placeholder="请输入备注" /></Form.Item>
          <Form.Item><Button type="primary" onClick={handleProjectModalOk} loading={createProjectMutation.isPending} block>保存</Button></Form.Item>
        </Form>
      </Drawer>

      {/* 跟进记录 Drawer */}
      <Drawer title={editingFollowUp ? '编辑跟进记录' : '新增跟进记录'} open={followUpModalVisible} onClose={() => setFollowUpModalVisible(false)} width={520} maskClosable={false} destroyOnClose>
        <Alert message={`客户：${customerName}`} type="info" style={{ marginBottom: 16 }} />
        <Form form={followUpForm} layout="vertical">
          <Form.Item name="follow_up_date" label="跟进日期" rules={[{ required: true, message: '请选择跟进日期' }]}><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="follow_up_method" label="跟进方式" rules={[{ required: true, message: '请选择跟进方式' }]}><Select>{FOLLOW_UP_METHODS.map(m => <Option key={m} value={m}>{m}</Option>)}</Select></Form.Item>
          <Form.Item name="follow_up_content" label="跟进内容" rules={[{ required: true, message: '请输入跟进内容' }]}><TextArea rows={4} placeholder="请输入跟进内容" /></Form.Item>
          <Form.Item name="follow_up_conclusion" label="跟进结论" rules={[{ required: true, message: '请选择跟进结论' }]}><Select>{FOLLOW_UP_CONCLUSIONS.map(c => <Option key={c} value={c}>{c}</Option>)}</Select></Form.Item>
          <Form.Item><Button type="primary" onClick={handleFollowUpModalOk} loading={createFollowUpMutation.isPending || updateFollowUpMutation.isPending} block>保存</Button></Form.Item>
        </Form>
      </Drawer>
    </PageScaffold>
  );
};

const FullViewContent: React.FC<{
  data: CustomerFullView;
  getStatusColor: (status: string) => string;
  tabItems: any[];
}> = ({ data, getStatusColor, tabItems }) => (
  <>
    <Card title="客户基本信息" style={{ marginBottom: 16 }} size="small">
      <Descriptions column={4} bordered size="small">
        <Descriptions.Item label="客户编号">{data.customer.customer_code}</Descriptions.Item>
        <Descriptions.Item label="客户名称">{data.customer.customer_name}</Descriptions.Item>
        <Descriptions.Item label="统一社会信用代码">{data.customer.credit_code}</Descriptions.Item>
        <Descriptions.Item label="行业">{data.customer.customer_industry}</Descriptions.Item>
        <Descriptions.Item label="区域">{data.customer.customer_region}</Descriptions.Item>
        <Descriptions.Item label="状态"><Tag color={getStatusColor(data.customer.customer_status)}>{data.customer.customer_status}</Tag></Descriptions.Item>
        <Descriptions.Item label="负责人"><UserOutlined style={{ marginRight: 4 }} />{data.customer.customer_owner_name}</Descriptions.Item>
        <Descriptions.Item label="主要联系人">{data.customer.main_contact || '-'}</Descriptions.Item>
        <Descriptions.Item label="电话"><PhoneOutlined style={{ marginRight: 4 }} />{data.customer.phone || '-'}</Descriptions.Item>
        <Descriptions.Item label="备注" span={3}>{data.customer.notes || '-'}</Descriptions.Item>
      </Descriptions>
    </Card>
    {data.channel && (
      <Card title="关联渠道" style={{ marginBottom: 16 }} size="small">
        <Descriptions column={4} bordered size="small">
          <Descriptions.Item label="渠道编号">{data.channel.channel_code}</Descriptions.Item>
          <Descriptions.Item label="公司名称">{data.channel.company_name}</Descriptions.Item>
          <Descriptions.Item label="类型">{data.channel.channel_type}</Descriptions.Item>
          <Descriptions.Item label="状态"><Tag color={data.channel.status === '合作中' ? 'green' : 'default'}>{data.channel.status}</Tag></Descriptions.Item>
          <Descriptions.Item label="主要联系人">{data.channel.main_contact || '-'}</Descriptions.Item>
          <Descriptions.Item label="电话">{data.channel.phone || '-'}</Descriptions.Item>
        </Descriptions>
      </Card>
    )}
    <Card title="关联信息"><Tabs items={tabItems} /></Card>
  </>
);

const FinanceViewContent: React.FC<{ data: CustomerFinanceView }> = ({ data }) => (
  <>
    <Row gutter={16} style={{ marginBottom: 24 }}>
      <Col span={6}><Card><Statistic title="合同总额" value={data.total_contract_amount} prefix={<FileTextOutlined />} precision={2} /></Card></Col>
      <Col span={6}><Card><Statistic title="下游合同" value={data.downstream_contract_amount} precision={2} /></Card></Col>
      <Col span={6}><Card><Statistic title="上游合同" value={data.upstream_contract_amount} precision={2} /></Card></Col>
      <Col span={6}><Card><Statistic title="回款进度" value={data.payment_completion_rate} suffix="%" precision={1} /></Card></Col>
    </Row>
    <Card title="客户基本信息" style={{ marginBottom: 16 }} size="small">
      <Descriptions column={4} bordered size="small">
        <Descriptions.Item label="客户编号">{data.customer_code}</Descriptions.Item>
        <Descriptions.Item label="客户名称">{data.customer_name}</Descriptions.Item>
        <Descriptions.Item label="统一社会信用代码">{data.credit_code}</Descriptions.Item>
        <Descriptions.Item label="状态"><Tag>{data.customer_status}</Tag></Descriptions.Item>
      </Descriptions>
    </Card>
    <Card title="合同列表" style={{ marginBottom: 16 }}>
      <Table
        dataSource={data.contracts}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        columns={[
          { title: '合同编号', dataIndex: 'contract_code', key: 'contract_code' },
          { title: '合同名称', dataIndex: 'contract_name', key: 'contract_name' },
          { title: '类型', dataIndex: 'contract_direction', key: 'contract_direction', render: (d: string) => <Tag color={d === 'Downstream' ? 'blue' : 'orange'}>{d === 'Downstream' ? '下游' : '上游'}</Tag> },
          { title: '状态', dataIndex: 'contract_status', key: 'contract_status', render: (s: string) => <Tag>{s}</Tag> },
          { title: '金额', dataIndex: 'contract_amount', key: 'contract_amount', render: (v: number) => v ? `¥${v.toLocaleString()}` : '-' },
          { title: '签订日期', dataIndex: 'signing_date', key: 'signing_date' },
        ]}
      />
    </Card>
    <Card title="回款计划" style={{ marginBottom: 16 }}>
      <Table
        dataSource={data.payment_plans}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        columns={[
          { title: '合同', dataIndex: 'contract_code', key: 'contract_code' },
          { title: '阶段', dataIndex: 'plan_stage', key: 'plan_stage' },
          { title: '计划金额', dataIndex: 'plan_amount', key: 'plan_amount', render: (v: number) => `¥${v.toLocaleString()}` },
          { title: '计划日期', dataIndex: 'plan_date', key: 'plan_date' },
          { title: '实际金额', dataIndex: 'actual_amount', key: 'actual_amount', render: (v: number | null) => v ? `¥${v.toLocaleString()}` : '-' },
          { title: '实际日期', dataIndex: 'actual_date', key: 'actual_date' },
          { title: '状态', dataIndex: 'payment_status', key: 'payment_status', render: (s: string) => <Tag color={s === 'completed' ? 'green' : s === 'partial' ? 'orange' : 'blue'}>{s === 'completed' ? '已完成' : s === 'partial' ? '部分完成' : '待支付'}</Tag> },
        ]}
      />
    </Card>
    <Card title="项目财务">
      <Table
        dataSource={data.projects}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        columns={[
          { title: '项目编号', dataIndex: 'project_code', key: 'project_code' },
          { title: '项目名称', dataIndex: 'project_name', key: 'project_name' },
          { title: '状态', dataIndex: 'project_status', key: 'project_status', render: (s: string) => <Tag>{s}</Tag> },
          { title: '下游合同金额', dataIndex: 'downstream_contract_amount', key: 'downstream_contract_amount', render: (v: number) => `¥${v.toLocaleString()}` },
          { title: '上游采购金额', dataIndex: 'upstream_procurement_amount', key: 'upstream_procurement_amount', render: (v: number | null) => v ? `¥${v.toLocaleString()}` : '-' },
          { title: '毛利', dataIndex: 'gross_margin', key: 'gross_margin', render: (v: number | null) => v ? `¥${v.toLocaleString()}` : '-' },
        ]}
      />
    </Card>
  </>
);

export default CustomerFullViewPage;
