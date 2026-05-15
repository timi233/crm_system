import React from 'react';
import { Alert, Col, Row, Skeleton, Space, Tag, Typography } from 'antd';
import { useSelector } from 'react-redux';
import { RootState } from '../../store/store';
import { getRoleLabel } from '../../utils/roles';
import BrandCard from '../common/BrandCard';
import { useRoleDashboard } from '../../hooks/useRoleDashboard';
import DashboardMetricGrid from './DashboardMetricGrid';
import DashboardQuickActions from './DashboardQuickActions';
import DashboardRiskList from './DashboardRiskList';
import DashboardTodoList from './DashboardTodoList';

const { Text, Title } = Typography;

const SCOPE_LABELS: Record<string, string> = {
  personal: '个人视图',
  team: '团队视图',
  global: '全局视图',
};

const REPORT_STATUS_LABELS: Record<string, string> = {
  not_created: '未生成',
  draft: '草稿',
  submitted: '已提交',
  withdrawn: '已撤回',
  team_view: '团队视图',
};

const REPORT_STATUS_COLORS: Record<string, string> = {
  not_created: 'default',
  draft: 'orange',
  submitted: 'green',
  withdrawn: 'gold',
  team_view: 'blue',
};

const RoleDashboard: React.FC = () => {
  const { user, capabilities } = useSelector((state: RootState) => state.auth);
  const { data, isLoading, error, refetch } = useRoleDashboard();

  if (isLoading) {
    return (
      <div style={{ padding: 24 }}>
        <Skeleton active paragraph={{ rows: 10 }} />
      </div>
    );
  }

  if (error || !data) {
    return (
      <Alert
        type="error"
        message="工作台加载失败"
        description={<a onClick={() => refetch()}>重新加载</a>}
        showIcon
      />
    );
  }

  const reportStatus = data.report_status;

  return (
    <div style={{ padding: 24 }}>
      <Row justify="space-between" align="middle" gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col>
          <Title level={4} style={{ margin: 0 }}>我的工作台</Title>
          <Space size={8} wrap style={{ marginTop: 8 }}>
            <Text type="secondary">欢迎，{user?.name}</Text>
            <Tag color="blue">{getRoleLabel(data.role || user?.role)}</Tag>
            <Tag>{SCOPE_LABELS[data.scope] || data.scope}</Tag>
          </Space>
        </Col>
        <Col>
          <Text type="secondary">
            更新于 {data.generated_at ? new Date(data.generated_at).toLocaleString() : '-'}
          </Text>
        </Col>
      </Row>

      {reportStatus && (
        <BrandCard title="日报/周报状态" variant="primary" style={{ marginBottom: 16 }}>
          <Space size={16} wrap>
            <span>
              今日日报：
              <Tag color={REPORT_STATUS_COLORS[reportStatus.daily || ''] || 'default'} style={{ marginLeft: 8 }}>
                {REPORT_STATUS_LABELS[reportStatus.daily || ''] || reportStatus.daily || '-'}
              </Tag>
            </span>
            <span>
              本周周报：
              <Tag color={REPORT_STATUS_COLORS[reportStatus.weekly || ''] || 'default'} style={{ marginLeft: 8 }}>
                {REPORT_STATUS_LABELS[reportStatus.weekly || ''] || reportStatus.weekly || '-'}
              </Tag>
            </span>
          </Space>
        </BrandCard>
      )}

      <div style={{ marginBottom: 16 }}>
        <DashboardMetricGrid metrics={data.metrics || []} />
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <DashboardTodoList todos={data.todos || []} />
        </Col>
        <Col xs={24} lg={8}>
          <DashboardQuickActions
            actions={data.quick_actions || []}
            capabilities={capabilities as Record<string, boolean>}
          />
        </Col>
        <Col xs={24}>
          <DashboardRiskList risks={data.risks || []} />
        </Col>
      </Row>
    </div>
  );
};

export default RoleDashboard;
