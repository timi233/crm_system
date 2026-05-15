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
  message,
} from 'antd';
import { CheckSquareOutlined, FilterOutlined, ReloadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useTodos } from '../hooks/useTodos';
import PageScaffold from '../components/common/PageScaffold';

const { Text } = Typography;

const TYPE_LABELS: Record<string, string> = {
  follow_up: '跟进提醒',
  contract_expiry: '合同到期',
  work_order: '工单处理',
  work_report: '日报/周报',
  handover: '离职交接',
};

const PRIORITY_COLORS: Record<string, { bg: string, color: string }> = {
  high: { bg: '#fef2f2', color: '#ef4444' },
  medium: { bg: '#fff7ed', color: '#f59e0b' },
  normal: { bg: '#f1f5f9', color: '#64748b' },
  low: { bg: '#eff6ff', color: '#3b82f6' },
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
    <PageScaffold
      title="待办中心"
      breadcrumbItems={[{ title: '首页', href: '/dashboard' }, { title: '待办中心' }]}
      extra={
        <Space>
          <Tag color="blue" style={{ borderRadius: '6px', border: 'none', padding: '2px 10px' }}>
            {data?.total || 0} 项待办
          </Tag>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
            刷新
          </Button>
        </Space>
      }
      filters={
        <Space size={12} wrap>
          <Select
            placeholder="类型"
            allowClear
            style={{ width: 150 }}
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
            style={{ width: 120 }}
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
      }
    >
      {isLoading ? (
        <Spin size="large" style={{ display: 'block', margin: '60px auto' }} />
      ) : error ? (
        <Empty description="加载失败" />
      ) : items.length === 0 ? (
        <Empty description="暂无待办事项" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        <List
          dataSource={items}
          renderItem={(item) => {
            const pColor = PRIORITY_COLORS[item.priority] || PRIORITY_COLORS.normal;
            return (
              <List.Item
                onClick={() => handleTodoClick(item)}
                style={{
                  cursor: item.link ? 'pointer' : 'default',
                  padding: '16px 24px',
                  borderBottom: '1px solid #f1f5f9',
                  transition: 'all 0.2s',
                }}
                className="list-item-hover"
              >
                <List.Item.Meta
                  title={
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span style={{ fontWeight: 700, color: '#1e293b' }}>{item.title}</span>
                      <Tag color="blue" style={{ border: 'none', background: '#e0e7ff', color: '#4338ca', fontSize: '11px', fontWeight: 700 }}>
                        {TYPE_LABELS[item.type] || item.type}
                      </Tag>
                      <span style={{
                        fontSize: '11px',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        background: pColor.bg,
                        color: pColor.color,
                        fontWeight: 700,
                        textTransform: 'uppercase'
                      }}>
                        {item.priority === 'high' ? '高' : item.priority === 'medium' ? '中' : item.priority === 'low' ? '低' : '普通'}
                      </span>
                    </div>
                  }
                  description={
                    <div style={{ marginTop: '4px', color: '#64748b' }}>
                      {item.description || ' '}
                    </div>
                  }
                />
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>截止日期</div>
                  <Text type="secondary" style={{ fontWeight: 500 }}>{item.due_date || '未设置'}</Text>
                </div>
              </List.Item>
            );
          }}
        />
      )}
    </PageScaffold>
  );
};

export default TodoCenterPage;