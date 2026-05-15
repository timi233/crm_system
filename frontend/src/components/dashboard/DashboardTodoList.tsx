import React from 'react';
import { Empty, List, Tag, Typography, Button, Space } from 'antd';
import { useNavigate } from 'react-router-dom';
import { RightOutlined } from '@ant-design/icons';
import BrandCard from '../common/BrandCard';
import { DashboardTodoItem } from '../../hooks/useRoleDashboard';

const { Text } = Typography;

type Props = {
  todos: DashboardTodoItem[];
  showMoreLink?: boolean;
};

const PRIORITY_COLORS: Record<string, { bg: string, color: string }> = {
  low: { bg: '#eff6ff', color: '#3b82f6' },
  normal: { bg: '#f1f5f9', color: '#64748b' },
  medium: { bg: '#fff7ed', color: '#f59e0b' },
  high: { bg: '#fef2f2', color: '#ef4444' },
  高: { bg: '#fef2f2', color: '#ef4444' },
  中: { bg: '#fff7ed', color: '#f59e0b' },
  低: { bg: '#eff6ff', color: '#3b82f6' },
};

const DashboardTodoList: React.FC<Props> = ({ todos, showMoreLink = true }) => {
  const navigate = useNavigate();

  return (
    <div style={{
      background: 'white',
      borderRadius: '12px',
      border: '1px solid #f1f5f9',
      boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
      height: '100%'
    }}>
      <div style={{
        padding: '20px 24px',
        borderBottom: '1px solid #f1f5f9',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a' }}>待办事项</div>
        {showMoreLink && (
          <Button type="link" size="small" onClick={() => navigate('/todos')} style={{ padding: 0 }}>
            查看全部 <RightOutlined />
          </Button>
        )}
      </div>
      <div style={{ padding: '8px 0' }}>
        {todos.length === 0 ? (
          <div style={{ padding: '40px 0' }}>
            <Empty description="暂无待办事项" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          </div>
        ) : (
          <List
            dataSource={todos}
            renderItem={(item) => {
              const priority = PRIORITY_COLORS[item.priority || 'normal'] || PRIORITY_COLORS.normal;
              return (
                <List.Item
                  onClick={() => item.link && navigate(item.link)}
                  style={{
                    cursor: item.link ? 'pointer' : 'default',
                    padding: '16px 24px',
                    transition: 'all 0.2s',
                    borderBottom: '1px solid #f8fafc'
                  }}
                  className="list-item-hover"
                >
                  <List.Item.Meta
                    title={
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <span style={{ fontWeight: 600, color: '#1e293b' }}>{item.title}</span>
                        <span style={{
                          fontSize: '11px',
                          padding: '2px 8px',
                          borderRadius: '4px',
                          background: priority.bg,
                          color: priority.color,
                          fontWeight: 700,
                          textTransform: 'uppercase'
                        }}>
                          {item.priority || 'normal'}
                        </span>
                      </div>
                    }
                    description={
                      <div style={{ marginTop: '4px' }}>
                        <div style={{ fontSize: '13px', color: '#64748b' }}>{item.description || ' '}</div>
                        <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>
                          截止日期: {item.due_date || '未设置'}
                        </div>
                      </div>
                    }
                  />
                </List.Item>
              );
            }}
          />
        )}
      </div>
    </div>
  );
};

export default DashboardTodoList;
