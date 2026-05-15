import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  List,
  Tag,
  Space,
  Select,
  DatePicker,
  Button,
  Spin,
  Typography,
  Empty,
} from 'antd';
import { CheckSquareOutlined, FilterOutlined, ReloadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useTodos } from '../hooks/useTodos';

const { Text } = Typography;

const TYPE_LABELS: Record<string, string> = {
  follow_up: '跟进提醒',
  contract_expiry: '合同到期',
  work_order: '工单处理',
  work_report: '日报/周报',
  handover: '离职交接',
};

const PRIORITY_COLORS: Record<string, string> = {
  high: 'red',
  medium: 'orange',
  normal: 'default',
  low: 'blue',
};

const TodoCenterPage: React.FC = () => {
  const navigate = useNavigate();
  const [type, setType] = useState<string | undefined>(undefined);
  const [priority, setPriority] = useState<string | undefined>(undefined);
  const [dateFrom, setDateFrom] = useState<string | undefined>(undefined);
  const [dateTo, setDateTo] = useState<string | undefined>(undefined);

  const { data, isLoading, error, refetch } = useTodos({
    type,
    priority,
    date_from: dateFrom,
    date_to: dateTo,
    limit: 100,
  });

  const handleTodoClick = (todo: typeof data extends { items: (infer T)[] } ? T : never) => {
    if (todo.link) {
      navigate(todo.link);
    }
  };

  const handleResetFilters = () => {
    setType(undefined);
    setPriority(undefined);
    setDateFrom(undefined);
    setDateTo(undefined);
  };

  const items = data?.items || [];

  return (
    <Card
      title={
        <Space>
          <CheckSquareOutlined />
          待办中心
          <Tag color="blue">{data?.total || 0} 项</Tag>
        </Space>
      }
      extra={
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
            刷新
          </Button>
        </Space>
      }
    >
      <Space style={{ marginBottom: 16 }} wrap>
        <FilterOutlined style={{ color: '#1890ff' }} />
        <Select
          placeholder="类型"
          allowClear
          style={{ width: 120 }}
          value={type}
          onChange={(v) => setType(v)}
          options={[
            { value: 'follow_up', label: '跟进提醒' },
            { value: 'contract_expiry', label: '合同到期' },
            { value: 'work_order', label: '工单处理' },
            { value: 'work_report', label: '日报/周报' },
            { value: 'handover', label: '离职交接' },
          ]}
        />
        <Select
          placeholder="优先级"
          allowClear
          style={{ width: 100 }}
          value={priority}
          onChange={(v) => setPriority(v)}
          options={[
            { value: 'high', label: '高' },
            { value: 'medium', label: '中' },
            { value: 'normal', label: '普通' },
            { value: 'low', label: '低' },
          ]}
        />
        <DatePicker
          placeholder="开始日期"
          style={{ width: 140 }}
          value={dateFrom ? dayjs(dateFrom) : null}
          onChange={(d) => setDateFrom(d ? d.format('YYYY-MM-DD') : undefined)}
        />
        <DatePicker
          placeholder="结束日期"
          style={{ width: 140 }}
          value={dateTo ? dayjs(dateTo) : null}
          onChange={(d) => setDateTo(d ? d.format('YYYY-MM-DD') : undefined)}
        />
        <Button onClick={handleResetFilters}>重置</Button>
      </Space>

      {isLoading ? (
        <Spin size="large" style={{ display: 'block', margin: '60px auto' }} />
      ) : error ? (
        <Empty description="加载失败" />
      ) : items.length === 0 ? (
        <Empty description="暂无待办事项" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        <List
          dataSource={items}
          renderItem={(item) => (
            <List.Item
              onClick={() => handleTodoClick(item)}
              style={{
                cursor: item.link ? 'pointer' : 'default',
                background: item.priority === 'high' ? '#fff1f0' : 'transparent',
                padding: '12px 16px',
                borderRadius: 4,
              }}
            >
              <List.Item.Meta
                title={
                  <Space>
                    <Text strong={item.priority === 'high'}>{item.title}</Text>
                    <Tag color={TYPE_LABELS[item.type] ? 'blue' : 'default'}>
                      {TYPE_LABELS[item.type] || item.type}
                    </Tag>
                    <Tag color={PRIORITY_COLORS[item.priority] || 'default'}>
                      {item.priority === 'high' ? '高' : item.priority === 'medium' ? '中' : item.priority === 'low' ? '低' : '普通'}
                    </Tag>
                  </Space>
                }
                description={item.description || ' '}
              />
              <Text type="secondary">{item.due_date || ''}</Text>
            </List.Item>
          )}
        />
      )}
    </Card>
  );
};

export default TodoCenterPage;