import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { App, Card, Descriptions, Tag, Table, Skeleton, Button, Space, Typography, Tabs } from 'antd';
import { ArrowLeftOutlined, UserOutlined, ToolOutlined, CommentOutlined } from '@ant-design/icons';
import { useQueryClient } from '@tanstack/react-query';
import { useProject } from '../hooks/useProjects';
import { useFollowUps } from '../hooks/useFollowUps';
import { useContracts } from '../hooks/useContracts';
import { useCreateDispatchFromProject } from '../hooks/useDispatch';
import DispatchModal from '../components/common/DispatchModal';
import DispatchHistoryTable from '../components/dispatch/DispatchHistoryTable';
import FollowUpModal from '../components/modals/FollowUpModal';
import PageScaffold from '../components/common/PageScaffold';

const { Title } = Typography;

const ProjectFullViewPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { message } = App.useApp();
  const queryClient = useQueryClient();
  const { data: project, isLoading: projectLoading } = useProject(Number(id));
  const { data: followUps = [], isLoading: followUpsLoading } = useFollowUps({ project_id: Number(id) });
  const { data: contracts = [], isLoading: contractsLoading } = useContracts(Number(id));
  const { mutateAsync: createDispatch, isPending: dispatchLoading } = useCreateDispatchFromProject();
  const [dispatchModalVisible, setDispatchModalVisible] = useState(false);
  const [followUpModalVisible, setFollowUpModalVisible] = useState(false);

  if (projectLoading) {
    return <Skeleton active />;
  }

  if (!project) {
    return <div>未找到项目信息</div>;
  }

  const breadcrumbs = [
    { title: '首页', href: '/dashboard' },
    { title: '项目管理', href: '/projects' },
    { title: `项目 ${project.project_code}`, href: '#' },
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
    <PageScaffold
      title={project.project_name}
      breadcrumbItems={[
        { title: '首页', href: '/dashboard' },
        { title: '项目管理', href: '/projects' },
        { title: project.project_code },
      ]}
      extra={
        <Space size={12}>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>返回</Button>
          <Button
            icon={<ToolOutlined />}
            type="primary"
            className="btn--gradient"
            onClick={() => setDispatchModalVisible(true)}
          >
            新增派工
          </Button>
          <Button
            icon={<CommentOutlined />}
            onClick={() => setFollowUpModalVisible(true)}
          >
            新增跟进记录
          </Button>
        </Space>
      }
    >
      <div className="fade-in">
        <div style={{
          background: '#f8fafc',
          padding: '24px',
          borderRadius: '12px',
          border: '1px solid #f1f5f9',
          marginBottom: 24
        }}>
          <Descriptions
            title={<span style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a' }}>基本信息</span>}
            column={4}
            size="middle"
          >
            <Descriptions.Item label="项目编号"><span style={{ fontWeight: 600 }}>{project.project_code}</span></Descriptions.Item>
            <Descriptions.Item label="状态"><Tag color="blue" style={{ border: 'none' }}>{project.project_status}</Tag></Descriptions.Item>
            <Descriptions.Item label="业务类型">{project.business_type}</Descriptions.Item>
            <Descriptions.Item label="负责人"><Space size={4}><UserOutlined style={{ color: 'var(--primary-color)' }} />{project.sales_owner_name || '-'}</Space></Descriptions.Item>
            <Descriptions.Item label="终端客户"><span style={{ fontWeight: 600 }}>{project.terminal_customer_name || '-'}</span></Descriptions.Item>
            <Descriptions.Item label="下游合同金额">{project.downstream_contract_amount ? `¥${project.downstream_contract_amount.toLocaleString()}` : '-'}</Descriptions.Item>
            <Descriptions.Item label="上游采购金额">{project.upstream_procurement_amount ? `¥${project.upstream_procurement_amount.toLocaleString()}` : '-'}</Descriptions.Item>
            <Descriptions.Item label="毛利率">{project.gross_margin ? `¥${project.gross_margin.toLocaleString()}` : '-'}</Descriptions.Item>
            <Descriptions.Item label="产品" span={4}>{project.products && project.products.length > 0 ? project.products.map((p: string) => <Tag key={p} color="blue" style={{ border: 'none' }}>{p}</Tag>) : '-'}</Descriptions.Item>
            <Descriptions.Item label="项目描述" span={4}>{project.notes || '-'}</Descriptions.Item>
          </Descriptions>
        </div>

        <div className="modern-tabs-container">
          <Tabs items={tabItems} type="card" className="custom-tabs" />
        </div>

        <Card title="派工历史" className="card--tertiary" bodyStyle={{ padding: 0 }} style={{ marginTop: 24 }}>
          <div style={{ padding: '16px' }}>
            <DispatchHistoryTable project_id={Number(id)} />
          </div>
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
          project_id={Number(id)}
          terminal_customer_id={project.terminal_customer_id}
        />
      </div>
    </PageScaffold>
  );
};

export default ProjectFullViewPage;
