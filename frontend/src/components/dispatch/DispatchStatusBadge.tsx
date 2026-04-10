import React from 'react';
import { Tag } from 'antd';
import type { DispatchStatus } from '../../types/dispatch';

interface DispatchStatusBadgeProps {
  status: DispatchStatus | string;
}

const statusConfig: Record<DispatchStatus, { color: string; text: string }> = {
  pending: { color: 'blue', text: '待处理' },
  assigned: { color: 'cyan', text: '已分配' },
  in_progress: { color: 'gold', text: '进行中' },
  completed: { color: 'green', text: '已完成' },
  cancelled: { color: 'red', text: '已取消' },
};

export const DispatchStatusBadge: React.FC<DispatchStatusBadgeProps> = ({ status }) => {
  const config = statusConfig[status as DispatchStatus] || { color: 'default', text: status };

  return <Tag color={config.color}>{config.text}</Tag>;
};
