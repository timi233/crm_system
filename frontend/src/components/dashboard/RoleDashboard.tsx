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
    <div className="fade-in" style={{ padding: '0 0 24px 0' }}>
      <div style={{
        background: 'white',
        padding: '24px 32px',
        borderRadius: '12px',
        marginBottom: '24px',
        border: '1px solid #f1f5f9',
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)'
      }}>
        <Row justify="space-between" align="middle" gutter={[16, 16]}>
          <Col>
            <div style={{ fontSize: '14px', color: '#64748b', fontWeight: 500, marginBottom: '4px' }}>
              {new Date().getHours() < 12 ? '早上好' : new Date().getHours() < 18 ? '下午好' : '晚上好'}，
            </div>
            <Title level={3} style={{ margin: 0, fontWeight: 700, letterSpacing: '-0.5px' }}>
              {user?.name}
            </Title>
            <Space size={8} wrap style={{ marginTop: 12 }}>
              <Tag color="blue" style={{ borderRadius: '6px', border: 'none', padding: '2px 10px' }}>
                {getRoleLabel(data.role || user?.role)}
              </Tag>
              <Tag style={{ borderRadius: '6px', border: 'none', padding: '2px 10px', background: '#f1f5f9', color: '#475569' }}>
                {SCOPE_LABELS[data.scope] || data.scope}
              </Tag>
              <Text type="secondary" style={{ fontSize: '13px', marginLeft: '8px' }}>
                数据更新于: {data.generated_at ? new Date(data.generated_at).toLocaleTimeString() : '-'}
              </Text>
            </Space>
          </Col>
          <Col>
            {data.metrics?.find(m => m.key === 'completion_rate') && (
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>本月目标完成率</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ width: '120px', height: '8px', background: '#f1f5f9', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ width: `${data.metrics.find(m => m.key === 'completion_rate')?.value || 0}%`, height: '100%', background: 'var(--primary-gradient)' }} />
                  </div>
                  <span style={{ fontWeight: 700, color: '#0f172a' }}>{data.metrics.find(m => m.key === 'completion_rate')?.value || 0}%</span>
                </div>
              </div>
            )}
          </Col>
        </Row>
      </div>

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
