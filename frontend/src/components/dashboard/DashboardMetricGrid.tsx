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
  users: <UserOutlined style={{ color: '#6366f1' }} />,
  alerts: <AlertOutlined style={{ color: '#ef4444' }} />,
  logs: <FileTextOutlined style={{ color: '#64748b' }} />,
  leads: <UserOutlined style={{ color: '#f59e0b' }} />,
  opportunities: <TeamOutlined style={{ color: '#06b6d4' }} />,
  projects: <FundProjectionScreenOutlined style={{ color: '#8b5cf6' }} />,
  contracts: <ProfileOutlined style={{ color: '#ec4899' }} />,
  targets: <BarChartOutlined style={{ color: '#10b981' }} />,
  followups: <FileTextOutlined style={{ color: '#3b82f6' }} />,
  amount: <DollarOutlined style={{ color: '#10b981' }} />,
  assigned: <ToolOutlined style={{ color: '#6366f1' }} />,
  pending: <ToolOutlined style={{ color: '#f59e0b' }} />,
  in_progress: <ToolOutlined style={{ color: '#3b82f6' }} />,
  channels: <TeamOutlined style={{ color: '#8b5cf6' }} />,
  plans: <FileTextOutlined style={{ color: '#64748b' }} />,
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
    <Row gutter={[20, 20]}>
      {metrics.map((metric) => (
        <Col key={metric.key} xs={24} sm={12} lg={8} xl={6}>
          <div
            onClick={() => metric.link && navigate(metric.link)}
            style={{
              background: 'white',
              padding: '20px',
              borderRadius: '12px',
              border: '1px solid #f1f5f9',
              boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
              cursor: metric.link ? 'pointer' : 'default',
              transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between'
            }}
            className="metric-card-hover"
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div style={{
                width: '40px',
                height: '40px',
                borderRadius: '10px',
                background: '#f8fafc',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '20px'
              }}>
                {ICONS[metric.key] || <BarChartOutlined style={{ color: '#64748b' }} />}
              </div>
              {metric.status && metric.status !== 'normal' && (
                <Tag
                  color={STATUS_COLORS[metric.status] || 'default'}
                  style={{
                    marginInlineEnd: 0,
                    borderRadius: '6px',
                    border: 'none',
                    fontSize: '11px',
                    fontWeight: 600,
                    textTransform: 'uppercase'
                  }}
                >
                  {metric.status}
                </Tag>
              )}
            </div>
            <div>
              <div style={{ fontSize: '13px', color: '#64748b', fontWeight: 500, marginBottom: '4px' }}>
                {metric.title}
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
                <div style={{ fontSize: '24px', fontWeight: 700, color: '#0f172a', letterSpacing: '-0.5px' }} className="number-display">
                  {typeof metric.value === 'number' ? metric.value.toLocaleString() : metric.value}
                </div>
                {metric.unit && <span style={{ fontSize: '13px', color: '#94a3b8' }}>{metric.unit}</span>}
              </div>
            </div>
          </div>
        </Col>
      ))}
    </Row>
  );
};

export default DashboardMetricGrid;
