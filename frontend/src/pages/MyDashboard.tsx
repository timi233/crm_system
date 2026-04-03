import React, { useState } from 'react';
import { Card, Row, Col, Statistic, List, Button, Space, Progress, Tag, Spin, Typography, Modal } from 'antd';
import { useNavigate } from 'react-router-dom';
import {
  UserOutlined,
  TeamOutlined,
  FileDoneOutlined,
  DollarOutlined,
  BellOutlined,
  PlusOutlined,
  PhoneOutlined,
  FundProjectionScreenOutlined,
  TrophyOutlined,
  RightOutlined,
  BulbOutlined,
  BarChartOutlined,
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

const { Title, Text } = Typography;

const MyDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useSelector((state: RootState) => state.auth);
  const isManager = user?.role === 'admin';
  const [notificationsModalVisible, setNotificationsModalVisible] = useState(false);
  const [alertsModalVisible, setAlertsModalVisible] = useState(false);

  const { data: summary, isLoading: summaryLoading } = useDashboardSummary();
  const { data: todos, isLoading: todosLoading } = useDashboardTodos();
  const { data: followups, isLoading: followupsLoading } = useDashboardRecentFollowups(5);
  const { data: notifications, isLoading: notificationsLoading } = useDashboardNotifications();
  const { data: alerts, isLoading: alertsLoading } = useAlerts();
  const { data: teamRank } = useTeamRank(5);
  const markReadMutation = useMarkNotificationsRead();

  if (summaryLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <Spin size="large" />
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
      .map(n => ({ entity_type: n.entity_type!, entity_id: n.entity_id!, type: n.type }));
    if (unreadNotifications.length > 0) {
      markReadMutation.mutate(unreadNotifications);
    }
  };

  const handleNotificationClick = (item: DashboardNotificationItem) => {
    if (item.entity_type && item.entity_id) {
      setNotificationsModalVisible(false);
      navigate(`/${item.entity_type}/${item.entity_id}/full`);
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
            <Statistic
              title="季度目标"
              value={summary?.quarterly_target || 0}
              prefix={<DollarOutlined />}
              precision={0}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="季度完成"
              value={summary?.quarterly_achieved || 0}
              prefix={<DollarOutlined />}
              precision={0}
              valueStyle={{
                color: (summary?.quarterly_achieved || 0) >= (summary?.quarterly_target || 0) ? '#3f8600' : '#cf1322'
              }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="本月目标"
              value={summary?.monthly_target || 0}
              prefix={<DollarOutlined />}
              precision={0}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="本月完成"
              value={summary?.monthly_achieved || 0}
              prefix={<DollarOutlined />}
              precision={0}
              valueStyle={{
                color: (summary?.monthly_achieved || 0) >= (summary?.monthly_target || 0) ? '#3f8600' : '#cf1322'
              }}
            />
          </Col>
        </Row>
      </Card>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={4}>
          <Card hoverable onClick={() => navigate('/leads')}>
            <Statistic
              title={isManager ? '团队线索' : '我的线索'}
              value={summary?.leads_count || 0}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card hoverable onClick={() => navigate('/opportunities')}>
            <Statistic
              title={isManager ? '团队商机' : '我的商机'}
              value={summary?.opportunities_count || 0}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card hoverable onClick={() => navigate('/contracts')}>
            <Statistic
              title={isManager ? '团队合同' : '我的合同'}
              value={summary?.contracts_count || 0}
              prefix={<FileDoneOutlined />}
            />
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
                  onClick={() => navigate(`/${item.entity_type}s/${item.entity_id}/full`)}
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
                  onClick={() => navigate(`/${item.entity_type}s/${item.entity_id}/full`)}
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
                  <Button type="primary" icon={<PlusOutlined />} block onClick={() => navigate('/customers/new')}>
                    新建客户
                  </Button>
                </Col>
                <Col span={12}>
                  <Button icon={<PlusOutlined />} block onClick={() => navigate('/leads/new')}>
                    新建线索
                  </Button>
                </Col>
              </Row>
              <Row gutter={8}>
                <Col span={12}>
                  <Button icon={<PlusOutlined />} block onClick={() => navigate('/opportunities/new')}>
                    新建商机
                  </Button>
                </Col>
                <Col span={12}>
                  <Button icon={<PlusOutlined />} block onClick={() => navigate('/contracts/new')}>
                    新建合同
                  </Button>
                </Col>
              </Row>
              <Row gutter={8}>
                <Col span={12}>
                  <Button icon={<PlusOutlined />} block onClick={() => navigate('/follow-ups/new')}>
                    添加跟进
                  </Button>
                </Col>
                <Col span={12}>
                  <Button icon={<BarChartOutlined />} block onClick={() => navigate('/reports/sales-funnel')}>
                    报表统计
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

      <Modal
        title="通知中心"
        open={notificationsModalVisible}
        onCancel={() => setNotificationsModalVisible(false)}
        footer={<Button onClick={() => setNotificationsModalVisible(false)}>关闭</Button>}
        width={600}
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
      </Modal>

      <Modal
        title={<><BellOutlined /> 预警中心</>}
        open={alertsModalVisible}
        onCancel={() => setAlertsModalVisible(false)}
        footer={<Button onClick={() => setAlertsModalVisible(false)}>关闭</Button>}
        width={700}
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
                  navigate(`/${item.entity_type}/${item.entity_id}/full`);
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
      </Modal>
    </div>
  );
};

export default MyDashboard;