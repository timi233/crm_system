import React from 'react';
import { Card, Row, Col, Statistic, Table, Skeleton, DatePicker, Typography, Progress, Select, Space, Result } from 'antd';
import { DollarOutlined, TeamOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { usePerformance } from '../hooks/useReports';
import { useUsers } from '../hooks/useUsers';

const { Title } = Typography;
const { RangePicker } = DatePicker;

const PerformanceReport: React.FC = () => {
  const [dates, setDates] = React.useState<[string, string] | undefined>();
  const [salesOwnerId, setSalesOwnerId] = React.useState<number | undefined>();
  const { data, isLoading } = usePerformance(dates?.[0], dates?.[1], salesOwnerId);
  const { data: users } = useUsers();

  if (isLoading || !data) {
    return (
      <div style={{ padding: 24 }}>
        <Skeleton active paragraph={{ rows: 10 }} />
      </div>
    );
  }

  const barOption = {
    title: { text: '销售人员业绩对比', left: 'center' },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['合同金额', '已回款金额', '待回款金额'], top: 30 },
    xAxis: { type: 'category', data: data.by_user.map(u => u.user_name) },
    yAxis: { type: 'value', name: '金额 (元)' },
    series: [
      {
        name: '合同金额',
        type: 'bar',
        data: data.by_user.map(u => u.contract_amount),
        itemStyle: { color: '#1890ff' },
      },
      {
        name: '已回款金额',
        type: 'bar',
        data: data.by_user.map(u => u.received_amount),
        itemStyle: { color: '#52c41a' },
      },
      {
        name: '待回款金额',
        type: 'bar',
        data: data.by_user.map(u => u.pending_amount),
        itemStyle: { color: '#faad14' },
      },
    ],
  };

  const lineOption = {
    title: { text: '月度合同趋势', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: data.by_month.map(m => m.month) },
    yAxis: [
      { type: 'value', name: '金额 (元)' },
      { type: 'value', name: '数量', position: 'right' },
    ],
    series: [
      {
        name: '合同金额',
        type: 'line',
        data: data.by_month.map(m => m.contract_amount),
        smooth: true,
        itemStyle: { color: '#1890ff' },
        areaStyle: { opacity: 0.3 },
      },
      {
        name: '合同数量',
        type: 'bar',
        yAxisIndex: 1,
        data: data.by_month.map(m => m.contract_count),
        itemStyle: { color: '#52c41a', opacity: 0.5 },
      },
    ],
  };

  const columns = [
    { title: '销售人员', dataIndex: 'user_name', key: 'user_name' },
    { title: '合同数量', dataIndex: 'contract_count', key: 'contract_count' },
    { 
      title: '合同金额', 
      dataIndex: 'contract_amount', 
      key: 'contract_amount',
      render: (v: number) => `¥${v?.toLocaleString() || 0}`,
    },
    { 
      title: '已回款金额', 
      dataIndex: 'received_amount', 
      key: 'received_amount',
      render: (v: number) => `¥${v?.toLocaleString() || 0}`,
    },
    { 
      title: '待回款金额', 
      dataIndex: 'pending_amount', 
      key: 'pending_amount',
      render: (v: number) => `¥${v?.toLocaleString() || 0}`,
    },
    {
      title: '回款进度',
      dataIndex: 'gross_margin',
      key: 'gross_margin',
      render: (_: number, record) => {
        const progress = record.contract_amount > 0 
          ? Math.round((record.received_amount / record.contract_amount) * 100) 
          : 0;
        return <Progress percent={progress} size="small" />;
      },
    },
  ];

  const totalProgress = data.total_contract_amount > 0
    ? Math.round((data.total_received_amount / data.total_contract_amount) * 100)
    : 0;

  return (
    <div style={{ padding: 24 }}>
      <Card>
        <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
          <Title level={4} style={{ margin: 0 }}>业绩统计报表</Title>
          <Space>
            <Select
              allowClear
              placeholder="选择销售人员"
              style={{ width: 200 }}
              value={salesOwnerId}
              onChange={(value) => setSalesOwnerId(value)}
              options={users?.map(u => ({ label: u.name, value: u.id }))}
            />
            <RangePicker onChange={(dates) => {
              if (dates && dates[0] && dates[1]) {
                setDates([dates[0].format('YYYY-MM-DD'), dates[1].format('YYYY-MM-DD')]);
              } else {
                setDates(undefined);
              }
            }} />
          </Space>
        </Row>

        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic 
                title="合同总金额" 
                value={data.total_contract_amount} 
                prefix={<DollarOutlined />} 
                precision={0}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic 
                title="已回款总额" 
                value={data.total_received_amount} 
                prefix="¥" 
                precision={0}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic 
                title="待回款总额" 
                value={data.total_pending_amount} 
                prefix="¥" 
                precision={0}
                valueStyle={{ color: '#cf1322' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <div style={{ marginBottom: 8 }}>整体回款进度</div>
              <Progress type="circle" percent={totalProgress} />
            </Card>
          </Col>
        </Row>

        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={24}>
            <ReactECharts option={barOption} style={{ height: 350 }} />
          </Col>
        </Row>

        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={24}>
            <ReactECharts option={lineOption} style={{ height: 350 }} />
          </Col>
        </Row>

        <Card title="销售人员业绩明细">
          <Table 
            columns={columns} 
            dataSource={data.by_user} 
            rowKey="user_id" 
            pagination={false}
            summary={() => (
              <Table.Summary.Row>
                <Table.Summary.Cell index={0}><strong>合计</strong></Table.Summary.Cell>
                <Table.Summary.Cell index={1}>
                  <strong>{data.by_user.reduce((sum, u) => sum + u.contract_count, 0)}</strong>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={2}>
                  <strong>¥{data.total_contract_amount.toLocaleString()}</strong>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={3}>
                  <strong>¥{data.total_received_amount.toLocaleString()}</strong>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={4}>
                  <strong>¥{data.total_pending_amount.toLocaleString()}</strong>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={5}>
                  <Progress percent={totalProgress} size="small" />
                </Table.Summary.Cell>
              </Table.Summary.Row>
            )}
          />
        </Card>
      </Card>
    </div>
  );
};

export default PerformanceReport;