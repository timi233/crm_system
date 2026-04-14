import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Descriptions, Tag, Table, Spin, Button, Space, Typography, message } from 'antd';
import { ArrowLeftOutlined, UserOutlined, PhoneOutlined, ToolOutlined } from '@ant-design/icons';
import { useQueryClient } from '@tanstack/react-query';
import { useLead } from '../hooks/useLeads';
import { useFollowUps } from '../hooks/useFollowUps';
import { useCreateDispatchFromLead } from '../hooks/useDispatch';
import DispatchModal from '../components/common/DispatchModal';
import DispatchHistoryTable from '../components/dispatch/DispatchHistoryTable';

const { Title } = Typography;

const LeadFullViewPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: lead, isLoading: leadLoading } = useLead(Number(id));
  const { data: followUps = [], isLoading: followUpsLoading } = useFollowUps({ lead_id: Number(id) });
  const { mutateAsync: createDispatch, isPending: dispatchLoading } = useCreateDispatchFromLead();
  const [dispatchModalVisible, setDispatchModalVisible] = useState(false);

  if (leadLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!lead) {
    return <div>未找到线索信息</div>;
  }

  const handleCreateDispatch = async (data: { technicianId: number; startDate: string; startPeriod: string; endDate: string; endPeriod: string; workType: string; serviceMode: 'online' | 'offline' }) => {
    try {
      await createDispatch({ 
        entityId: Number(id), 
        technicianId: data.technicianId,
        startDate: data.startDate,
        startPeriod: data.startPeriod,
        endDate: data.endDate,
        endPeriod: data.endPeriod,
        workType: data.workType,
        serviceMode: data.serviceMode
      });
      message.success('派工创建成功！派工历史已更新');
      queryClient.invalidateQueries({ queryKey: ['dispatch-records'] });
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
    <div style={{ padding: 24 }}>
      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>
            返回
          </Button>
          <Title level={4} style={{ margin: 0 }}>
            {lead.lead_name}
            <Tag color="blue" style={{ marginLeft: 8 }}>{lead.lead_code}</Tag>
          </Title>
          <Button 
            icon={<ToolOutlined />} 
            type="primary"
            onClick={() => setDispatchModalVisible(true)}
            disabled={lead.converted_to_opportunity}
          >
            新增派工
          </Button>
        </Space>

        <Card title="线索基本信息" style={{ marginBottom: 16 }} size="small">
          <Descriptions column={4} bordered size="small">
            <Descriptions.Item label="线索编号">{lead.lead_code}</Descriptions.Item>
            <Descriptions.Item label="线索名称">{lead.lead_name}</Descriptions.Item>
            <Descriptions.Item label="阶段">
              <Tag color={getStageColor(lead.lead_stage)}>{lead.lead_stage}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="来源">{lead.lead_source || '-'}</Descriptions.Item>
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
            <Descriptions.Item label="转化状态">
              {lead.converted_to_opportunity ? <Tag color="green">已转商机</Tag> : <Tag color="blue">跟进中</Tag>}
            </Descriptions.Item>
            <Descriptions.Item label="备注" span={4}>{lead.notes || '-'}</Descriptions.Item>
          </Descriptions>
        </Card>

        <Card title={`跟进记录 (${followUps.length})`}>
          <Table
            columns={followUpColumns}
            dataSource={followUps}
            rowKey="id"
            loading={followUpsLoading}
            pagination={{ pageSize: 10 }}
            size="small"
          />
        </Card>

        <Card title="派工历史" style={{ marginTop: 16 }}>
          <DispatchHistoryTable lead_id={Number(id)} />
        </Card>
      </Card>

      <DispatchModal
        visible={dispatchModalVisible}
        onClose={() => setDispatchModalVisible(false)}
        onSubmit={handleCreateDispatch}
        loading={dispatchLoading}
        dispatchInfo={dispatchInfo}
      />
    </div>
  );
};

export default LeadFullViewPage;