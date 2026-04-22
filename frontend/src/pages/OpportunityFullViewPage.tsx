import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { App, Card, Descriptions, Tag, Table, Skeleton, Button, Space, Typography, Tabs, Timeline, Tooltip } from 'antd';
import { ArrowLeftOutlined, UserOutlined, ToolOutlined, ClockCircleOutlined, CommentOutlined } from '@ant-design/icons';
import { useQueryClient } from '@tanstack/react-query';
import { useOpportunity } from '../hooks/useOpportunities';
import { useFollowUps } from '../hooks/useFollowUps';
import { useNineA, useNineAVersions } from '../hooks/useNineA';
import { useCreateDispatchFromOpportunity } from '../hooks/useDispatch';
import DispatchModal from '../components/common/DispatchModal';
import DispatchHistoryTable from '../components/dispatch/DispatchHistoryTable';
import FollowUpModal from '../components/modals/FollowUpModal';
import PageScaffold from '../components/common/PageScaffold';

const { Title } = Typography;

const OpportunityFullViewPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { message } = App.useApp();
  const queryClient = useQueryClient();
  const { data: opportunity, isLoading: oppLoading } = useOpportunity(Number(id));
  const { data: followUps = [], isLoading: followUpsLoading } = useFollowUps({ opportunity_id: Number(id) });
  const { data: nineA, isLoading: nineALoading } = useNineA(Number(id));
  const { data: nineAVersions = [], isLoading: versionsLoading } = useNineAVersions(Number(id));
  const { mutateAsync: createDispatch, isPending: dispatchLoading } = useCreateDispatchFromOpportunity();
  const [dispatchModalVisible, setDispatchModalVisible] = useState(false);
  const [followUpModalVisible, setFollowUpModalVisible] = useState(false);

  if (oppLoading) {
    return <Skeleton active />;
  }

  if (!opportunity) {
    return <div>未找到商机信息</div>;
  }

  const breadcrumbs = [
    { title: '首页', href: '/dashboard' },
    { title: '商机管理', href: '/opportunities' },
    { title: `商机 ${opportunity.opportunity_code}`, href: '#' },
  ];

  const handleCreateDispatch = async (data: { technicianIds: number[]; startDate: string; startPeriod: string; endDate: string; endPeriod: string; workType: string; serviceMode: 'online' | 'offline' }) => {
    try {
      await createDispatch({ 
        entityId: Number(id), 
        technicianIds: data.technicianIds,
        startDate: data.startDate,
        startPeriod: data.startPeriod,
        endDate: data.endDate,
        endPeriod: data.endPeriod,
        workType: data.workType,
        serviceMode: data.serviceMode
      });
      message.success('派工创建成功！派工历史已更新');
      queryClient.invalidateQueries({ queryKey: ['dispatchRecords'] });
    } catch (error: any) {
      message.error(error.message || '派工创建失败');
    }
  };

  const dispatchInfo = {
    customer_name: opportunity.terminal_customer_name,
    contact: opportunity.sales_owner_name,
    phone: undefined,
    entity_name: opportunity.opportunity_name,
    entity_type: '商机',
  };

  const getStageColor = (stage: string) => {
    const colors: Record<string, string> = {
      '需求方案': 'blue',
      '需求确认': 'cyan',
      '报价投标': 'gold',
      '合同签订': 'purple',
      '已成交': 'green',
      '已流失': 'red',
    };
    return colors[stage] || 'default';
  };

  const followUpColumns = [
    { title: '跟进日期', dataIndex: 'follow_up_date', key: 'follow_up_date', width: 120 },
    { title: '跟进方式', dataIndex: 'follow_up_method', key: 'follow_up_method', width: 100 },
    { title: '跟进内容', dataIndex: 'follow_up_content', key: 'follow_up_content', ellipsis: true },
    { title: '跟进结论', dataIndex: 'follow_up_conclusion', key: 'follow_up_conclusion', width: 100, render: (s: string) => <Tag color="blue">{s}</Tag> },
    { title: '下次行动', dataIndex: 'next_action', key: 'next_action', ellipsis: true },
    { title: '跟进人', dataIndex: 'follower_name', key: 'follower_name', width: 100 },
  ];

  const tabItems = [
    {
      key: 'follow_ups',
      label: `跟进记录 (${followUps.length})`,
      children: (
        <Table
          columns={followUpColumns}
          dataSource={followUps}
          rowKey="id"
          loading={followUpsLoading}
          pagination={{ pageSize: 10 }}
          size="small"
        />
      ),
    },
    {
      key: 'nine_a',
      label: '9A分析',
      children: nineALoading || versionsLoading ? (
        <Skeleton active />
      ) : nineAVersions.length > 0 ? (
        <Timeline
          items={nineAVersions.map((version, index) => ({
            key: version.id,
            color: index === 0 ? 'green' : 'gray',
            dot: index === 0 ? <ClockCircleOutlined style={{ fontSize: '14px' }} /> : undefined,
            children: (
              <Card 
                size="small" 
                style={{ marginBottom: 8 }}
                title={
                  <Space>
                    <span style={{ fontWeight: index === 0 ? 600 : 400 }}>
                      {version.created_at ? new Date(version.created_at).toLocaleString('zh-CN') : '-'}
                    </span>
                    <Tag color={index === 0 ? 'green' : 'default'}>
                      {version.created_by_name || '未知用户'}
                    </Tag>
                    {index === 0 && <Tag color="blue">当前</Tag>}
                  </Space>
                }
              >
                <Descriptions column={2} size="small">
                  <Descriptions.Item label="关键事件" span={2}>{version.key_events || '-'}</Descriptions.Item>
                  <Descriptions.Item label="预算">{version.budget ? `¥${version.budget.toLocaleString()}` : '-'}</Descriptions.Item>
                  <Descriptions.Item label="关单时间">{version.close_date || '-'}</Descriptions.Item>
                  <Descriptions.Item label="决策链影响度" span={2}>{version.decision_chain_influence || '-'}</Descriptions.Item>
                  <Descriptions.Item label="客户的挑战和痛点" span={2}>{version.customer_challenges || '-'}</Descriptions.Item>
                  <Descriptions.Item label="客户需求和价值诉求" span={2}>{version.customer_needs || '-'}</Descriptions.Item>
                  <Descriptions.Item label="解决方案和差异化因素" span={2}>{version.solution_differentiation || '-'}</Descriptions.Item>
                  <Descriptions.Item label="竞争者" span={2}>{version.competitors || '-'}</Descriptions.Item>
                  <Descriptions.Item label="购买方式" span={2}>{version.buying_method || '-'}</Descriptions.Item>
                </Descriptions>
              </Card>
            ),
          }))}
        />
      ) : (
        <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
          暂无9A分析数据，请在商机列表中点击"9A管理"按钮添加
        </div>
      ),
    },
  ];

  return (
    <PageScaffold
      title={`${opportunity.opportunity_code} - ${opportunity.opportunity_name}`}
      breadcrumbItems={[
        { title: '首页', href: '/dashboard' },
        { title: '商机管理', href: '/opportunities' },
        { title: opportunity.opportunity_code },
      ]}
      extra={
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>返回</Button>
          <Tooltip title={opportunity.opportunity_stage === '已成交' || opportunity.opportunity_stage === '已流失' ? '商机已成交或已流失，不可新增派工' : ''}>
            <Button 
              icon={<ToolOutlined />} 
              type="primary"
              onClick={() => setDispatchModalVisible(true)}
              disabled={opportunity.opportunity_stage === '已成交' || opportunity.opportunity_stage === '已流失'}
            >
              新增派工
            </Button>
          </Tooltip>
          <Tooltip title={opportunity.opportunity_stage === '已成交' || opportunity.opportunity_stage === '已流失' ? '商机已成交或已流失，不可新增跟进' : ''}>
            <Button 
              icon={<CommentOutlined />} 
              onClick={() => setFollowUpModalVisible(true)}
              disabled={opportunity.opportunity_stage === '已成交' || opportunity.opportunity_stage === '已流失'}
            >
              新增跟进记录
            </Button>
          </Tooltip>
        </Space>
      }
    >
      <Card title="商机基本信息" style={{ marginBottom: 16 }} size="small">
          <Descriptions column={4} bordered size="small">
            <Descriptions.Item label="商机编号">{opportunity.opportunity_code}</Descriptions.Item>
            <Descriptions.Item label="商机名称">{opportunity.opportunity_name}</Descriptions.Item>
            <Descriptions.Item label="阶段">
              <Tag color={getStageColor(opportunity.opportunity_stage)}>{opportunity.opportunity_stage}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="来源">{opportunity.opportunity_source}</Descriptions.Item>
            <Descriptions.Item label="终端客户">{opportunity.terminal_customer_name}</Descriptions.Item>
            <Descriptions.Item label="负责人">
              <UserOutlined style={{ marginRight: 4 }} />
              {opportunity.sales_owner_name}
            </Descriptions.Item>
            <Descriptions.Item label="关联渠道">{opportunity.channel_name || '-'}</Descriptions.Item>
            <Descriptions.Item label="产品">{opportunity.products && opportunity.products.length > 0 ? opportunity.products.map((p: string) => <Tag key={p} color="blue">{p}</Tag>) : '-'}</Descriptions.Item>
            <Descriptions.Item label="预计金额">{opportunity.expected_contract_amount ? `¥${opportunity.expected_contract_amount.toLocaleString()}` : '-'}</Descriptions.Item>
            <Descriptions.Item label="预计关闭日期">{opportunity.expected_close_date || '-'}</Descriptions.Item>
            <Descriptions.Item label="项目状态">
              {opportunity.project_id ? <Tag color="blue">已转项目</Tag> : <Tag color="orange">跟进中</Tag>}
            </Descriptions.Item>
            <Descriptions.Item label="流失原因">{opportunity.loss_reason || '-'}</Descriptions.Item>
            <Descriptions.Item label="创建时间" span={4}>{opportunity.created_at || '-'}</Descriptions.Item>
          </Descriptions>
        </Card>

        <Card title="关联信息" style={{ marginBottom: 16 }}>
          <Tabs items={tabItems} />
        </Card>

        <Card title="派工历史">
          <DispatchHistoryTable opportunity_id={Number(id)} />
        </Card>

        <DispatchModal
          visible={dispatchModalVisible}
          onClose={() => setDispatchModalVisible(false)}
          onSubmit={handleCreateDispatch}
          loading={dispatchLoading}
          dispatchInfo={dispatchInfo}
        />

        <FollowUpModal
          visible={followUpModalVisible}
          onClose={() => setFollowUpModalVisible(false)}
          opportunity_id={Number(id)}
          terminal_customer_id={opportunity.terminal_customer_id}
        />
    </PageScaffold>
  );
};

export default OpportunityFullViewPage;
