import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Descriptions, Tag, Table, Tabs, Spin, Button, Space, Statistic, Row, Col, Typography } from 'antd';
import { ArrowLeftOutlined, UserOutlined, ShopOutlined, PhoneOutlined, FileTextOutlined } from '@ant-design/icons';
import { useCustomerFullView } from '../hooks/useCustomerFullView';

const { Title } = Typography;

const CustomerFullViewPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, isLoading } = useCustomerFullView(Number(id));

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!data) {
    return <div>未找到客户信息</div>;
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      '意向客户': 'blue',
      '潜在客户': 'cyan',
      '成交客户': 'green',
      '流失客户': 'red',
    };
    return colors[status] || 'default';
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

  const getOppStageColor = (stage: string) => {
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

  const leadColumns = [
    { title: '线索编号', dataIndex: 'lead_code', key: 'lead_code', width: 180 },
    { title: '线索名称', dataIndex: 'lead_name', key: 'lead_name' },
    { title: '阶段', dataIndex: 'lead_stage', key: 'lead_stage', render: (s: string) => <Tag color={getStageColor(s)}>{s}</Tag> },
    { title: '来源', dataIndex: 'lead_source', key: 'lead_source' },
    { title: '预计预算', dataIndex: 'estimated_budget', key: 'estimated_budget', render: (v: number) => v ? `¥${v.toLocaleString()}` : '-' },
    { title: '负责人', dataIndex: 'sales_owner_name', key: 'sales_owner_name' },
    { title: '状态', dataIndex: 'converted_to_opportunity', key: 'converted_to_opportunity', render: (v: boolean) => v ? <Tag color="green">已转化</Tag> : <Tag color="blue">跟进中</Tag> },
  ];

  const opportunityColumns = [
    { title: '商机编号', dataIndex: 'opportunity_code', key: 'opportunity_code', width: 180 },
    { title: '商机名称', dataIndex: 'opportunity_name', key: 'opportunity_name' },
    { title: '阶段', dataIndex: 'opportunity_stage', key: 'opportunity_stage', render: (s: string) => <Tag color={getOppStageColor(s)}>{s}</Tag> },
    { title: '预计金额', dataIndex: 'expected_contract_amount', key: 'expected_contract_amount', render: (v: number) => v ? `¥${v.toLocaleString()}` : '-' },
    { title: '负责人', dataIndex: 'sales_owner_name', key: 'sales_owner_name' },
    { title: '渠道', dataIndex: 'channel_name', key: 'channel_name', render: (v: string) => v || '-' },
    { title: '项目', dataIndex: 'project_id', key: 'project_id', render: (v: number) => v ? <Tag color="blue">已转项目</Tag> : '-' },
  ];

  const projectColumns = [
    { title: '项目编号', dataIndex: 'project_code', key: 'project_code', width: 180 },
    { title: '项目名称', dataIndex: 'project_name', key: 'project_name' },
    { title: '状态', dataIndex: 'project_status', key: 'project_status', render: (s: string) => <Tag color="blue">{s}</Tag> },
    { title: '业务类型', dataIndex: 'business_type', key: 'business_type' },
    { title: '合同金额', dataIndex: 'downstream_contract_amount', key: 'downstream_contract_amount', render: (v: number) => v ? `¥${v.toLocaleString()}` : '-' },
    { title: '负责人', dataIndex: 'sales_owner_name', key: 'sales_owner_name' },
  ];

  const followUpColumns = [
    { title: '跟进日期', dataIndex: 'follow_up_date', key: 'follow_up_date', width: 120 },
    { title: '方式', dataIndex: 'follow_up_method', key: 'follow_up_method', width: 80 },
    { title: '内容', dataIndex: 'follow_up_content', key: 'follow_up_content', ellipsis: true },
    { title: '结论', dataIndex: 'follow_up_conclusion', key: 'follow_up_conclusion', width: 80, render: (s: string) => <Tag color="blue">{s}</Tag> },
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
      key: 'leads',
      label: `线索 (${data.summary.leads_count})`,
      children: (
        <Table
          columns={leadColumns}
          dataSource={data.leads}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          size="small"
        />
      ),
    },
    {
      key: 'opportunities',
      label: `商机 (${data.summary.opportunities_count})`,
      children: (
        <Table
          columns={opportunityColumns}
          dataSource={data.opportunities}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          size="small"
        />
      ),
    },
    {
      key: 'projects',
      label: `项目 (${data.summary.projects_count})`,
      children: (
        <Table
          columns={projectColumns}
          dataSource={data.projects}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          size="small"
        />
      ),
    },
    {
      key: 'follow_ups',
      label: `跟进记录 (${data.summary.follow_ups_count})`,
      children: (
        <Table
          columns={followUpColumns}
          dataSource={data.follow_ups}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          size="small"
        />
      ),
    },
    {
      key: 'contracts',
      label: `合同 (${data.summary.contracts_count})`,
      children: (
        <Table
          columns={contractColumns}
          dataSource={data.contracts}
          rowKey="id"
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
            {data.customer.customer_name}
            <Tag color="blue" style={{ marginLeft: 8 }}>{data.customer.customer_code}</Tag>
          </Title>
        </Space>

        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="线索数"
                value={data.summary.leads_count}
                prefix={<FileTextOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="商机数"
                value={data.summary.opportunities_count}
                prefix={<ShopOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="项目数"
                value={data.summary.projects_count}
                prefix={<FileTextOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="合同数"
                value={data.summary.contracts_count}
                prefix={<FileTextOutlined />}
              />
            </Card>
          </Col>
        </Row>

        <Card title="客户基本信息" style={{ marginBottom: 16 }} size="small">
          <Descriptions column={4} bordered size="small">
            <Descriptions.Item label="客户编号">{data.customer.customer_code}</Descriptions.Item>
            <Descriptions.Item label="客户名称">{data.customer.customer_name}</Descriptions.Item>
            <Descriptions.Item label="统一社会信用代码">{data.customer.credit_code}</Descriptions.Item>
            <Descriptions.Item label="行业">{data.customer.customer_industry}</Descriptions.Item>
            <Descriptions.Item label="区域">{data.customer.customer_region}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={getStatusColor(data.customer.customer_status)}>{data.customer.customer_status}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="负责人">
              <UserOutlined style={{ marginRight: 4 }} />
              {data.customer.customer_owner_name}
            </Descriptions.Item>
            <Descriptions.Item label="主要联系人">{data.customer.main_contact || '-'}</Descriptions.Item>
            <Descriptions.Item label="电话">
              <PhoneOutlined style={{ marginRight: 4 }} />
              {data.customer.phone || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="备注" span={3}>{data.customer.notes || '-'}</Descriptions.Item>
          </Descriptions>
        </Card>

        {data.channel && (
          <Card title="关联渠道" style={{ marginBottom: 16 }} size="small">
            <Descriptions column={4} bordered size="small">
              <Descriptions.Item label="渠道编号">{data.channel.channel_code}</Descriptions.Item>
              <Descriptions.Item label="公司名称">{data.channel.company_name}</Descriptions.Item>
              <Descriptions.Item label="类型">{data.channel.channel_type}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={data.channel.status === '合作中' ? 'green' : 'default'}>{data.channel.status}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="主要联系人">{data.channel.main_contact || '-'}</Descriptions.Item>
              <Descriptions.Item label="电话">{data.channel.phone || '-'}</Descriptions.Item>
            </Descriptions>
          </Card>
        )}

        <Card title="关联信息">
          <Tabs items={tabItems} />
        </Card>
      </Card>
    </div>
  );
};

export default CustomerFullViewPage;