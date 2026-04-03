import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Descriptions, Tag, Table, Spin, Button, Space, Typography, Tabs, Progress } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useContract } from '../hooks/useContracts';

const { Title } = Typography;

const ContractFullViewPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: contract, isLoading } = useContract(Number(id));

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!contract) {
    return <div>未找到合同信息</div>;
  }

  const getStatusConfig = (status: string) => {
    const configs: Record<string, { label: string; color: string }> = {
      'draft': { label: '草稿', color: 'default' },
      'pending': { label: '审批中', color: 'processing' },
      'signed': { label: '已签署', color: 'success' },
      'archived': { label: '已归档', color: 'cyan' },
      'rejected': { label: '已驳回', color: 'error' },
    };
    return configs[status] || configs['draft'];
  };

  const productColumns = [
    { title: '产品名称', dataIndex: 'product_name', key: 'product_name' },
    { title: '数量', dataIndex: 'quantity', key: 'quantity', width: 80 },
    { title: '单价', dataIndex: 'unit_price', key: 'unit_price', render: (v: number) => v ? `¥${v.toLocaleString()}` : '-' },
    { title: '折扣', dataIndex: 'discount', key: 'discount', width: 80, render: (v: number) => v ? `${(v * 100).toFixed(0)}%` : '100%' },
    { title: '金额', dataIndex: 'amount', key: 'amount', render: (v: number) => v ? `¥${v.toLocaleString()}` : '-' },
    { title: '备注', dataIndex: 'notes', key: 'notes', ellipsis: true },
  ];

  const paymentColumns = [
    { title: '阶段', dataIndex: 'plan_stage', key: 'plan_stage', width: 100 },
    { title: '计划金额', dataIndex: 'plan_amount', key: 'plan_amount', render: (v: number) => v ? `¥${v.toLocaleString()}` : '-' },
    { title: '计划日期', dataIndex: 'plan_date', key: 'plan_date', width: 110 },
    { title: '实际金额', dataIndex: 'actual_amount', key: 'actual_amount', render: (v: number) => v ? `¥${v.toLocaleString()}` : '-' },
    { title: '实际日期', dataIndex: 'actual_date', key: 'actual_date', width: 110 },
    { title: '状态', dataIndex: 'payment_status', key: 'payment_status', width: 80, render: (s: string) => {
      const colors: Record<string, string> = { 'pending': 'default', 'partial': 'processing', 'completed': 'success' };
      const labels: Record<string, string> = { 'pending': '待付款', 'partial': '部分付款', 'completed': '已完成' };
      return <Tag color={colors[s] || 'default'}>{labels[s] || s}</Tag>;
    }},
  ];

  const totalPlanAmount = contract.payment_plans?.reduce((sum: number, p: any) => sum + (p.plan_amount || 0), 0) || 0;
  const totalActualAmount = contract.payment_plans?.reduce((sum: number, p: any) => sum + (p.actual_amount || 0), 0) || 0;
  const paymentProgress = totalPlanAmount > 0 ? Math.round((totalActualAmount / totalPlanAmount) * 100) : 0;

  const tabItems = [
    {
      key: 'products',
      label: `产品清单 (${contract.products?.length || 0})`,
      children: (
        <Table
          columns={productColumns}
          dataSource={contract.products || []}
          rowKey="id"
          pagination={false}
          size="small"
          summary={() => (
            <Table.Summary.Row>
              <Table.Summary.Cell index={0} colSpan={4}><strong>合计</strong></Table.Summary.Cell>
              <Table.Summary.Cell index={4}>
                <strong>¥{(contract.products || []).reduce((sum: number, p: any) => sum + (p.amount || 0), 0).toLocaleString()}</strong>
              </Table.Summary.Cell>
              <Table.Summary.Cell index={5} />
            </Table.Summary.Row>
          )}
        />
      ),
    },
    {
      key: 'payments',
      label: `付款计划 (${contract.payment_plans?.length || 0})`,
      children: (
        <>
          {contract.contract_direction === 'Downstream' && (
            <Card size="small" style={{ marginBottom: 16 }}>
              <Space size="large">
                <span>回款进度：</span>
                <Progress percent={paymentProgress} style={{ width: 200 }} />
                <span>¥{totalActualAmount.toLocaleString()} / ¥{totalPlanAmount.toLocaleString()}</span>
              </Space>
            </Card>
          )}
          <Table
            columns={paymentColumns}
            dataSource={contract.payment_plans || []}
            rowKey="id"
            pagination={false}
            size="small"
          />
        </>
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
            {contract.contract_name}
            <Tag color="blue" style={{ marginLeft: 8 }}>{contract.contract_code}</Tag>
          </Title>
        </Space>

        <Card title="合同基本信息" style={{ marginBottom: 16 }} size="small">
          <Descriptions column={4} bordered size="small">
            <Descriptions.Item label="合同编号">{contract.contract_code}</Descriptions.Item>
            <Descriptions.Item label="合同名称">{contract.contract_name}</Descriptions.Item>
            <Descriptions.Item label="合同类型">
              <Tag color={contract.contract_direction === 'Downstream' ? 'blue' : 'orange'}>
                {contract.contract_direction === 'Downstream' ? '下游合同' : '上游合同'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="合同状态">
              <Tag color={getStatusConfig(contract.contract_status).color}>
                {getStatusConfig(contract.contract_status).label}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="合同金额">¥{contract.contract_amount?.toLocaleString() || 0}</Descriptions.Item>
            <Descriptions.Item label="签订日期">{contract.signing_date || '-'}</Descriptions.Item>
            <Descriptions.Item label="生效日期">{contract.effective_date || '-'}</Descriptions.Item>
            <Descriptions.Item label="到期日期">{contract.expiry_date || '-'}</Descriptions.Item>
            <Descriptions.Item label="关联项目">{contract.project_id || '-'}</Descriptions.Item>
            <Descriptions.Item label="终端客户">{contract.terminal_customer_id || '-'}</Descriptions.Item>
            <Descriptions.Item label="渠道/供应商">{contract.channel_id || '-'}</Descriptions.Item>
            <Descriptions.Item label="备注" span={4}>{contract.notes || '-'}</Descriptions.Item>
          </Descriptions>
        </Card>

        <Card title="合同详情">
          <Tabs items={tabItems} />
        </Card>
      </Card>
    </div>
  );
};

export default ContractFullViewPage;