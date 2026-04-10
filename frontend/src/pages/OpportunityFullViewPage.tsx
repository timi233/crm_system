import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Descriptions, Tag, Table, Spin, Button, Space, Typography, Tabs, message } from 'antd';
import { ArrowLeftOutlined, UserOutlined, ToolOutlined } from '@ant-design/icons';
import { useOpportunity } from '../hooks/useOpportunities';
import { useFollowUps } from '../hooks/useFollowUps';
import { useNineA } from '../hooks/useNineA';
import { useCreateDispatchFromOpportunity } from '../hooks/useDispatch';
import DispatchModal from '../components/common/DispatchModal';
import DispatchHistoryTable from '../components/dispatch/DispatchHistoryTable';

const { Title } = Typography;

const OpportunityFullViewPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: opportunity, isLoading: oppLoading } = useOpportunity(Number(id));
  const { data: followUps = [], isLoading: followUpsLoading } = useFollowUps({ opportunity_id: Number(id) });
  const { data: nineA, isLoading: nineALoading } = useNineA(Number(id));
  const { mutate: createDispatch, isPending: dispatchLoading } = useCreateDispatchFromOpportunity();
  const [dispatchModalVisible, setDispatchModalVisible] = useState(false);

  if (oppLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!opportunity) {
    return <div>未找到商机信息</div>;
  }

  const handleCreateDispatch = async (values: any) => {
    try {
      await createDispatch({
        opportunityId: Number(id),
        request: values,
      });
      message.success('派工申请创建成功！');
    } catch (error: any) {
      message.error(error.message || '派工申请创建失败');
      throw error;
    }
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
      children: nineALoading ? (
        <Spin />
      ) : nineA ? (
        <Descriptions column={2} bordered size="small">
          <Descriptions.Item label="关键事件" span={2}>{nineA.key_events || '-'}</Descriptions.Item>
          <Descriptions.Item label="预算">{nineA.budget ? `¥${nineA.budget.toLocaleString()}` : '-'}</Descriptions.Item>
          <Descriptions.Item label="决策链影响度" span={2}>{nineA.decision_chain_influence || '-'}</Descriptions.Item>
          <Descriptions.Item label="客户的挑战和痛点" span={2}>{nineA.customer_challenges || '-'}</Descriptions.Item>
          <Descriptions.Item label="客户需求和价值诉求" span={2}>{nineA.customer_needs || '-'}</Descriptions.Item>
          <Descriptions.Item label="解决方案和差异化因素" span={2}>{nineA.solution_differentiation || '-'}</Descriptions.Item>
          <Descriptions.Item label="竞争者" span={2}>{nineA.competitors || '-'}</Descriptions.Item>
          <Descriptions.Item label="购买方式" span={2}>{nineA.buying_method || '-'}</Descriptions.Item>
        </Descriptions>
      ) : (
        <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
          暂无9A分析数据，请在商机列表中点击"9A管理"按钮添加
        </div>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>
            返回
          </Button>
          <Title level={4} style={{ margin: 0 }}>
            {opportunity.opportunity_name}
            <Tag color="blue" style={{ marginLeft: 8 }}>{opportunity.opportunity_code}</Tag>
          </Title>
          <Button 
            icon={<ToolOutlined />} 
            type="primary"
            onClick={() => setDispatchModalVisible(true)}
            disabled={opportunity.opportunity_stage === '已成交' || opportunity.opportunity_stage === '已流失'}
          >
            派工申请
          </Button>
        </Space>

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
            <Descriptions.Item label="线索等级">{opportunity.lead_grade}</Descriptions.Item>
            <Descriptions.Item label="预计金额">{opportunity.expected_contract_amount ? `¥${opportunity.expected_contract_amount.toLocaleString()}` : '-'}</Descriptions.Item>
            <Descriptions.Item label="预计关闭日期">{opportunity.expected_close_date || '-'}</Descriptions.Item>
            <Descriptions.Item label="项目状态">
              {opportunity.project_id ? <Tag color="blue">已转项目</Tag> : <Tag color="orange">跟进中</Tag>}
            </Descriptions.Item>
            <Descriptions.Item label="流失原因">{opportunity.loss_reason || '-'}</Descriptions.Item>
            <Descriptions.Item label="创建时间" span={4}>{opportunity.created_at || '-'}</Descriptions.Item>
          </Descriptions>
        </Card>

        <Card title="关联信息">
          <Tabs items={tabItems} />
        </Card>

        <Card title="派工历史" style={{ marginTop: 16 }}>
          <DispatchHistoryTable opportunity_id={Number(id)} />
        </Card>
      </Card>

      <DispatchModal
        visible={dispatchModalVisible}
        onClose={() => setDispatchModalVisible(false)}
        onSubmit={handleCreateDispatch}
        loading={dispatchLoading}
      />
    </div>
  );
};

export default OpportunityFullViewPage;