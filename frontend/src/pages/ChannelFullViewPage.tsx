import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Descriptions, Tag, Table, Tabs, Spin, Button, Space, Statistic, Row, Col, Typography } from 'antd';
import { ArrowLeftOutlined, ShopOutlined, PhoneOutlined, MailOutlined, GlobalOutlined, EnvironmentOutlined } from '@ant-design/icons';
import { useChannelFullView } from '../hooks/useChannelFullView';

const { Title } = Typography;

const ChannelFullViewPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, isLoading } = useChannelFullView(Number(id));

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!data) {
    return <div>未找到渠道信息</div>;
  }

  const getStatusColor = (status: string) => {
    return status === '合作中' ? 'green' : 'default';
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

  const customerColumns = [
    { title: '客户编号', dataIndex: 'customer_code', key: 'customer_code', width: 180 },
    { title: '客户名称', dataIndex: 'customer_name', key: 'customer_name' },
    { title: '行业', dataIndex: 'customer_industry', key: 'customer_industry' },
    { title: '区域', dataIndex: 'customer_region', key: 'customer_region' },
    { title: '状态', dataIndex: 'customer_status', key: 'customer_status', render: (s: string) => <Tag color="blue">{s}</Tag> },
    { title: '负责人', dataIndex: 'customer_owner_name', key: 'customer_owner_name' },
  ];

  const opportunityColumns = [
    { title: '商机编号', dataIndex: 'opportunity_code', key: 'opportunity_code', width: 180 },
    { title: '商机名称', dataIndex: 'opportunity_name', key: 'opportunity_name' },
    { title: '阶段', dataIndex: 'opportunity_stage', key: 'opportunity_stage', render: (s: string) => <Tag color={getOppStageColor(s)}>{s}</Tag> },
    { title: '预计金额', dataIndex: 'expected_contract_amount', key: 'expected_contract_amount', render: (v: number) => v ? `¥${v.toLocaleString()}` : '-' },
    { title: '终端客户', dataIndex: 'terminal_customer_name', key: 'terminal_customer_name' },
    { title: '负责人', dataIndex: 'sales_owner_name', key: 'sales_owner_name' },
    { title: '项目', dataIndex: 'project_id', key: 'project_id', render: (v: number) => v ? <Tag color="blue">已转项目</Tag> : '-' },
  ];

  const projectColumns = [
    { title: '项目编号', dataIndex: 'project_code', key: 'project_code', width: 180 },
    { title: '项目名称', dataIndex: 'project_name', key: 'project_name' },
    { title: '状态', dataIndex: 'project_status', key: 'project_status', render: (s: string) => <Tag color="blue">{s}</Tag> },
    { title: '业务类型', dataIndex: 'business_type', key: 'business_type' },
    { title: '合同金额', dataIndex: 'downstream_contract_amount', key: 'downstream_contract_amount', render: (v: number) => v ? `¥${v.toLocaleString()}` : '-' },
    { title: '终端客户', dataIndex: 'terminal_customer_name', key: 'terminal_customer_name' },
    { title: '负责人', dataIndex: 'sales_owner_name', key: 'sales_owner_name' },
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
      key: 'customers',
      label: `关联客户 (${data.summary.customers_count})`,
      children: (
        <Table
          columns={customerColumns}
          dataSource={data.customers}
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
            <ShopOutlined style={{ marginRight: 8 }} />
            {data.channel.company_name}
            <Tag color="blue" style={{ marginLeft: 8 }}>{data.channel.channel_code}</Tag>
          </Title>
        </Space>

        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="关联客户数"
                value={data.summary.customers_count}
                prefix={<ShopOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="商机数"
                value={data.summary.opportunities_count}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="项目数"
                value={data.summary.projects_count}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="合同数"
                value={data.summary.contracts_count}
              />
            </Card>
          </Col>
        </Row>

        <Card title="渠道基本信息" style={{ marginBottom: 16 }} size="small">
          <Descriptions column={4} bordered size="small">
            <Descriptions.Item label="渠道编号">{data.channel.channel_code}</Descriptions.Item>
            <Descriptions.Item label="公司名称">{data.channel.company_name}</Descriptions.Item>
            <Descriptions.Item label="类型">{data.channel.channel_type}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={getStatusColor(data.channel.status)}>{data.channel.status}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="主要联系人">{data.channel.main_contact || '-'}</Descriptions.Item>
            <Descriptions.Item label="电话">
              <PhoneOutlined style={{ marginRight: 4 }} />
              {data.channel.phone || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="邮箱">
              <MailOutlined style={{ marginRight: 4 }} />
              {data.channel.email || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="统一社会信用代码">{data.channel.credit_code || '-'}</Descriptions.Item>
            <Descriptions.Item label="省份">{data.channel.province || '-'}</Descriptions.Item>
            <Descriptions.Item label="城市">{data.channel.city || '-'}</Descriptions.Item>
            <Descriptions.Item label="详细地址" span={2}>
              <EnvironmentOutlined style={{ marginRight: 4 }} />
              {data.channel.address || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="官网">
              {data.channel.website ? (
                <a href={data.channel.website} target="_blank" rel="noopener noreferrer">
                  <GlobalOutlined style={{ marginRight: 4 }} />
                  {data.channel.website}
                </a>
              ) : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="微信公众号">{data.channel.wechat || '-'}</Descriptions.Item>
            <Descriptions.Item label="合作区域">{data.channel.cooperation_region || '-'}</Descriptions.Item>
            <Descriptions.Item label="折扣率">{data.channel.discount_rate ? `${(data.channel.discount_rate * 100).toFixed(2)}%` : '-'}</Descriptions.Item>
            <Descriptions.Item label="备注" span={4}>{data.channel.notes || '-'}</Descriptions.Item>
          </Descriptions>
        </Card>

        <Card title="关联信息">
          <Tabs items={tabItems} />
        </Card>
      </Card>
    </div>
  );
};

export default ChannelFullViewPage;