import React from 'react';
import { Button, Empty, Space } from 'antd';
import {
  BarChartOutlined,
  FileTextOutlined,
  FundProjectionScreenOutlined,
  HistoryOutlined,
  PlusOutlined,
  SettingOutlined,
  TeamOutlined,
  ToolOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import BrandCard from '../common/BrandCard';
import { DashboardQuickAction } from '../../hooks/useRoleDashboard';

type Props = {
  actions: DashboardQuickAction[];
  capabilities: Record<string, boolean>;
};

const ICONS: Record<string, React.ReactNode> = {
  users: <TeamOutlined />,
  logs: <HistoryOutlined />,
  alerts: <SettingOutlined />,
  dict: <SettingOutlined />,
  targets: <BarChartOutlined />,
  reports: <FileTextOutlined />,
  opportunities: <FundProjectionScreenOutlined />,
  'reports-funnel': <BarChartOutlined />,
  customers: <TeamOutlined />,
  leads: <PlusOutlined />,
  followups: <FileTextOutlined />,
  contracts: <FileTextOutlined />,
  payment: <BarChartOutlined />,
  performance: <BarChartOutlined />,
  workorders: <ToolOutlined />,
  knowledge: <FileTextOutlined />,
  channels: <TeamOutlined />,
  training: <FileTextOutlined />,
};

const DashboardQuickActions: React.FC<Props> = ({ actions, capabilities }) => {
  const navigate = useNavigate();
  const visibleActions = actions.filter((action) => !action.capability || capabilities[action.capability]);

  return (
    <BrandCard title="快捷入口" variant="secondary">
      {visibleActions.length === 0 ? (
        <Empty description="暂无可用入口" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        <Space direction="vertical" style={{ width: '100%' }}>
          {visibleActions.map((action) => (
            <Button
              key={action.key}
              icon={ICONS[action.key] || <FileTextOutlined />}
              onClick={() => navigate(action.link)}
              block
            >
              {action.title}
            </Button>
          ))}
        </Space>
      )}
    </BrandCard>
  );
};

export default DashboardQuickActions;
