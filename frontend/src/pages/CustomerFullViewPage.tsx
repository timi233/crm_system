import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { App, Card, Descriptions, Tag, Table, Tabs, Skeleton, Button, Space, Statistic, Row, Col, Typography, Popconfirm, Dropdown, Modal, Form, Input, Select, DatePicker, InputNumber, Alert, Result, Drawer, Cascader } from 'antd';
import type { MenuProps } from 'antd';
import type { RootState } from '../store/store';
import { ArrowLeftOutlined, UserOutlined, ShopOutlined, PhoneOutlined, FileTextOutlined, PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, MoreOutlined, ClockCircleOutlined } from '@ant-design/icons';
import PageScaffold from '../components/common/PageScaffold';
import PageModal from '../components/common/PageModal';
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
import { formatWan, fromWan, toWan } from '../utils/currency';

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

  const MASKED_CREDENTIAL_VALUE = '******';
  const credentialFields = ['username', 'password', 'login_url'] as const;
  const removeMaskedCredentialFields = (data: ProductInstallationUpdate) => {
    credentialFields.forEach((field) => {
      if (data[field] === MASKED_CREDENTIAL_VALUE || data[field] === undefined) {
        delete data[field];
      }
    });
  };

  const handleAddPI = () => { setEditingPI(null); piForm.resetFields(); setPiModalVisible(true); };
  const handleEditPI = (record: ProductInstallation) => {
    setEditingPI(record);
    const productTypeArray = record.product_type ? record.product_type.split(' / ') : [];
    piForm.setFieldsValue({
      ...record,
      product_type: productTypeArray.length > 0 ? productTypeArray : undefined,
      online_date: record.online_date ? dayjs(record.online_date) : null,
      maintenance_expiry: record.maintenance_expiry ? dayjs(record.maintenance_expiry) : null,
      username: undefined,
      password: undefined,
      login_url: undefined,
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
      if (editingPI) {
        const updateData = submitData as ProductInstallationUpdate;
        removeMaskedCredentialFields(updateData);
        await updatePIMutation.mutateAsync({ id: editingPI.id, data: updateData });
        message.success('更新成功');
      }
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
      const submitData = {
        ...values,
        estimated_budget: fromWan(values.estimated_budget),
        terminal_customer_id: customerIdNum,
        sales_owner_id: user?.id,
      };
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
      const submitData = {
        ...values,
        expected_contract_amount: fromWan(values.expected_contract_amount),
        terminal_customer_id: customerIdNum,
        sales_owner_id: user?.id,
      };
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
      const submitData = {
        ...values,
        downstream_contract_amount: fromWan(values.downstream_contract_amount),
        upstream_procurement_amount: fromWan(values.upstream_procurement_amount),
        terminal_customer_id: customerIdNum,
        sales_owner_id: user?.id,
      };
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
    { title: '预计预算(万元)', dataIndex: 'estimated_budget', key: 'estimated_budget', width: 120, render: (v: number) => formatWan(v) },
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
    { title: '预计金额(万元)', dataIndex: 'expected_contract_amount', key: 'expected_contract_amount', width: 120, render: (v: number) => formatWan(v) },
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
    { title: '合同金额(万元)', dataIndex: 'downstream_contract_amount', key: 'downstream_contract_amount', width: 120, render: (v: number) => formatWan(v) },
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
    { title: '金额(万元)', dataIndex: 'contract_amount', key: 'contract_amount', width: 120, render: (v: number) => formatWan(v) },
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
      title={customerName}
      breadcrumbItems={[
        { title: '首页', href: '/dashboard' },
        { title: '终端客户', href: '/customers' },
        { title: isFinanceView ? data.customer_code : data.customer.customer_code },
      ]}
      extra={
        <Space size={12}>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>返回</Button>
          {!isFinanceView && (
            <Dropdown
              menu={{
                items: [
                  { key: 'lead', label: '新增线索', icon: <PlusOutlined />, onClick: handleAddLead },
                  { key: 'opp', label: '新增商机', icon: <PlusOutlined />, onClick: handleAddOpportunity },
                  { key: 'proj', label: '新增项目', icon: <PlusOutlined />, onClick: handleAddProject },
                  { key: 'follow', label: '新增跟进', icon: <PhoneOutlined />, onClick: handleAddFollowUp },
                ],
              }}
            >
              <Button type="primary" className="btn--gradient" icon={<PlusOutlined />}>快捷操作</Button>
            </Dropdown>
          )}
        </Space>
      }
    >
      <div className="fade-in">
        {isFinanceView ? (
          <FinanceViewContent data={data as CustomerFinanceView} />
        ) : (
          <FullViewContent
            data={data as CustomerFullView}
            getStatusColor={getStatusColor}
            tabItems={tabItems}
          />
        )}
      </div>

      {/* 产品装机 Modal */}
      <PageModal
        title={editingPI ? '编辑产品装机信息' : '登记新产品装机'}
        open={piModalVisible}
        onClose={() => setPiModalVisible(false)}
        width={680}
        footer={[
          <Button key="cancel" onClick={() => setPiModalVisible(false)}>取消</Button>,
          <Button key="submit" type="primary" className="btn--gradient" onClick={handlePIModalOk} loading={createPIMutation.isPending || updatePIMutation.isPending}>保存入库</Button>
        ]}
      >
        <Alert message={`当前客户：${customerName}`} type="info" showIcon style={{ marginBottom: 24, borderRadius: '8px' }} />
        <Form form={piForm} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="manufacturer" label="厂商/品牌" rules={[{ required: true, message: '请选择厂商' }]}>
                <Select placeholder="选择品牌">{MANUFACTURERS.map(m => <Option key={m} value={m}>{m}</Option>)}</Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="product_type" label="产品分类" rules={[{ required: true, message: '请选择类型' }]}>
                <Cascader options={productTypeOptions} placeholder="选择产品分类" showSearch />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="product_model" label="规格型号"><Input placeholder="输入产品具体型号" /></Form.Item></Col>
            <Col span={12}><Form.Item name="license_scale" label="授权/装机规模"><Input placeholder="例如：500节点 / 10节点" /></Form.Item></Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="system_version" label="系统/固件版本"><Input placeholder="输入版本号" /></Form.Item></Col>
            <Col span={12}>
              <Row gutter={8}>
                <Col span={12}><Form.Item name="online_date" label="上线时间"><DatePicker style={{ width: '100%' }} /></Form.Item></Col>
                <Col span={12}><Form.Item name="maintenance_expiry" label="维保到期"><DatePicker style={{ width: '100%' }} /></Form.Item></Col>
              </Row>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}><Form.Item name="username" label="管理账号"><Input placeholder="用户名" /></Form.Item></Col>
            <Col span={8}><Form.Item name="password" label="管理密码"><Input.Password placeholder="密码" /></Form.Item></Col>
            <Col span={8}><Form.Item name="login_url" label="登录/访问地址"><Input placeholder="URL 或 IP" /></Form.Item></Col>
          </Row>
          <Form.Item name="notes" label="其他备注说明"><TextArea rows={3} placeholder="输入其他补充信息..." /></Form.Item>
        </Form>
      </PageModal>

      {/* 线索 Modal */}
      <PageModal
        title="建立新销售线索"
        open={leadModalVisible}
        onClose={() => setLeadModalVisible(false)}
        width={640}
        footer={[
          <Button key="cancel" onClick={() => setLeadModalVisible(false)}>取消</Button>,
          <Button key="submit" type="primary" className="btn--gradient" onClick={handleLeadModalOk} loading={createLeadMutation.isPending}>确认建立线索</Button>
        ]}
      >
        <Alert message={`当前客户：${customerName}`} type="info" showIcon style={{ marginBottom: 24, borderRadius: '8px' }} />
        <Form form={leadForm} layout="vertical">
          <Form.Item name="lead_name" label="线索名称" rules={[{ required: true, message: '请输入线索名称' }]}><Input placeholder="描述线索的核心内容，如：某系统扩容需求" /></Form.Item>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="lead_stage" label="跟进阶段" rules={[{ required: true, message: '请选择阶段' }]}>
              <Select placeholder="选择当前阶段">{LEAD_STAGES.map(s => <Option key={s} value={s}>{s}</Option>)}</Select>
            </Form.Item></Col>
            <Col span={12}><Form.Item name="lead_source" label="线索来源">
              <Select placeholder="来源途径" allowClear>{LEAD_SOURCES.map(s => <Option key={s} value={s}>{s}</Option>)}</Select>
            </Form.Item></Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="source_channel_id" label="来源渠道"><Select placeholder="选择来源渠道" allowClear options={channelOptions} /></Form.Item></Col>
            <Col span={12}><Form.Item name="channel_id" label="协同渠道"><Select placeholder="选择协同渠道" allowClear options={channelOptions} /></Form.Item></Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="estimated_budget" label="预计预算 (万元)"><InputNumber style={{ width: '100%' }} placeholder="0.0" precision={1} min={0} /></Form.Item></Col>
            <Col span={12}><Form.Item name="contact_person" label="对接联系人"><Input placeholder="联系人姓名" /></Form.Item></Col>
          </Row>
          <Form.Item name="contact_phone" label="联系电话"><Input placeholder="手机或固件" /></Form.Item>
          <Form.Item name="products" label="意向产品品牌"><Select mode="multiple" placeholder="选择涉及产品" allowClear>{PRODUCTS.map(p => <Option key={p} value={p}>{p}</Option>)}</Select></Form.Item>
          <Form.Item name="notes" label="线索备注"><TextArea rows={3} placeholder="补充其他信息..." /></Form.Item>
        </Form>
      </PageModal>

      {/* 商机 Modal */}
      <PageModal
        title="登记新商机项目"
        open={opportunityModalVisible}
        onClose={() => setOpportunityModalVisible(false)}
        width={640}
        footer={[
          <Button key="cancel" onClick={() => setOpportunityModalVisible(false)}>取消</Button>,
          <Button key="submit" type="primary" className="btn--gradient" onClick={handleOpportunityModalOk} loading={createOpportunityMutation.isPending}>保存并入库</Button>
        ]}
      >
        <Alert message={`当前客户：${customerName}`} type="info" showIcon style={{ marginBottom: 24, borderRadius: '8px' }} />
        <Form form={opportunityForm} layout="vertical">
          <Form.Item name="opportunity_name" label="商机名称" rules={[{ required: true, message: '请输入商机名称' }]}><Input placeholder="例如：某市电子政务平台建设" /></Form.Item>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="opportunity_stage" label="商机阶段" rules={[{ required: true, message: '请选择阶段' }]}>
              <Select placeholder="选择阶段">{OPPORTUNITY_STAGES.map(s => <Option key={s} value={s}>{s}</Option>)}</Select>
            </Form.Item></Col>
            <Col span={12}><Form.Item name="opportunity_source" label="商机来源">
              <Select placeholder="来源途径" allowClear>{OPPORTUNITY_SOURCES.map(s => <Option key={s} value={s}>{s}</Option>)}</Select>
            </Form.Item></Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="expected_contract_amount" label="预计合同金额 (万元)"><InputNumber style={{ width: '100%' }} placeholder="0.0" precision={1} min={0} /></Form.Item></Col>
            <Col span={12}><Form.Item name="expected_close_date" label="预计成交日期"><DatePicker style={{ width: '100%' }} /></Form.Item></Col>
          </Row>
          <Form.Item name="products" label="涉及产品品牌"><Select mode="multiple" placeholder="选择涉及产品" allowClear>{PRODUCTS.map(p => <Option key={p} value={p}>{p}</Option>)}</Select></Form.Item>
          <Form.Item name="notes" label="商机详细说明"><TextArea rows={3} placeholder="输入商机背景和关键信息..." /></Form.Item>
        </Form>
      </PageModal>

      {/* 项目 Modal */}
      <PageModal
        title="建立新交付项目"
        open={projectModalVisible}
        onClose={() => setProjectModalVisible(false)}
        width={720}
        footer={[
          <Button key="cancel" onClick={() => setProjectModalVisible(false)}>取消</Button>,
          <Button key="submit" type="primary" className="btn--gradient" onClick={handleProjectModalOk} loading={createProjectMutation.isPending}>建立项目工程</Button>
        ]}
      >
        <Alert message={`当前客户：${customerName}`} type="info" showIcon style={{ marginBottom: 24, borderRadius: '8px' }} />
        <Form form={projectForm} layout="vertical">
          <Form.Item name="project_name" label="项目名称" rules={[{ required: true, message: '请输入项目名称' }]}><Input placeholder="输入项目正式名称" /></Form.Item>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="project_status" label="项目状态" rules={[{ required: true, message: '请选择状态' }]}>
              <Select placeholder="选择状态">{PROJECT_STATUS.map(s => <Option key={s} value={s}>{s}</Option>)}</Select>
            </Form.Item></Col>
            <Col span={12}><Form.Item name="business_type" label="业务性质" rules={[{ required: true, message: '请选择业务类型' }]}>
              <Select placeholder="选择业务性质">{BUSINESS_TYPES.map(t => <Option key={t} value={t}>{t}</Option>)}</Select>
            </Form.Item></Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="downstream_contract_amount" label="下游合同金额 (万元)"><InputNumber style={{ width: '100%' }} placeholder="0.0" precision={1} min={0} /></Form.Item></Col>
            <Col span={12}><Form.Item name="upstream_procurement_amount" label="上游采购金额 (万元)"><InputNumber style={{ width: '100%' }} placeholder="0.0" precision={1} min={0} /></Form.Item></Col>
          </Row>
          <Form.Item name="products" label="涉及产品清单"><Select mode="multiple" placeholder="选择产品品牌" allowClear>{PRODUCTS.map(p => <Option key={p} value={p}>{p}</Option>)}</Select></Form.Item>
          <Form.Item name="description" label="项目整体描述"><TextArea rows={3} placeholder="简述项目建设目标和规模..." /></Form.Item>
          <Form.Item name="notes" label="补充备注信息"><TextArea rows={2} placeholder="其他需要说明的事项..." /></Form.Item>
        </Form>
      </PageModal>

      {/* 跟进记录 Modal */}
      <PageModal
        title={editingFollowUp ? '修改跟进详情' : '记录新业务进展'}
        open={followUpModalVisible}
        onClose={() => setFollowUpModalVisible(false)}
        width={600}
        footer={[
          <Button key="cancel" onClick={() => setFollowUpModalVisible(false)}>取消</Button>,
          <Button key="submit" type="primary" className="btn--gradient" onClick={handleFollowUpModalOk} loading={createFollowUpMutation.isPending || updateFollowUpMutation.isPending}>保存记录</Button>
        ]}
      >
        <Alert message={`当前客户：${customerName}`} type="info" showIcon style={{ marginBottom: 24, borderRadius: '8px' }} />
        <Form form={followUpForm} layout="vertical">
          <Row gutter={16}>
            <Col span={12}><Form.Item name="follow_up_date" label="沟通日期" rules={[{ required: true, message: '请选择日期' }]}><DatePicker style={{ width: '100%' }} /></Form.Item></Col>
            <Col span={12}><Form.Item name="follow_up_method" label="沟通方式" rules={[{ required: true, message: '请选择方式' }]}>
              <Select placeholder="选择方式">{FOLLOW_UP_METHODS.map(m => <Option key={m} value={m}>{m}</Option>)}</Select>
            </Form.Item></Col>
          </Row>
          <Form.Item name="follow_up_content" label="进展/内容摘要" rules={[{ required: true, message: '请输入跟进内容' }]}><TextArea rows={5} placeholder="详细记录沟通内容和达成的一致意见..." /></Form.Item>
          <Form.Item name="follow_up_conclusion" label="定性结论" rules={[{ required: true, message: '请选择跟进结论' }]}>
            <Select placeholder="选择结论">{FOLLOW_UP_CONCLUSIONS.map(c => <Option key={c} value={c}>{c}</Option>)}</Select>
          </Form.Item>
        </Form>
      </PageModal>
    </PageScaffold>
  );
};

const FullViewContent: React.FC<{
  data: CustomerFullView;
  getStatusColor: (status: string) => string;
  tabItems: any[];
}> = ({ data, getStatusColor, tabItems }) => (
  <Space direction="vertical" size={24} style={{ width: '100%' }}>
    <div style={{
      background: '#f8fafc',
      padding: '24px',
      borderRadius: '12px',
      border: '1px solid #f1f5f9'
    }}>
      <Descriptions
        title={<span style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a' }}>基本信息</span>}
        column={4}
        size="middle"
      >
        <Descriptions.Item label="客户编号"><span style={{ fontWeight: 600, color: '#1e293b' }}>{data.customer.customer_code}</span></Descriptions.Item>
        <Descriptions.Item label="统一社会信用代码">{data.customer.credit_code}</Descriptions.Item>
        <Descriptions.Item label="行业"><Tag color="default" style={{ border: 'none', background: '#e2e8f0' }}>{data.customer.customer_industry}</Tag></Descriptions.Item>
        <Descriptions.Item label="状态"><Tag color={getStatusColor(data.customer.customer_status)} style={{ border: 'none' }}>{data.customer.customer_status}</Tag></Descriptions.Item>
        <Descriptions.Item label="区域">{data.customer.customer_region}</Descriptions.Item>
        <Descriptions.Item label="负责人"><Space size={4}><UserOutlined style={{ color: 'var(--primary-color)' }} />{data.customer.customer_owner_name}</Space></Descriptions.Item>
        <Descriptions.Item label="主要联系人">{data.customer.main_contact || '-'}</Descriptions.Item>
        <Descriptions.Item label="电话"><Space size={4}><PhoneOutlined style={{ color: '#64748b' }} />{data.customer.phone || '-'}</Space></Descriptions.Item>
        <Descriptions.Item label="备注" span={4}>{data.customer.notes || '-'}</Descriptions.Item>
      </Descriptions>
    </div>

    {data.channel && (
      <div style={{
        background: '#eff6ff',
        padding: '24px',
        borderRadius: '12px',
        border: '1px solid #dbeafe'
      }}>
        <Descriptions
          title={<span style={{ fontSize: '16px', fontWeight: 700, color: '#1e40af' }}>关联渠道</span>}
          column={3}
          size="middle"
        >
          <Descriptions.Item label="渠道编号">{data.channel.channel_code}</Descriptions.Item>
          <Descriptions.Item label="公司名称"><span style={{ fontWeight: 600 }}>{data.channel.company_name}</span></Descriptions.Item>
          <Descriptions.Item label="类型">{data.channel.channel_type}</Descriptions.Item>
          <Descriptions.Item label="状态"><Tag color={data.channel.status === '合作中' ? 'green' : 'default'} style={{ border: 'none' }}>{data.channel.status}</Tag></Descriptions.Item>
          <Descriptions.Item label="主要联系人">{data.channel.main_contact || '-'}</Descriptions.Item>
          <Descriptions.Item label="电话">{data.channel.phone || '-'}</Descriptions.Item>
        </Descriptions>
      </div>
    )}

    <div className="modern-tabs-container">
      <Tabs
        items={tabItems}
        type="card"
        className="custom-tabs"
      />
    </div>
  </Space>
);

const FinanceViewContent: React.FC<{ data: CustomerFinanceView }> = ({ data }) => (
  <Space direction="vertical" size={24} style={{ width: '100%' }}>
    <Row gutter={20}>
      <Col span={6}>
        <div style={{ background: 'white', padding: '24px', borderRadius: '12px', border: '1px solid #f1f5f9', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
          <Statistic
            title={<span style={{ color: '#64748b', fontSize: '13px', fontWeight: 500 }}>合同总额(万元)</span>}
            value={toWan(data.total_contract_amount)}
            precision={1}
            valueStyle={{ fontWeight: 800, color: '#0f172a', letterSpacing: '-0.5px' }}
          />
        </div>
      </Col>
      <Col span={6}>
        <div style={{ background: 'white', padding: '24px', borderRadius: '12px', border: '1px solid #f1f5f9', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
          <Statistic
            title={<span style={{ color: '#64748b', fontSize: '13px', fontWeight: 500 }}>下游合同(万元)</span>}
            value={toWan(data.downstream_contract_amount)}
            precision={1}
            valueStyle={{ fontWeight: 800, color: '#0f172a', letterSpacing: '-0.5px' }}
          />
        </div>
      </Col>
      <Col span={6}>
        <div style={{ background: 'white', padding: '24px', borderRadius: '12px', border: '1px solid #f1f5f9', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
          <Statistic
            title={<span style={{ color: '#64748b', fontSize: '13px', fontWeight: 500 }}>上游合同(万元)</span>}
            value={toWan(data.upstream_contract_amount)}
            precision={1}
            valueStyle={{ fontWeight: 800, color: '#0f172a', letterSpacing: '-0.5px' }}
          />
        </div>
      </Col>
      <Col span={6}>
        <div style={{ background: 'white', padding: '24px', borderRadius: '12px', border: '1px solid #f1f5f9', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
          <Statistic
            title={<span style={{ color: '#64748b', fontSize: '13px', fontWeight: 500 }}>回款进度</span>}
            value={data.payment_completion_rate}
            suffix={<span style={{ fontSize: '14px', color: '#94a3b8', marginLeft: '4px' }}>%</span>}
            precision={1}
            valueStyle={{ fontWeight: 800, color: '#0052cc' }}
          />
        </div>
      </Col>
    </Row>

    <div style={{ background: 'white', padding: '24px', borderRadius: '12px', border: '1px solid #f1f5f9' }}>
      <Descriptions
        title={<span style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a' }}>基本财务信息</span>}
        column={4}
        size="middle"
      >
        <Descriptions.Item label="客户编号">{data.customer_code}</Descriptions.Item>
        <Descriptions.Item label="客户名称"><span style={{ fontWeight: 600 }}>{data.customer_name}</span></Descriptions.Item>
        <Descriptions.Item label="信用代码">{data.credit_code}</Descriptions.Item>
        <Descriptions.Item label="状态"><Tag style={{ border: 'none', background: '#f1f5f9' }}>{data.customer_status}</Tag></Descriptions.Item>
      </Descriptions>
    </div>

    <Card title="合同列表" className="card--tertiary" bodyStyle={{ padding: 0 }}>
      <Table
        dataSource={data.contracts}
        rowKey="id"
        pagination={{ pageSize: 5 }}
        size="small"
        className="customer-table"
        columns={[
          { title: '合同编号', dataIndex: 'contract_code', key: 'contract_code' },
          { title: '合同名称', dataIndex: 'contract_name', key: 'contract_name' },
          { title: '类型', dataIndex: 'contract_direction', key: 'contract_direction', render: (d: string) => <Tag color={d === 'Downstream' ? 'blue' : 'orange'} style={{ border: 'none' }}>{d === 'Downstream' ? '下游' : '上游'}</Tag> },
          { title: '状态', dataIndex: 'contract_status', key: 'contract_status', render: (s: string) => <Tag style={{ border: 'none' }}>{s}</Tag> },
          { title: '金额(万元)', dataIndex: 'contract_amount', key: 'contract_amount', render: (v: number) => formatWan(v) },
          { title: '签订日期', dataIndex: 'signing_date', key: 'signing_date' },
        ]}
      />
    </Card>

    <Card title="回款计划" className="card--tertiary" bodyStyle={{ padding: 0 }}>
      <Table
        dataSource={data.payment_plans}
        rowKey="id"
        pagination={{ pageSize: 5 }}
        size="small"
        className="customer-table"
        columns={[
          { title: '合同', dataIndex: 'contract_code', key: 'contract_code' },
          { title: '阶段', dataIndex: 'plan_stage', key: 'plan_stage' },
          { title: '计划金额(万元)', dataIndex: 'plan_amount', key: 'plan_amount', render: (v: number) => formatWan(v) },
          { title: '计划日期', dataIndex: 'plan_date', key: 'plan_date' },
          { title: '实际金额(万元)', dataIndex: 'actual_amount', key: 'actual_amount', render: (v: number | null) => formatWan(v) },
          { title: '实际日期', dataIndex: 'actual_date', key: 'actual_date' },
          { title: '状态', dataIndex: 'payment_status', key: 'payment_status', render: (s: string) => <Tag color={s === 'completed' ? 'green' : s === 'partial' ? 'orange' : 'blue'} style={{ border: 'none' }}>{s === 'completed' ? '已完成' : s === 'partial' ? '部分完成' : '待支付'}</Tag> },
        ]}
      />
    </Card>
  </Space>
);

export default CustomerFullViewPage;
