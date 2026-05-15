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

const PRIORITY_COLORS: Record<string, string> = {
  low: 'blue',
  normal: 'default',
  medium: 'orange',
  high: 'red',
  高: 'red',
  中: 'orange',
  低: 'blue',
};

const DashboardTodoList: React.FC<Props> = ({ todos, showMoreLink = true }) => {
  const navigate = useNavigate();

  return (
    <BrandCard title="待办事项" variant="primary" extra={showMoreLink ? (
      <Button type="link" size="small" onClick={() => navigate('/todos')}>
        查看全部 <RightOutlined />
      </Button>
    ) : null}>
      {todos.length === 0 ? (
        <Empty description="暂无待办事项" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        <List
          dataSource={todos}
          renderItem={(item) => (
            <List.Item
              onClick={() => item.link && navigate(item.link)}
              style={{ cursor: item.link ? 'pointer' : 'default' }}
              actions={[
                <Tag key="priority" color={PRIORITY_COLORS[item.priority || 'normal'] || 'default'}>
                  {item.priority || 'normal'}
                </Tag>,
              ]}
            >
              <List.Item.Meta title={item.title} description={item.description || ' '} />
              <Text type="secondary">{item.due_date || ''}</Text>
            </List.Item>
          )}
        />
      )}
    </BrandCard>
  );
};

export default DashboardTodoList;
