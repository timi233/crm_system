import React, { useState } from 'react';
import { Card, Row, Col, Statistic, List, Button, Space, Progress, Tag, Spin, Skeleton, Typography, Drawer, Tooltip, Form, Input, Select, DatePicker, Cascader, InputNumber, Checkbox, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import {
  UserOutlined,
  TeamOutlined,
  DollarOutlined,
  BellOutlined,
  PlusOutlined,
  PhoneOutlined,
  FundProjectionScreenOutlined,
  TrophyOutlined,
  RightOutlined,
  BulbOutlined,
  BarChartOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  ToolOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { useSelector } from 'react-redux';
import { RootState } from '../store/store';
import {
  useDashboardSummary,
  useDashboardTodos,
  useDashboardRecentFollowups,
  useDashboardNotifications,
  useMarkNotificationsRead,
  useTeamRank,
  DashboardNotificationItem,
} from '../hooks/useDashboard';
import { useAlerts, AlertItem } from '../hooks/useAlerts';
import { useCreateCustomer } from '../hooks/useCustomers';
import { useCreateLead, LeadCreate } from '../hooks/useLeads';
import { useCreateOpportunity } from '../hooks/useOpportunities';
import { useCreateFollowUp } from '../hooks/useFollowUps';
import { useDictItems, useRegionCascader } from '../hooks/useDictItems';
import { useUsers } from '../hooks/useUsers';
import { useChannels } from '../hooks/useChannels';
import { useCustomers } from '../hooks/useCustomers';
import { useProjects } from '../hooks/useProjects';
import FollowUpModal from '../components/modals/FollowUpModal';

const ENTITY_ROUTE_MAP: Record<string, string> = {
  lead: 'leads',
  opportunity: 'opportunities',
  project: 'projects',
  customer: 'customers',
  contract: 'contracts',
  work_order: 'work-orders',
};

const getEntityRoute = (entityType: string): string => {
  return ENTITY_ROUTE_MAP[entityType] || entityType;
};

const { Title, Text } = Typography;

const MyDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useSelector((state: RootState) => state.auth);
  const isManager = user?.role === 'admin';
  const [notificationsModalVisible, setNotificationsModalVisible] = useState(false);
  const [alertsModalVisible, setAlertsModalVisible] = useState(false);
  const [isCustomerDrawerVisible, setIsCustomerDrawerVisible] = useState(false);
  const [isLeadDrawerVisible, setIsLeadDrawerVisible] = useState(false);
  const [isOpportunityDrawerVisible, setIsOpportunityDrawerVisible] = useState(false);
  const [isFollowUpDrawerVisible, setIsFollowUpDrawerVisible] = useState(false);

  const [customerForm] = Form.useForm();
  const [leadForm] = Form.useForm();
  const [opportunityForm] = Form.useForm();

  const { data: summary, isLoading: summaryLoading } = useDashboardSummary();
  const { data: todos, isLoading: todosLoading } = useDashboardTodos();
  const { data: followups, isLoading: followupsLoading } = useDashboardRecentFollowups(5);
  const { data: notifications, isLoading: notificationsLoading } = useDashboardNotifications();
  const { data: alerts, isLoading: alertsLoading } = useAlerts();
  const { data: teamRank } = useTeamRank(5, isManager);
  const markReadMutation = useMarkNotificationsRead();

  const { data: regionOptions = [] } = useRegionCascader();
  const { data: industryItems = [] } = useDictItems('行业');
  const { data: statusItems = [] } = useDictItems('客户状态');
  const { data: sourceItems = [] } = useDictItems('商机来源');
  const { data: productItems = [] } = useDictItems('产品品牌');
  const { data: methodItems = [] } = useDictItems('跟进方式');
  const { data: conclusionItems = [] } = useDictItems('跟进结论');
  const { data: users = [] } = useUsers();
  const { data: channels = [] } = useChannels();
  const { data: customers = [] } = useCustomers();
  const { data: projects = [] } = useProjects();

  const createCustomerMutation = useCreateCustomer();
  const createLeadMutation = useCreateLead();
  const createOpportunityMutation = useCreateOpportunity();
  const createFollowUpMutation = useCreateFollowUp();

  if (summaryLoading) {
    return (
      <div style={{ padding: 24 }}>
        <Skeleton active paragraph={{ rows: 8 }} />
      </div>
    );
  }

  const funnelOption = {
    tooltip: { trigger: 'item', formatter: '{b}: {c}' },
    series: [{
      type: 'funnel',
      left: '10%',
      top: 10,
      bottom: 10,
      width: '80%',
      min: 0,
      max: 100,
      minSize: '20%',
      maxSize: '100%',
      sort: 'none',
      gap: 2,
      label: { show: true, position: 'inside', fontSize: 12 },
      itemStyle: { borderColor: '#fff', borderWidth: 1 },
      data: [
        { value: summary?.leads_count || 0, name: '线索' },
        { value: summary?.opportunities_count || 0, name: '商机' },
        { value: summary?.projects_count || 0, name: '项目' },
        { value: summary?.contracts_count || 0, name: '合同' },
      ],
    }],
  };

  const handleOpenNotificationsModal = () => {
    setNotificationsModalVisible(true);
    const unreadNotifications = (notifications || [])
      .filter(n => !n.is_read && n.entity_type && n.entity_id)
      .map(n => ({ entity_type: n.entity_type as string, entity_id: n.entity_id as number, type: n.type }));
    if (unreadNotifications.length > 0) {
      markReadMutation.mutate(unreadNotifications);
    }
  };

  const handleCustomerSubmit = async (values: any) => {
    try {
      const payload = {
        ...values,
        customer_region: values.customer_region?.join?.('/') || '',
        maintenance_expiry: values.maintenance_expiry?.format?.('YYYY-MM-DD'),
      };
      await createCustomerMutation.mutateAsync(payload);
      message.success('客户创建成功');
      customerForm.resetFields();
      setIsCustomerDrawerVisible(false);
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  const handleLeadSubmit = async (values: any) => {
    try {
      const payload: LeadCreate = values;
      await createLeadMutation.mutateAsync(payload);
      message.success('线索创建成功');
      leadForm.resetFields();
      setIsLeadDrawerVisible(false);
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  const handleOpportunitySubmit = async (values: any) => {
    try {
      const payload = {
        ...values,
        expected_close_date: values.expected_close_date?.format?.('YYYY-MM-DD'),
      };
      await createOpportunityMutation.mutateAsync(payload);
      message.success('商机创建成功');
      opportunityForm.resetFields();
      setIsOpportunityDrawerVisible(false);
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  const handleNotificationClick = (item: DashboardNotificationItem) => {
    if (item.entity_type && item.entity_id) {
      setNotificationsModalVisible(false);
      navigate(`/${getEntityRoute(item.entity_type)}/${item.entity_id}/full`);
    }
  };

  const renderNotificationContent = (item: DashboardNotificationItem) => {
    if (!item.entity_type || !item.entity_code) {
      return <span>{item.content}</span>;
    }
    const parts = item.content.split(item.entity_code);
    return (
      <span>
        {parts[0]}
        <a onClick={(e) => { e.stopPropagation(); handleNotificationClick(item); }} style={{ color: '#1890ff' }}>
          {item.entity_code}
        </a>
        {parts[1]}
      </span>
    );
  };

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      '高': 'red',
      '中': 'orange',
      '低': 'blue',
    };
    return colors[priority] || 'default';
  };

  return (
    <div style={{ padding: 24 }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Title level={4} style={{ margin: 0 }}>
          我的工作台
        </Title>
        <Text type="secondary">
          欢迎，{user?.name} ({user?.role === 'admin' ? '管理员' : '销售'})
        </Text>
      </Row>

      <Card title="业绩目标" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Tooltip title="同比上月">
              <Statistic
                title="季度目标"
                value={summary?.quarterly_target || 0}
                valueStyle={{ color: summary?.quarterly_target && summary?.quarterly_target_prev ? (summary.quarterly_target > summary.quarterly_target_prev ? '#3f8600' : '#cf1322') : '' }}
                prefix={<DollarOutlined />}
                suffix={summary?.quarterly_target && summary?.quarterly_target_prev ? (
                  summary.quarterly_target > summary.quarterly_target_prev ? <ArrowUpOutlined /> : <ArrowDownOutlined />
                ) : ''}
                precision={0}
              />
            </Tooltip>
          </Col>
          <Col span={6}>
            <Tooltip title="完成率对比">
              <Statistic
                title="季度完成"
                value={summary?.quarterly_achieved || 0}
                prefix={<DollarOutlined />}
                precision={0}
                valueStyle={{
                  color: (summary?.quarterly_achieved || 0) >= (summary?.quarterly_target || 0) ? '#3f8600' : '#cf1322'
                }}
                suffix={summary?.quarterly_achieved && summary?.quarterly_achieved_prev ? (
                  summary.quarterly_achieved > summary.quarterly_achieved_prev ? <ArrowUpOutlined /> : <ArrowDownOutlined />
                ) : ''}
              />
            </Tooltip>
          </Col>
          <Col span={6}>
            <Tooltip title="本月目标">
              <Statistic
                title="本月目标"
                value={summary?.monthly_target || 0}
                prefix={<DollarOutlined />}
                precision={0}
                valueStyle={{ color: summary?.monthly_target && summary?.monthly_target_prev ? (summary.monthly_target > summary.monthly_target_prev ? '#3f8600' : '#cf1322') : '' }}
                suffix={summary?.monthly_target && summary?.monthly_target_prev ? (
                  summary.monthly_target > summary.monthly_target_prev ? <ArrowUpOutlined /> : <ArrowDownOutlined />
                ) : ''}
              />
            </Tooltip>
          </Col>
          <Col span={6}>
            <Tooltip title="本月完成">
              <Statistic
                title="本月完成"
                value={summary?.monthly_achieved || 0}
                prefix={<DollarOutlined />}
                precision={0}
                valueStyle={{
                  color: (summary?.monthly_achieved || 0) >= (summary?.monthly_target || 0) ? '#3f8600' : '#cf1322'
                }}
                suffix={summary?.monthly_achieved && summary?.monthly_achieved_prev ? (
                  summary.monthly_achieved > summary.monthly_achieved_prev ? <ArrowUpOutlined /> : <ArrowDownOutlined />
                ) : ''}
              />
            </Tooltip>
          </Col>
        </Row>
      </Card>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={4}>
          <Card hoverable onClick={() => navigate('/leads')}>
            <Tooltip title={summary?.leads_count && summary?.leads_count_prev ? `上月线索 ${summary.leads_count_prev || 0}` : ''}>
              <Statistic
                title={isManager ? '团队线索' : '我的线索'}
                value={summary?.leads_count || 0}
                prefix={<UserOutlined />}
                suffix={summary?.leads_count && summary?.leads_count_prev ? (
                  summary.leads_count > summary.leads_count_prev ? <ArrowUpOutlined /> : <ArrowDownOutlined />
                ) : ''}
              />
            </Tooltip>
          </Card>
        </Col>
        <Col span={4}>
          <Card hoverable onClick={() => navigate('/opportunities')}>
            <Tooltip title={summary?.opportunities_count && summary?.opportunities_count_prev ? `上月商机 ${summary.opportunities_count_prev || 0}` : ''}>
              <Statistic
                title={isManager ? '团队商机' : '我的商机'}
                value={summary?.opportunities_count || 0}
                prefix={<TeamOutlined />}
                suffix={summary?.opportunities_count && summary?.opportunities_count_prev ? (
                  summary.opportunities_count > summary.opportunities_count_prev ? <ArrowUpOutlined /> : <ArrowDownOutlined />
                ) : ''}
              />
            </Tooltip>
          </Card>
        </Col>
        <Col span={4}>
          <Card hoverable onClick={() => navigate('/follow-ups')}>
            <Statistic
              title="待跟进"
              value={summary?.pending_followups || 0}
              prefix={<PhoneOutlined />}
              valueStyle={{ color: (summary?.pending_followups || 0) > 5 ? '#cf1322' : '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card hoverable onClick={() => setAlertsModalVisible(true)}>
            <Statistic
              title="预警中心"
              value={summary?.alerts_count || 0}
              prefix={<BellOutlined />}
              valueStyle={{ color: (summary?.alerts_count || 0) > 0 ? '#cf1322' : '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card hoverable onClick={() => navigate('/opportunities')}>
            <Statistic
              title="本季度预计下单"
              value={summary?.quarterly_forecast_amount || 0}
              prefix={<DollarOutlined />}
              precision={0}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={16}>
          <Card title="今日待办" extra={<a onClick={() => navigate('/follow-ups')}>查看全部</a>} style={{ marginBottom: 16 }}>
            <List
              loading={todosLoading}
              dataSource={todos?.slice(0, 5) || []}
              renderItem={(item) => (
                <List.Item
                  actions={[<Tag color={getPriorityColor(item.priority)}>{item.priority}</Tag>]}
                  onClick={() => navigate(`/${getEntityRoute(item.entity_type || '')}/${item.entity_id}/full`)}
                  style={{ cursor: 'pointer' }}
                >
                  <List.Item.Meta
                    title={<><Tag color="blue">{item.type}</Tag>{item.title}</>}
                    description={item.customer_name}
                  />
                  <Text type="secondary">{item.due_date}</Text>
                </List.Item>
              )}
              locale={{ emptyText: '暂无待办事项' }}
            />
          </Card>

          <Card title="最近跟进记录" extra={<a onClick={() => navigate('/follow-ups')}>查看全部</a>}>
            <List
              loading={followupsLoading}
              dataSource={followups || []}
              renderItem={(item) => (
                <List.Item
                  onClick={() => navigate(`/${getEntityRoute(item.entity_type || '')}/${item.entity_id}/full`)}
                  style={{ cursor: 'pointer' }}
                >
                  <List.Item.Meta
                    title={item.customer_name}
                    description={`${item.follow_up_method} - ${item.follow_up_content}`}
                  />
                  <Text type="secondary">{item.follow_up_date}</Text>
                </List.Item>
              )}
              locale={{ emptyText: '暂无跟进记录' }}
            />
          </Card>
        </Col>

        <Col span={8}>
          <Card title="快捷入口" style={{ marginBottom: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Row gutter={8}>
                <Col span={12}>
                  <Button type="primary" icon={<PlusOutlined />} block onClick={() => setIsCustomerDrawerVisible(true)}>
                    新建客户
                  </Button>
                </Col>
                <Col span={12}>
                  <Button icon={<PlusOutlined />} block onClick={() => setIsLeadDrawerVisible(true)}>
                    新建线索
                  </Button>
                </Col>
              </Row>
              <Row gutter={8}>
                <Col span={12}>
                  <Button icon={<PlusOutlined />} block onClick={() => setIsOpportunityDrawerVisible(true)}>
                    新建商机
                  </Button>
                </Col>
                <Col span={12}>
                  <Button icon={<PlusOutlined />} block onClick={() => setIsFollowUpDrawerVisible(true)}>
                    添加跟进
                  </Button>
                </Col>
              </Row>
              <Row gutter={8}>
                <Col span={12}>
                  <Button icon={<BarChartOutlined />} block onClick={() => navigate('/reports/sales-funnel')}>
                    报表统计
                  </Button>
                </Col>
                <Col span={12}>
                  <Button icon={<ToolOutlined />} block onClick={() => navigate('/work-orders')}>
                    工单管理
                  </Button>
                </Col>
              </Row>
            </Space>
          </Card>

          <Card title="销售漏斗速览" style={{ marginBottom: 16 }}>
            <ReactECharts option={funnelOption} style={{ height: 200 }} />
          </Card>

          <Card title="通知中心" extra={<a onClick={handleOpenNotificationsModal}>查看全部</a>}>
            <List
              loading={notificationsLoading}
              dataSource={notifications?.slice(0, 3) || []}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    title={<><Tag color={item.is_read ? 'default' : 'green'}>{item.type}</Tag>{item.title}</>}
                    description={renderNotificationContent(item)}
                  />
                </List.Item>
              )}
              locale={{ emptyText: '暂无通知' }}
            />
          </Card>

          {isManager && (
            <Card title="团队排行榜" extra={<a onClick={() => navigate('/reports/performance')}>查看详情</a>} style={{ marginTop: 16 }}>
              <List
                size="small"
                dataSource={teamRank || []}
                renderItem={(item) => (
                  <List.Item>
                    <Space>
                      <TrophyOutlined style={{ color: item.rank === 1 ? '#faad14' : '#8c8c8c' }} />
                      <Text strong={item.rank === 1}>{item.rank}. {item.user_name}</Text>
                      <Text type="secondary">¥{item.amount?.toLocaleString() || 0}</Text>
                    </Space>
                  </List.Item>
                )}
                locale={{ emptyText: '暂无数据' }}
              />
            </Card>
          )}
        </Col>
      </Row>

      <Drawer
        title="通知中心"
        open={notificationsModalVisible}
        onClose={() => setNotificationsModalVisible(false)}
        width={480}
        maskClosable={false}
      >
        <List
          loading={notificationsLoading}
          dataSource={notifications || []}
          renderItem={(item) => (
            <List.Item
              style={{ cursor: item.entity_type ? 'pointer' : 'default', opacity: item.is_read ? 0.7 : 1 }}
              onClick={() => handleNotificationClick(item)}
            >
              <List.Item.Meta
                title={<><Tag color={item.is_read ? 'default' : 'green'}>{item.type}</Tag>{item.title}</>}
                description={renderNotificationContent(item)}
              />
              <Text type="secondary">{item.created_at?.split('T')[0] || ''}</Text>
            </List.Item>
          )}
          locale={{ emptyText: '暂无通知' }}
        />
      </Drawer>

      <Drawer
        title={<><BellOutlined /> 预警中心</>}
        open={alertsModalVisible}
        onClose={() => setAlertsModalVisible(false)}
        width={520}
        maskClosable={false}
      >
        <List
          loading={alertsLoading}
          dataSource={alerts || []}
          renderItem={(item: AlertItem) => (
            <List.Item
              style={{ cursor: item.entity_type ? 'pointer' : 'default' }}
              onClick={() => {
                if (item.entity_type && item.entity_id) {
                  setAlertsModalVisible(false);
                  navigate(`/${getEntityRoute(item.entity_type)}/${item.entity_id}/full`);
                }
              }}
            >
              <List.Item.Meta
                title={
                  <>
                    <Tag color={
                      item.priority === 'high' ? 'red' :
                      item.priority === 'medium' ? 'orange' : 'blue'
                    }>
                      {item.priority === 'high' ? '高' : item.priority === 'medium' ? '中' : '低'}
                    </Tag>
                    <Tag>{item.alert_type}</Tag>
                    {item.title}
                  </>
                }
                description={item.content}
              />
              <Text type="secondary">{item.created_at?.split('T')[0] || ''}</Text>
            </List.Item>
          )}
          locale={{ emptyText: '暂无预警' }}
        />
      </Drawer>

      <Drawer
        title="新建客户"
        open={isCustomerDrawerVisible}
        onClose={() => {
          customerForm.resetFields();
          setIsCustomerDrawerVisible(false);
        }}
        width={520}
        maskClosable={false}
        destroyOnClose
      >
        <Form
          form={customerForm}
          layout="vertical"
          onFinish={handleCustomerSubmit}
          disabled={createCustomerMutation.isPending}
        >
          <Form.Item
            label="客户名称"
            name="customer_name"
            rules={[{ required: true, message: '请输入客户名称' }]}
          >
            <Input placeholder="请输入客户全称" />
          </Form.Item>

          <Form.Item
            label="统一社会信用代码"
            name="credit_code"
            rules={[{ required: true, message: '请输入统一社会信用代码' }, { len: 18, message: '统一社会信用代码应为 18 位' }]}
          >
            <Input placeholder="18 位统一社会信用代码" maxLength={18} />
          </Form.Item>

          <Form.Item
            label="客户行业"
            name="customer_industry"
            rules={[{ required: true, message: '请选择客户行业' }]}
          >
            <Select placeholder="请选择客户所属行业" showSearch>
              {industryItems.map(item => (
                <Select.Option key={item.id} value={item.name}>{item.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            label="客户区域"
            name="customer_region"
            rules={[{ required: true, message: '请选择客户所在区域' }]}
          >
            <Cascader
              options={regionOptions}
              placeholder="请选择省/市"
              showSearch
            />
          </Form.Item>

          <Form.Item
            label="客户负责人"
            name="customer_owner_id"
            rules={[{ required: true, message: '请选择客户负责人' }]}
          >
            <Select placeholder="选择负责跟进此客户的销售" showSearch optionFilterProp="children">
              {users.map(u => (
                <Select.Option key={u.id} value={u.id}>{u.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item label="关联渠道" name="channel_id">
            <Select placeholder="请选择渠道 (可选)" showSearch optionFilterProp="children" allowClear>
              {channels.map(ch => (
                <Select.Option key={ch.id} value={ch.id}>{ch.company_name}</Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item label="主要联系人" name="main_contact">
            <Input placeholder="客户侧主要对接人姓名" />
          </Form.Item>

          <Form.Item label="联系电话" name="phone">
            <Input placeholder="联系电话" />
          </Form.Item>

          <Form.Item
            label="客户状态"
            name="customer_status"
            rules={[{ required: true, message: '请选择客户状态' }]}
          >
            <Select placeholder="客户当前状态">
              {statusItems.map(item => (
                <Select.Option key={item.id} value={item.name}>{item.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item label="维保到期时间" name="maintenance_expiry">
            <DatePicker placeholder="选择维保合同到期日" style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item label="备注" name="notes">
            <Input.TextArea rows={4} placeholder="其他备注信息" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={createCustomerMutation.isPending} block>
              保存
            </Button>
          </Form.Item>
        </Form>
      </Drawer>

      <Drawer
        title="新建线索"
        open={isLeadDrawerVisible}
        onClose={() => {
          leadForm.resetFields();
          setIsLeadDrawerVisible(false);
        }}
        width={520}
        maskClosable={false}
        destroyOnClose
      >
        <Form
          form={leadForm}
          layout="vertical"
          onFinish={handleLeadSubmit}
          disabled={createLeadMutation.isPending}
        >
          <Form.Item
            name="lead_name"
            label="线索名称"
            rules={[{ required: true, message: '请输入线索名称' }]}
          >
            <Input placeholder="请输入线索名称" />
          </Form.Item>

          <Form.Item
            name="terminal_customer_id"
            label="终端客户"
            rules={[{ required: true, message: '请选择终端客户' }]}
          >
            <Select placeholder="请选择终端客户" showSearch optionFilterProp="children">
              {customers.map(c => (
                <Select.Option key={c.id} value={c.id}>{c.customer_name}</Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="sales_owner_id"
            label="销售负责人"
            rules={[{ required: true, message: '请选择销售负责人' }]}
          >
            <Select placeholder="请选择销售负责人" showSearch optionFilterProp="children">
              {users.map(u => (
                <Select.Option key={u.id} value={u.id}>{u.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="lead_stage"
            label="线索阶段"
            rules={[{ required: true, message: '请选择线索阶段' }]}
            initialValue="初步接触"
          >
            <Select placeholder="请选择线索阶段">
              <Select.Option value="初步接触">初步接触</Select.Option>
              <Select.Option value="意向沟通">意向沟通</Select.Option>
              <Select.Option value="需求挖掘中">需求挖掘中</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item name="lead_source" label="线索来源">
            <Select placeholder="请选择线索来源" allowClear>
              {sourceItems.map(item => (
                <Select.Option key={item.id} value={item.name}>{item.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="source_channel_id" label="来源渠道" tooltip="归因渠道，创建后原则上不可修改">
            <Select placeholder="请选择来源渠道" allowClear showSearch optionFilterProp="label">
              {channels.map(ch => (
                <Select.Option key={ch.id} value={ch.id}>{ch.company_name}</Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="channel_id" label="协同渠道" tooltip="当前协同渠道，可随时修改">
            <Select placeholder="请选择协同渠道" allowClear showSearch optionFilterProp="label">
              {channels.map(ch => (
                <Select.Option key={ch.id} value={ch.id}>{ch.company_name}</Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="products" label="产品">
            <Select mode="multiple" placeholder="请选择产品（可多选）" allowClear>
              {productItems.map(item => (
                <Select.Option key={item.id} value={item.name}>{item.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="contact_person" label="联系人">
            <Input placeholder="联系人姓名" />
          </Form.Item>

          <Form.Item name="contact_phone" label="联系电话">
            <Input placeholder="联系电话" />
          </Form.Item>

          <Form.Item name="estimated_budget" label="预估预算">
            <InputNumber placeholder="请输入预估预算" style={{ width: '100%' }} min={0} precision={2} />
          </Form.Item>

          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={3} placeholder="请输入备注信息" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={createLeadMutation.isPending} block>
              保存
            </Button>
          </Form.Item>
        </Form>
      </Drawer>

      <Drawer
        title="新建商机"
        open={isOpportunityDrawerVisible}
        onClose={() => {
          opportunityForm.resetFields();
          setIsOpportunityDrawerVisible(false);
        }}
        width={520}
        maskClosable={false}
        destroyOnClose
      >
        <Form
          form={opportunityForm}
          layout="vertical"
          onFinish={handleOpportunitySubmit}
          disabled={createOpportunityMutation.isPending}
        >
          <Form.Item
            name="opportunity_name"
            label="商机名称"
            rules={[{ required: true, message: '请输入商机名称' }]}
          >
            <Input placeholder="请输入商机名称" />
          </Form.Item>

          <Form.Item
            name="terminal_customer_id"
            label="终端客户"
            rules={[{ required: true, message: '请选择终端客户' }]}
          >
            <Select placeholder="请选择终端客户" showSearch optionFilterProp="children">
              {customers.map(c => (
                <Select.Option key={c.id} value={c.id}>{c.customer_name}</Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="sales_owner_id"
            label="销售负责人"
            rules={[{ required: true, message: '请选择销售负责人' }]}
          >
            <Select placeholder="请选择销售负责人" showSearch optionFilterProp="children">
              {users.map(u => (
                <Select.Option key={u.id} value={u.id}>{u.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="opportunity_stage"
            label="商机阶段"
            rules={[{ required: true, message: '请选择商机阶段' }]}
            initialValue="需求方案"
          >
            <Select placeholder="请选择商机阶段">
              <Select.Option value="需求方案">需求方案</Select.Option>
              <Select.Option value="方案评审">方案评审</Select.Option>
              <Select.Option value="报价/谈判">报价/谈判</Select.Option>
              <Select.Option value="赢单">赢单</Select.Option>
              <Select.Option value="输单">输单</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="opportunity_source"
            label="商机来源"
            rules={[{ required: true, message: '请选择商机来源' }]}
          >
            <Select placeholder="请选择商机来源">
              {sourceItems.map(item => (
                <Select.Option key={item.id} value={item.name}>{item.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="products" label="产品">
            <Select mode="multiple" placeholder="请选择产品（可多选）" allowClear>
              {productItems.map(item => (
                <Select.Option key={item.id} value={item.name}>{item.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="expected_contract_amount"
            label="预计合同金额"
            rules={[{ required: true, message: '请输入预计合同金额' }]}
          >
            <InputNumber placeholder="请输入预计合同金额" style={{ width: '100%' }} min={0} precision={2} />
          </Form.Item>

          <Form.Item name="expected_close_date" label="预计关闭日期">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="channel_id" label="关联渠道">
            <Select placeholder="请选择渠道 (可选)" showSearch optionFilterProp="children" allowClear>
              {channels.map(ch => (
                <Select.Option key={ch.id} value={ch.id}>{ch.company_name}</Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={3} placeholder="请输入备注信息" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={createOpportunityMutation.isPending} block>
              保存
            </Button>
          </Form.Item>
        </Form>
      </Drawer>

      <FollowUpModal
        visible={isFollowUpDrawerVisible}
        onClose={() => {
          setIsFollowUpDrawerVisible(false);
        }}
      />
    </div>
  );
};

export default MyDashboard;