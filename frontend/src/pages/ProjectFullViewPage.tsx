import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Descriptions, Tag, Table, Spin, Button, Space, Typography, Tabs, message } from 'antd';
import { ArrowLeftOutlined, UserOutlined, ToolOutlined } from '@ant-design/icons';
import { useQueryClient } from '@tanstack/react-query';
import { useProject } from '../hooks/useProjects';
import { useFollowUps } from '../hooks/useFollowUps';
import { useContracts } from '../hooks/useContracts';
import { useCreateDispatchFromProject } from '../hooks/useDispatch';
import DispatchModal from '../components/common/DispatchModal';
import DispatchHistoryTable from '../components/dispatch/DispatchHistoryTable';

const { Title } = Typography;

const ProjectFullViewPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: project, isLoading: projectLoading } = useProject(Number(id));
  const { data: followUps = [], isLoading: followUpsLoading } = useFollowUps({ project_id: Number(id) });
  const { data: contracts = [], isLoading: contractsLoading } = useContracts(Number(id));
  const { mutate: createDispatch, isPending: dispatchLoading } = useCreateDispatchFromProject();
  const [dispatchModalVisible, setDispatchModalVisible] = useState(false);

  if (projectLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!project) {
    return <div>未找到项目信息</div>;
  }

  const handleCreateDispatch = async (data: { technicianId: number; startDate: string; startPeriod: string; endDate: string; endPeriod: string; workType: string }) => {
    try {
      await createDispatch({ 
        entityId: Number(id), 
        technicianId: data.technicianId,
        startDate: data.startDate,
        startPeriod: data.startPeriod,
        endDate: data.endDate,
        endPeriod: data.endPeriod,
        workType: data.workType
      });
      message.success('派工创建成功！派工历史已更新');
      queryClient.invalidateQueries({ queryKey: ['dispatch-records'] });
    } catch (error: any) {
      message.error(error.message || '派工创建失败');
    }
  };

  const dispatchInfo = {
    customer_name: project.terminal_customer_name,
    contact: project.sales_owner_name,
    phone: undefined,
    entity_name: project.project_name,
    entity_type: '项目',
  };

  const followUpColumns = [
    { title: '跟进日期', dataIndex: 'follow_up_date', key: 'follow_up_date', width: 120 },
    { title: '跟进方式', dataIndex: 'follow_up_method', key: 'follow_up_method', width: 100 },
    { title: '跟进内容', dataIndex: 'follow_up_content', key: 'follow_up_content', ellipsis: true },
    { title: '跟进结论', dataIndex: 'follow_up_conclusion', key: 'follow_up_conclusion', width: 100, render: (s: string) => <Tag color="blue">{s}</Tag> },
    { title: '下次行动', dataIndex: 'next_action', key: 'next_action', ellipsis: true },
    { title: '跟进人', dataIndex: 'follower_name', key: 'follower_name', width: 100 },
  ];

  const contractColumns = [
    { title: '合同编号', dataIndex: 'contract_code', key: 'contract_code', width: 180 },
    { title: '合同名称', dataIndex: 'contract_name', key: 'contract_name' },
    { title: '类型', dataIndex: 'contract_direction', key: 'contract_direction', width: 80, render: (d: string) => <Tag color={d === 'Downstream' ? 'blue' : 'orange'}>{d === 'Downstream' ? '下游' : '上游'}</Tag> },
    { title: '状态', dataIndex: 'contract_status', key: 'contract_status', width: 80, render: (s: string) => <Tag>{s}</Tag> },
    { title: '金额', dataIndex: 'contract_amount', key: 'contract_amount', render: (v: number) => v ? `¥${v.toLocaleString()}` : '-' },
    { title: '签订日期', dataIndex: 'signing_date', key: 'signing_date', width: 110 },
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
      key: 'contracts',
      label: `关联合同 (${contracts.length})`,
      children: (
        <Table
          columns={contractColumns}
          dataSource={contracts}
          rowKey="id"
          loading={contractsLoading}
          pagination={{ pageSize: 10 }}
          size="small"
        />
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
            {project.project_name}
            <Tag color="blue" style={{ marginLeft: 8 }}>{project.project_code}</Tag>
          </Title>
          <Button 
            icon={<ToolOutlined />} 
            type="primary"
            onClick={() => setDispatchModalVisible(true)}
          >
            新增派工
          </Button>
        </Space>

        <Card title="项目基本信息" style={{ marginBottom: 16 }} size="small">
          <Descriptions column={4} bordered size="small">
            <Descriptions.Item label="项目编号">{project.project_code}</Descriptions.Item>
            <Descriptions.Item label="项目名称">{project.project_name}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color="blue">{project.project_status}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="业务类型">{project.business_type}</Descriptions.Item>
            <Descriptions.Item label="终端客户">{project.terminal_customer_name || '-'}</Descriptions.Item>
            <Descriptions.Item label="负责人">
              <UserOutlined style={{ marginRight: 4 }} />
              {project.sales_owner_name || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="下游合同金额">{project.downstream_contract_amount ? `¥${project.downstream_contract_amount.toLocaleString()}` : '-'}</Descriptions.Item>
            <Descriptions.Item label="上游采购金额">{project.upstream_procurement_amount ? `¥${project.upstream_procurement_amount.toLocaleString()}` : '-'}</Descriptions.Item>
            <Descriptions.Item label="毛利率">{project.gross_margin ? `¥${project.gross_margin.toLocaleString()}` : '-'}</Descriptions.Item>
            <Descriptions.Item label="项目描述" span={3}>{project.notes || '-'}</Descriptions.Item>
          </Descriptions>
        </Card>

        <Card title="关联信息">
          <Tabs items={tabItems} />
        </Card>

        <Card title="派工历史" style={{ marginTop: 16 }}>
          <DispatchHistoryTable project_id={Number(id)} />
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

export default ProjectFullViewPage;