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
    <Card
      title={
        <Space>
          <BellOutlined />
          通知中心
          <Badge count={unreadCount?.count || 0} showZero={false} />
        </Space>
      }
      extra={
        <Space>
          <Select
            value={filter}
            onChange={(v) => setFilter(v)}
            style={{ width: 120 }}
            options={[
              { value: 'all', label: '全部' },
              { value: 'unread', label: '未读' },
            ]}
          />
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
    >
      {isLoading ? (
        <Spin size="large" style={{ display: 'block', margin: '60px auto' }} />
      ) : items.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: '#999' }}>
          暂无通知
        </div>
      ) : (
        <List
          dataSource={items}
          renderItem={(n) => (
            <List.Item
              style={{
                cursor: 'pointer',
                background: n.is_read ? 'transparent' : '#f0f7ff',
                padding: '12px 16px',
              }}
              onClick={() => handleNotificationClick(n)}
            >
              <List.Item.Meta
                avatar={
                  n.is_read ? (
                    <CheckOutlined style={{ color: '#52c41a' }} />
                  ) : (
                    <Badge dot>
                      <BellOutlined style={{ color: '#1890ff' }} />
                    </Badge>
                  )
                }
                title={
                  <Space>
                    <Text strong={!n.is_read}>{n.title}</Text>
                    <Tag color={n.is_read ? 'default' : 'blue'}>
                      {TYPE_LABELS[n.notification_type] || n.notification_type}
                    </Tag>
                  </Space>
                }
                description={
                  <Space direction="vertical" size={0}>
                    <Text type="secondary">{n.content}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {dayjs(n.created_at).fromNow()}
                    </Text>
                  </Space>
                }
              />
            </List.Item>
          )}
        />
      )}
    </Card>
  );
};

export default NotificationCenterPage;
