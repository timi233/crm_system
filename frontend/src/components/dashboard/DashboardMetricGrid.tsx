import React from 'react';
import { Col, Empty, Row, Tag } from 'antd';
import {
  AlertOutlined,
  BarChartOutlined,
  DollarOutlined,
  FileTextOutlined,
  FundProjectionScreenOutlined,
  ProfileOutlined,
  TeamOutlined,
  ToolOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import BrandCard from '../common/BrandCard';
import UnifiedStatistic from '../common/UnifiedStatistic';
import { DashboardMetricCard } from '../../hooks/useRoleDashboard';

type Props = {
  metrics: DashboardMetricCard[];
};

const ICONS: Record<string, React.ReactNode> = {
  users: <UserOutlined />,
  alerts: <AlertOutlined />,
  logs: <FileTextOutlined />,
  leads: <UserOutlined />,
  opportunities: <TeamOutlined />,
  projects: <FundProjectionScreenOutlined />,
  contracts: <ProfileOutlined />,
  targets: <BarChartOutlined />,
  followups: <FileTextOutlined />,
  amount: <DollarOutlined />,
  assigned: <ToolOutlined />,
  pending: <ToolOutlined />,
  in_progress: <ToolOutlined />,
  channels: <TeamOutlined />,
  plans: <FileTextOutlined />,
};

const STATUS_COLORS: Record<string, string> = {
  normal: 'blue',
  success: 'green',
  warning: 'orange',
  danger: 'red',
};

const DashboardMetricGrid: React.FC<Props> = ({ metrics }) => {
  const navigate = useNavigate();

  if (metrics.length === 0) {
    return <Empty description="暂无指标数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />;
  }

  return (
    <Row gutter={[16, 16]}>
      {metrics.map((metric) => (
        <Col key={metric.key} xs={24} sm={12} lg={8} xl={6}>
          <BrandCard
            hoverable={Boolean(metric.link)}
            onClick={() => metric.link && navigate(metric.link)}
            variant="secondary"
            style={{ height: '100%' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
              <UnifiedStatistic
                title={metric.title}
                value={metric.value || 0}
                prefix={ICONS[metric.key] || <BarChartOutlined />}
                suffix={metric.unit || ''}
              />
              {metric.status && metric.status !== 'normal' && (
                <Tag color={STATUS_COLORS[metric.status] || 'default'} style={{ marginInlineEnd: 0 }}>
                  {metric.status}
                </Tag>
              )}
            </div>
          </BrandCard>
        </Col>
      ))}
    </Row>
  );
};

export default DashboardMetricGrid;
