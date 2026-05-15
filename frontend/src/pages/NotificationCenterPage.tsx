import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  List,
  Button,
  Space,
  Tag,
  Select,
  Badge,
  Spin,
  Typography,
  message,
} from 'antd';
import {
  BellOutlined,
  CheckOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import {
  useNotifications,
  useUnreadCount,
  useMarkNotificationRead,
  useMarkAllRead,
} from '../hooks/useNotifications';
import PageScaffold from '../components/common/PageScaffold';
import { ClockCircleOutlined } from '@ant-design/icons';
import { Empty } from 'antd';

dayjs.extend(relativeTime);

const { Text } = Typography;

const TYPE_LABELS: Record<string, string> = {
  handover_pending: '离职交接',
  work_report_comment: '日报评论',
  system: '系统通知',
};

const ENTITY_ROUTE_MAP: Record<string, (id: number) => string> = {
  work_report: (id: number) => `/work-reports/${id}`,
  handover_request: (id: number) => `/handovers/${id}`,
  work_order: (id: number) => `/work-orders/${id}`,
};

const NotificationCenterPage: React.FC = () => {
  const navigate = useNavigate();
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  const { data: notifications, isLoading } = useNotifications(
    filter === 'unread' ? { is_read: false, limit: 100 } : { limit: 100 }
  );
  const { data: unreadCount } = useUnreadCount();

  const markReadMutation = useMarkNotificationRead();
  const markAllMutation = useMarkAllRead();

  const handleNotificationClick = async (n: typeof notifications extends { items: (infer T)[] } ? T : never) => {
    if (!n.is_read) {
      markReadMutation.mutate(n.id);
    }
    const routeFn = ENTITY_ROUTE_MAP[n.entity_type || ''];
    if (routeFn && n.entity_id) {
      navigate(routeFn(n.entity_id));
    } else if (!n.is_read) {
      message.success('已标记为已读');
    }
  };

  const handleMarkAllRead = () => {
    markAllMutation.mutate(undefined, {
      onSuccess: () => message.success('已全部标记为已读'),
    });
  };

  const items = notifications?.items || [];

  return (
    <PageScaffold
      title="通知中心"
      breadcrumbItems={[{ title: '首页', href: '/dashboard' }, { title: '通知中心' }]}
      extra={
        <Space>
          <Button
            icon={<CheckCircleOutlined />}
            onClick={handleMarkAllRead}
            loading={markAllMutation.isPending}
            disabled={items.length === 0}
          >
            全部已读
          </Button>
        </Space>
      }
      filters={
        <Space size={12}>
          <Select
            value={filter}
            onChange={(v) => setFilter(v)}
            style={{ width: 150 }}
            options={[
              { value: 'all', label: '显示全部通知' },
              { value: 'unread', label: '仅显示未读' },
            ]}
          />
        </Space>
      }
    >
      {isLoading ? (
        <Spin size="large" style={{ display: 'block', margin: '60px auto' }} />
      ) : items.length === 0 ? (
        <div style={{ padding: '60px 0' }}>
          <Empty description="暂无通知" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        </div>
      ) : (
        <List
          dataSource={items}
          renderItem={(n) => (
            <List.Item
              style={{
                cursor: 'pointer',
                background: n.is_read ? 'transparent' : '#f0f7ff',
                padding: '20px 24px',
                borderBottom: '1px solid #f1f5f9',
                transition: 'all 0.2s',
              }}
              onClick={() => handleNotificationClick(n)}
              className="list-item-hover"
            >
              <List.Item.Meta
                avatar={
                  <div style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '10px',
                    background: n.is_read ? '#f8fafc' : '#e0e7ff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '18px'
                  }}>
                    {n.is_read ? (
                      <CheckOutlined style={{ color: '#94a3b8' }} />
                    ) : (
                      <BellOutlined style={{ color: '#4338ca' }} />
                    )}
                  </div>
                }
                title={
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <Text strong={!n.is_read} style={{ fontSize: '15px', color: n.is_read ? '#64748b' : '#1e293b' }}>{n.title}</Text>
                    <Tag color={n.is_read ? 'default' : 'blue'} style={{ border: 'none', background: n.is_read ? '#f1f5f9' : '#e0e7ff', color: n.is_read ? '#94a3b8' : '#4338ca', fontSize: '11px', fontWeight: 700 }}>
                      {TYPE_LABELS[n.notification_type] || n.notification_type}
                    </Tag>
                  </div>
                }
                description={
                  <div style={{ marginTop: '4px' }}>
                    <div style={{ color: '#64748b', fontSize: '13px', marginBottom: '4px' }}>{n.content}</div>
                    <div style={{ color: '#94a3b8', fontSize: '12px' }}>
                      <ClockCircleOutlined style={{ marginRight: '4px' }} />
                      {dayjs(n.created_at).fromNow()}
                    </div>
                  </div>
                }
              />
            </List.Item>
          )}
        />
      )}
    </PageScaffold>
  );
};

export default NotificationCenterPage;
