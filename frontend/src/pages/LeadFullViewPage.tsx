import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { App, Card, Descriptions, Tag, Table, Skeleton, Button, Space, Typography, Tooltip } from 'antd';
import { ArrowLeftOutlined, UserOutlined, PhoneOutlined, ToolOutlined, CommentOutlined } from '@ant-design/icons';
import { useQueryClient } from '@tanstack/react-query';
import { useLead } from '../hooks/useLeads';
import { useFollowUps } from '../hooks/useFollowUps';
import { useCreateDispatchFromLead } from '../hooks/useDispatch';
import DispatchModal from '../components/common/DispatchModal';
import DispatchHistoryTable from '../components/dispatch/DispatchHistoryTable';
import FollowUpModal from '../components/modals/FollowUpModal';
import PageScaffold from '../components/common/PageScaffold';

const { Title } = Typography;

const LeadFullViewPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { message } = App.useApp();
  const queryClient = useQueryClient();
  const { data: lead, isLoading: leadLoading } = useLead(Number(id));
  const { data: followUps = [], isLoading: followUpsLoading } = useFollowUps({ lead_id: Number(id) });
  const { mutateAsync: createDispatch, isPending: dispatchLoading } = useCreateDispatchFromLead();
  const [dispatchModalVisible, setDispatchModalVisible] = useState(false);
  const [followUpModalVisible, setFollowUpModalVisible] = useState(false);

  if (leadLoading) {
    return <Skeleton active />;
  }

  if (!lead) {
    return <div>未找到线索信息</div>;
  }

  const breadcrumbs = [
    { title: '首页', href: '/dashboard' },
    { title: '线索管理', href: '/leads' },
    { title: `线索 ${lead.lead_code}`, href: '#' },
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
    customer_name: lead.terminal_customer_name,
    contact: lead.contact_person,
    phone: lead.contact_phone,
    entity_name: lead.lead_name,
    entity_type: '线索',
  };

  const getStageColor = (stage: string) => {
    const colors: Record<string, string> = {
      '初步接触': 'blue',
      '需求确认': 'cyan',
      '方案报价': 'gold',
      '商务谈判': 'purple',
      '已转化': 'green',
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

  return (
    <PageScaffold
      title={`${lead.lead_code} - ${lead.lead_name}`}
      breadcrumbItems={[
        { title: '首页', href: '/dashboard' },
        { title: '线索管理', href: '/leads' },
        { title: lead.lead_code },
      ]}
      extra={
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>返回</Button>
          <Tooltip title={lead.converted_to_opportunity ? '线索已转商机，不可新增派工' : ''}>
            <Button 
              icon={<ToolOutlined />} 
              type="primary"
              onClick={() => setDispatchModalVisible(true)}
              disabled={lead.converted_to_opportunity}
            >
              新增派工
            </Button>
          </Tooltip>
          <Tooltip title={lead.converted_to_opportunity ? '线索已转商机，不可新增跟进' : ''}>
            <Button 
              icon={<CommentOutlined />} 
              onClick={() => setFollowUpModalVisible(true)}
              disabled={lead.converted_to_opportunity}
            >
              新增跟进记录
            </Button>
          </Tooltip>
        </Space>
      }
    >
      <Card title="线索基本信息" style={{ marginBottom: 16 }} size="small">
          <Descriptions column={4} bordered size="small">
            <Descriptions.Item label="线索编号">{lead.lead_code}</Descriptions.Item>
            <Descriptions.Item label="线索名称">{lead.lead_name}</Descriptions.Item>
            <Descriptions.Item label="阶段">
              <Tag color={getStageColor(lead.lead_stage)}>{lead.lead_stage}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="来源">{lead.lead_source || '-'}</Descriptions.Item>
            <Descriptions.Item label="产品">{lead.products && lead.products.length > 0 ? lead.products.map((p: string) => <Tag key={p} color="blue">{p}</Tag>) : '-'}</Descriptions.Item>
            <Descriptions.Item label="终端客户">{lead.terminal_customer_name}</Descriptions.Item>
            <Descriptions.Item label="负责人">
              <UserOutlined style={{ marginRight: 4 }} />
              {lead.sales_owner_name}
            </Descriptions.Item>
            <Descriptions.Item label="联系人">{lead.contact_person || '-'}</Descriptions.Item>
            <Descriptions.Item label="联系电话">
              <PhoneOutlined style={{ marginRight: 4 }} />
              {lead.contact_phone || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="预计预算">{lead.estimated_budget ? `¥${lead.estimated_budget.toLocaleString()}` : '-'}</Descriptions.Item>
            <Descriptions.Item label="需求确认">{lead.has_confirmed_requirement ? <Tag color="green">已确认</Tag> : <Tag>未确认</Tag>}</Descriptions.Item>
            <Descriptions.Item label="预算确认">{lead.has_confirmed_budget ? <Tag color="green">已确认</Tag> : <Tag>未确认</Tag>}</Descriptions.Item>
            <Descriptions.Item label="来源渠道">{lead.source_channel_name || '-'}</Descriptions.Item>
            <Descriptions.Item label="协同渠道">{lead.channel_name || '-'}</Descriptions.Item>
            <Descriptions.Item label="转化状态">
              {lead.converted_to_opportunity ? <Tag color="green">已转商机</Tag> : <Tag color="blue">跟进中</Tag>}
            </Descriptions.Item>
            <Descriptions.Item label="备注" span={4}>{lead.notes || '-'}</Descriptions.Item>
          </Descriptions>
        </Card>

        <Card title={`跟进记录 (${followUps.length})`} style={{ marginBottom: 16 }}>
          <Table
            columns={followUpColumns}
            dataSource={followUps}
            rowKey="id"
            loading={followUpsLoading}
            pagination={{ pageSize: 10 }}
            size="small"
          />
        </Card>

        <Card title="派工历史">
          <DispatchHistoryTable lead_id={Number(id)} />
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
          lead_id={Number(id)}
          terminal_customer_id={lead.terminal_customer_id}
        />
    </PageScaffold>
  );
};

export default LeadFullViewPage;
