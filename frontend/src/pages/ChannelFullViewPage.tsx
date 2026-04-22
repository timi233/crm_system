import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Descriptions, Tag, Table, Tabs, Skeleton, Button, Statistic, Row, Col, Typography, Result, Modal, Form, Input, Switch, Space, App, Popconfirm } from 'antd';
import { ArrowLeftOutlined, ShopOutlined, PhoneOutlined, MailOutlined, GlobalOutlined, EnvironmentOutlined, PlusOutlined, EditOutlined } from '@ant-design/icons';
import { useChannelFullView } from '../hooks/useChannelFullView';
import { useChannelWorkOrders } from '../hooks/useChannelWorkOrders';
import { useChannelAssignments } from '../hooks/useChannelAssignments';
import { useChannelExecutionPlans } from '../hooks/useChannelExecutionPlans';
import { useChannelTargets } from '../hooks/useChannelTargets';
import { useChannelFollowUps } from '../hooks/useChannelFollowUps';
import { useChannelLeads } from '../hooks/useChannelLeads';
import { ChannelContact, useChannelContacts, useCreateChannelContact, useDeleteChannelContact, useUpdateChannelContact } from '../hooks/useChannelContacts';
import PageScaffold from '../components/common/PageScaffold';
import FollowUpModal from '../components/modals/FollowUpModal';

const { TextArea } = Input;

const ChannelFullViewPage: React.FC = () => {
  const { message } = App.useApp();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const channelId = Number(id);
  const [activeTab, setActiveTab] = useState('customers');
  const [followUpModalVisible, setFollowUpModalVisible] = useState(false);
  const [contactModalVisible, setContactModalVisible] = useState(false);
  const [editingContact, setEditingContact] = useState<ChannelContact | null>(null);
  const [followUpsPage, setFollowUpsPage] = useState(1);
  const [leadsPage, setLeadsPage] = useState(1);
  const pageSize = 10;
  const [contactForm] = Form.useForm();
  
  const { data, isLoading } = useChannelFullView(channelId);
  
  const workOrdersQuery = useChannelWorkOrders(channelId, { enabled: activeTab === 'work_orders' });
  const assignmentsQuery = useChannelAssignments(channelId, { enabled: activeTab === 'assignments' });
  const executionPlansQuery = useChannelExecutionPlans(channelId, { enabled: activeTab === 'execution_plans' });
  const targetsQuery = useChannelTargets(channelId, { enabled: activeTab === 'targets' });
  const followUpsQuery = useChannelFollowUps(channelId, { enabled: activeTab === 'follow_ups', page: followUpsPage, pageSize });
  const leadsQuery = useChannelLeads(channelId, { enabled: activeTab === 'leads', page: leadsPage, pageSize });
  const contactsQuery = useChannelContacts(channelId, { enabled: activeTab === 'contacts' });
  const createContactMutation = useCreateChannelContact(channelId);
  const updateContactMutation = useUpdateChannelContact(channelId);
  const deleteContactMutation = useDeleteChannelContact(channelId);

  const handleTabChange = (key: string) => {
    setActiveTab(key);
  };

  const openCreateContactModal = () => {
    setEditingContact(null);
    contactForm.resetFields();
    contactForm.setFieldsValue({ is_primary: false });
    setContactModalVisible(true);
  };

  const openEditContactModal = (contact: ChannelContact) => {
    setEditingContact(contact);
    contactForm.setFieldsValue(contact);
    setContactModalVisible(true);
  };

  const handleSaveContact = async () => {
    try {
      const values = await contactForm.validateFields();
      if (editingContact) {
        await updateContactMutation.mutateAsync({
          contactId: editingContact.id,
          payload: values,
        });
        message.success('联系人已更新');
      } else {
        await createContactMutation.mutateAsync(values);
        message.success('联系人已创建');
      }
      setContactModalVisible(false);
      setEditingContact(null);
      contactForm.resetFields();
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  const handleDeleteContact = async (contactId: number) => {
    try {
      await deleteContactMutation.mutateAsync(contactId);
      message.success('联系人已删除');
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '删除联系人失败');
    }
  };

  if (isLoading) {
    return <Skeleton active paragraph={{ rows: 10 }} />;
  }

  if (!data) {
    return (
      <Result
        status="404"
        title="渠道不存在"
        subTitle="该渠道可能已被删除或您无权查看"
        extra={<Button type="primary" onClick={() => navigate('/channels')}>返回渠道列表</Button>}
      />
    );
  }

  const breadcrumbs = [
    { title: '首页', href: '/dashboard' },
    { title: '渠道档案', href: '/channels' },
    { title: data.channel.company_name, href: '#' },
  ];

  const getStatusColor = (status: string) => {
    return status === '合作中' ? 'green' : 'default';
  };

  const getOppStageColor = (stage: string) => {
    const colors: Record<string, string> = {
      '需求方案': 'blue',
      '需求确认': 'cyan',
      '报价投标': 'gold',
      '合同签订': 'purple',
      '已成交': 'green',
      '已流失': 'red',
    };
    return colors[stage] || 'default';
  };

  const customerColumns = [
    { title: '客户编号', dataIndex: 'customer_code', key: 'customer_code', width: 180 },
    { title: '客户名称', dataIndex: 'customer_name', key: 'customer_name' },
    { title: '关联类型', dataIndex: 'relation_type', key: 'relation_type', width: 170, render: (value: string) => <Tag color="geekblue">{value}</Tag> },
    { title: '行业', dataIndex: 'customer_industry', key: 'customer_industry' },
    { title: '区域', dataIndex: 'customer_region', key: 'customer_region' },
    { title: '状态', dataIndex: 'customer_status', key: 'customer_status', render: (s: string) => <Tag color="blue">{s}</Tag> },
    { title: '负责人', dataIndex: 'customer_owner_name', key: 'customer_owner_name' },
  ];

  const opportunityColumns = [
    { title: '商机编号', dataIndex: 'opportunity_code', key: 'opportunity_code', width: 180 },
    { title: '商机名称', dataIndex: 'opportunity_name', key: 'opportunity_name' },
    { title: '关联类型', dataIndex: 'relation_type', key: 'relation_type', width: 120, render: (value: string) => <Tag color="geekblue">{value}</Tag> },
    { title: '阶段', dataIndex: 'opportunity_stage', key: 'opportunity_stage', render: (s: string) => <Tag color={getOppStageColor(s)}>{s}</Tag> },
    { title: '预计金额', dataIndex: 'expected_contract_amount', key: 'expected_contract_amount', render: (v: number) => v ? `¥${v.toLocaleString()}` : '-' },
    { title: '终端客户', dataIndex: 'terminal_customer_name', key: 'terminal_customer_name' },
    { title: '负责人', dataIndex: 'sales_owner_name', key: 'sales_owner_name' },
    { title: '项目', dataIndex: 'project_id', key: 'project_id', render: (v: number) => v ? <Tag color="blue">已转项目</Tag> : '-' },
  ];

  const projectColumns = [
    { title: '项目编号', dataIndex: 'project_code', key: 'project_code', width: 180 },
    { title: '项目名称', dataIndex: 'project_name', key: 'project_name' },
    { title: '状态', dataIndex: 'project_status', key: 'project_status', render: (s: string) => <Tag color="blue">{s}</Tag> },
    { title: '业务类型', dataIndex: 'business_type', key: 'business_type' },
    { title: '合同金额', dataIndex: 'downstream_contract_amount', key: 'downstream_contract_amount', render: (v: number) => v ? `¥${v.toLocaleString()}` : '-' },
    { title: '终端客户', dataIndex: 'terminal_customer_name', key: 'terminal_customer_name' },
    { title: '负责人', dataIndex: 'sales_owner_name', key: 'sales_owner_name' },
  ];

  const contractColumns = [
    { title: '合同编号', dataIndex: 'contract_code', key: 'contract_code', width: 180 },
    { title: '合同名称', dataIndex: 'contract_name', key: 'contract_name' },
    { title: '类型', dataIndex: 'contract_direction', key: 'contract_direction', width: 80, render: (d: string) => <Tag color={d === 'Downstream' ? 'blue' : 'orange'}>{d === 'Downstream' ? '下游' : '上游'}</Tag> },
    { title: '状态', dataIndex: 'contract_status', key: 'contract_status', width: 80, render: (s: string) => <Tag>{s}</Tag> },
    { title: '金额', dataIndex: 'contract_amount', key: 'contract_amount', render: (v: number) => v ? `¥${v.toLocaleString()}` : '-' },
    { title: '签订日期', dataIndex: 'signing_date', key: 'signing_date', width: 110 },
  ];

  const workOrderColumns = [
    { title: '工单编号', dataIndex: 'work_order_no', key: 'work_order_no', width: 180 },
    { title: '工单类型', dataIndex: 'order_type', key: 'order_type' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s: string) => <Tag color="blue">{s}</Tag> },
    { title: '客户名称', dataIndex: 'customer_name', key: 'customer_name' },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  ];

  const assignmentColumns = [
    { title: '用户名称', dataIndex: 'user_name', key: 'user_name' },
    { title: '权限级别', dataIndex: 'permission_level', key: 'permission_level' },
    { title: '分配时间', dataIndex: 'assigned_at', key: 'assigned_at', width: 180 },
  ];

  const executionPlanColumns = [
    { title: '计划类型', dataIndex: 'plan_type', key: 'plan_type' },
    {
      title: '计划分类',
      dataIndex: 'plan_category',
      key: 'plan_category',
      render: (value: string) => (value === 'training' ? <Tag color="purple">培训</Tag> : <Tag>通用</Tag>),
    },
    { title: '计划周期', dataIndex: 'plan_period', key: 'plan_period' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s: string) => <Tag color="blue">{s}</Tag> },
    { title: '计划内容', dataIndex: 'plan_content', key: 'plan_content', ellipsis: true },
  ];

  const targetColumns = [
    { title: '年份', dataIndex: 'year', key: 'year', width: 100 },
    { title: '季度', dataIndex: 'quarter', key: 'quarter', width: 80 },
    { title: '月份', dataIndex: 'month', key: 'month', width: 80 },
    { title: '绩效目标(万元)', dataIndex: 'performance_target', key: 'performance_target', render: (v: number) => v ? `${(v / 10000).toLocaleString('zh-CN', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} 万元` : '-' },
    { title: '实际完成(万元)', dataIndex: 'achieved_performance', key: 'achieved_performance', render: (v: number) => v ? `${(v / 10000).toLocaleString('zh-CN', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} 万元` : '-' },
  ];

  const followUpColumns = [
    { title: '拜访日期', dataIndex: 'follow_up_date', key: 'follow_up_date', width: 120 },
    { title: '拜访方式', dataIndex: 'follow_up_method', key: 'follow_up_method', width: 100 },
    { title: '关联类型', dataIndex: 'relation_type', key: 'relation_type', width: 170, render: (value: string) => <Tag color="geekblue">{value || '渠道跟进'}</Tag> },
    { title: '拜访内容', dataIndex: 'follow_up_content', key: 'follow_up_content', ellipsis: true },
    { title: '拜访结论', dataIndex: 'follow_up_conclusion', key: 'follow_up_conclusion', width: 120, render: (value: string) => <Tag color="blue">{value || '-'}</Tag> },
    { title: '拜访目的', dataIndex: 'visit_purpose', key: 'visit_purpose', width: 120, render: (value: string) => value || '-' },
    { title: '拜访地点', dataIndex: 'visit_location', key: 'visit_location', width: 140, render: (value: string) => value || '-' },
    {
      title: '关联对象',
      key: 'related_entity',
      render: (_: unknown, record: any) => record.lead_name || record.opportunity_name || record.project_name || '-',
    },
    { title: '拜访人', dataIndex: 'follower_name', key: 'follower_name', width: 120 },
  ];

  const leadColumns = [
    { title: '线索编号', dataIndex: 'lead_code', key: 'lead_code', width: 180 },
    { title: '线索名称', dataIndex: 'lead_name', key: 'lead_name' },
    { title: '关联类型', dataIndex: 'relation_type', key: 'relation_type', width: 140, render: (value: string) => <Tag color="geekblue">{value}</Tag> },
    { title: '阶段', dataIndex: 'stage', key: 'stage', width: 120, render: (value: string) => <Tag color="cyan">{value}</Tag> },
    { title: '联系人', dataIndex: 'contact_person', key: 'contact_person', width: 140 },
    { title: '负责人', dataIndex: 'sales_owner_name', key: 'sales_owner_name', width: 140 },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 120 },
  ];

  const contactColumns = [
    {
      title: '姓名',
      dataIndex: 'name',
      key: 'name',
      render: (value: string, record: ChannelContact) => (
        <Space>
          <span>{value}</span>
          {record.is_primary ? <Tag color="gold">主联系人</Tag> : null}
        </Space>
      ),
    },
    { title: '职位', dataIndex: 'title', key: 'title', width: 140 },
    { title: '电话', dataIndex: 'phone', key: 'phone', width: 160 },
    { title: '邮箱', dataIndex: 'email', key: 'email', width: 220 },
    { title: '备注', dataIndex: 'notes', key: 'notes', ellipsis: true },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_: unknown, record: ChannelContact) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEditContactModal(record)}>
            编辑
          </Button>
          <Popconfirm title="确定删除该联系人？" onConfirm={() => handleDeleteContact(record.id)}>
            <Button size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const tabItems = [
    {
      key: 'customers',
      label: `关联客户 (${data.summary.customers_count})`,
      children: (
        <Table
          columns={customerColumns}
          dataSource={data.customers}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          size="small"
        />
      ),
    },
    {
      key: 'opportunities',
      label: `商机 (${data.summary.opportunities_count})`,
      children: (
        <Table
          columns={opportunityColumns}
          dataSource={data.opportunities}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          size="small"
        />
      ),
    },
    {
      key: 'projects',
      label: `项目 (${data.summary.projects_count})`,
      children: (
        <Table
          columns={projectColumns}
          dataSource={data.projects}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          size="small"
        />
      ),
    },
    {
      key: 'contracts',
      label: `合同 (${data.summary.contracts_count})`,
      children: (
        <Table
          columns={contractColumns}
          dataSource={data.contracts}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          size="small"
        />
      ),
    },
    {
      key: 'follow_ups',
      label: `渠道跟进 (${followUpsQuery.data?.total ?? 0})`,
      children: (
        <div>
          <Button type="primary" icon={<PlusOutlined />} style={{ marginBottom: 16 }} onClick={() => setFollowUpModalVisible(true)}>
            新增渠道跟进
          </Button>
          <Table
            columns={followUpColumns}
            dataSource={followUpsQuery.data?.items || []}
            rowKey="id"
            size="small"
            loading={followUpsQuery.isLoading}
            pagination={{
              current: followUpsPage,
              pageSize,
              total: followUpsQuery.data?.total || 0,
              onChange: (page) => setFollowUpsPage(page),
            }}
          />
        </div>
      ),
    },
    {
      key: 'leads',
      label: `线索 (${leadsQuery.data?.total ?? data.summary.leads_count ?? 0})`,
      children: (
        <Table
          columns={leadColumns}
          dataSource={leadsQuery.data?.items || data.leads || []}
          rowKey="id"
          size="small"
          loading={leadsQuery.isLoading}
          pagination={{
            current: leadsPage,
            pageSize,
            total: leadsQuery.data?.total || data.summary.leads_count || 0,
            onChange: (page) => setLeadsPage(page),
          }}
        />
      ),
    },
    {
      key: 'contacts',
      label: `联系人 (${contactsQuery.data?.length ?? 0})`,
      children: (
        <div>
          <Button type="primary" icon={<PlusOutlined />} style={{ marginBottom: 16 }} onClick={openCreateContactModal}>
            新增联系人
          </Button>
          <Table
            columns={contactColumns}
            dataSource={contactsQuery.data || []}
            rowKey="id"
            size="small"
            loading={contactsQuery.isLoading}
            pagination={false}
          />
        </div>
      ),
    },
    {
      key: 'work_orders',
      label: `工单记录 (${data.summary.work_orders_count})`,
      children: (
        <Table
          columns={workOrderColumns}
          dataSource={workOrdersQuery.data?.items || []}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          size="small"
          loading={workOrdersQuery.isLoading}
        />
      ),
    },
    {
      key: 'execution_plans',
      label: `执行计划 (${data.summary.execution_plans_count})`,
      children: (
        <Table
          columns={executionPlanColumns}
          dataSource={executionPlansQuery.data?.items || []}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          size="small"
          loading={executionPlansQuery.isLoading}
        />
      ),
    },
    {
      key: 'targets',
      label: `绩效目标 (${data.summary.targets_count})`,
      children: (
        <Table
          columns={targetColumns}
          dataSource={targetsQuery.data?.items || []}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          size="small"
          loading={targetsQuery.isLoading}
        />
      ),
    },
    {
      key: 'assignments',
      label: `渠道分配 (${data.summary.assignments_count})`,
      children: (
        <Table
          columns={assignmentColumns}
          dataSource={assignmentsQuery.data?.items || []}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          size="small"
          loading={assignmentsQuery.isLoading}
        />
      ),
    },
  ];

  return (
    <PageScaffold
      title={`${data.channel.channel_code} - ${data.channel.company_name}`}
      breadcrumbItems={[
        { title: '首页', href: '/dashboard' },
        { title: '渠道档案', href: '/channels' },
        { title: data.channel.channel_code },
      ]}
      extra={
        <>
          <Button onClick={() => navigate(`/channel-follow-ups?channel_id=${channelId}`)}>
            查看渠道跟进
          </Button>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>
            返回
          </Button>
        </>
      }
    >
      <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={3}>
            <Card>
              <Statistic
                title="关联客户数"
                value={data.summary.customers_count}
                prefix={<ShopOutlined />}
              />
            </Card>
          </Col>
          <Col span={3}>
            <Card>
              <Statistic
                title="商机数"
                value={data.summary.opportunities_count}
              />
            </Card>
          </Col>
          <Col span={3}>
            <Card>
              <Statistic
                title="项目数"
                value={data.summary.projects_count}
              />
            </Card>
          </Col>
          <Col span={3}>
            <Card>
              <Statistic
                title="合同数"
                value={data.summary.contracts_count}
              />
            </Card>
          </Col>
          <Col span={3}>
            <Card>
              <Statistic
                title="工单数"
                value={data.summary.work_orders_count}
              />
            </Card>
          </Col>
          <Col span={3}>
            <Card>
              <Statistic
                title="执行计划数"
                value={data.summary.execution_plans_count}
              />
            </Card>
          </Col>
          <Col span={3}>
            <Card>
              <Statistic
                title="绩效目标数"
                value={data.summary.targets_count}
              />
            </Card>
          </Col>
          <Col span={3}>
            <Card>
              <Statistic
                title="渠道分配数"
                value={data.summary.assignments_count}
              />
            </Card>
          </Col>
        </Row>

        <Card title="渠道基本信息" style={{ marginBottom: 16 }} size="small">
          <Descriptions column={4} bordered size="small">
            <Descriptions.Item label="渠道编号">{data.channel.channel_code}</Descriptions.Item>
            <Descriptions.Item label="公司名称">{data.channel.company_name}</Descriptions.Item>
            <Descriptions.Item label="类型">{data.channel.channel_type}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={getStatusColor(data.channel.status)}>{data.channel.status}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="主要联系人">{data.channel.main_contact || '-'}</Descriptions.Item>
            <Descriptions.Item label="电话">
              <PhoneOutlined style={{ marginRight: 4 }} />
              {data.channel.phone || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="邮箱">
              <MailOutlined style={{ marginRight: 4 }} />
              {data.channel.email || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="统一社会信用代码">{data.channel.credit_code || '-'}</Descriptions.Item>
            <Descriptions.Item label="省份">{data.channel.province || '-'}</Descriptions.Item>
            <Descriptions.Item label="城市">{data.channel.city || '-'}</Descriptions.Item>
            <Descriptions.Item label="详细地址" span={2}>
              <EnvironmentOutlined style={{ marginRight: 4 }} />
              {data.channel.address || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="官网">
              {data.channel.website ? (
                <a href={data.channel.website} target="_blank" rel="noopener noreferrer">
                  <GlobalOutlined style={{ marginRight: 4 }} />
                  {data.channel.website}
                </a>
              ) : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="微信公众号">{data.channel.wechat || '-'}</Descriptions.Item>
            <Descriptions.Item label="合作区域">{data.channel.cooperation_region || '-'}</Descriptions.Item>
            <Descriptions.Item label="折扣率">{data.channel.discount_rate ? `${(data.channel.discount_rate * 100).toFixed(2)}%` : '-'}</Descriptions.Item>
            <Descriptions.Item label="备注" span={4}>{data.channel.notes || '-'}</Descriptions.Item>
          </Descriptions>
        </Card>

        <Card title="关联信息">
          <Tabs items={tabItems} activeKey={activeTab} onChange={handleTabChange} />
        </Card>

      <FollowUpModal
        visible={followUpModalVisible}
        onClose={() => setFollowUpModalVisible(false)}
        channel_id={channelId}
      />

      <Modal
        title={editingContact ? '编辑联系人' : '新增联系人'}
        open={contactModalVisible}
        onOk={handleSaveContact}
        onCancel={() => {
          setContactModalVisible(false);
          setEditingContact(null);
          contactForm.resetFields();
        }}
        confirmLoading={createContactMutation.isPending || updateContactMutation.isPending}
      >
        <Form form={contactForm} layout="vertical">
          <Form.Item name="name" label="姓名" rules={[{ required: true, message: '请输入联系人姓名' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="title" label="职位">
            <Input />
          </Form.Item>
          <Form.Item name="phone" label="电话">
            <Input />
          </Form.Item>
          <Form.Item name="email" label="邮箱">
            <Input />
          </Form.Item>
          <Form.Item name="is_primary" label="设为主联系人" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="notes" label="备注">
            <TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </PageScaffold>
  );
};

export default ChannelFullViewPage;
