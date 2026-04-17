import React from 'react';
import { Result, Button, Space } from 'antd';

export interface EmptyStateProps {
  title?: string;
  description?: string;
  action?: React.ReactNode;
}

const EmptyState: React.FC<EmptyStateProps> = ({
  title = '暂无数据',
  description = '请尝试创建新记录或调整筛选条件',
  action,
}) => (
  <Result
    status="404"
    title={title}
    subTitle={description}
    extra={action && <Space>{action}</Space>}
    style={{ padding: '40px 0' }}
  />
);

export default EmptyState;
