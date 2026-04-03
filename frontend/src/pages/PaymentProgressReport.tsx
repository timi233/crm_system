import React from 'react';
import { Card, Row, Col, Statistic, Table, Spin, DatePicker, Typography, Progress, Select, Space } from 'antd';
import { DollarOutlined, ExclamationCircleOutlined, CheckCircleOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { usePaymentProgress } from '../hooks/useReports';
import { useUsers } from '../hooks/useUsers';

const { Title } = Typography;
const { RangePicker } = DatePicker;

const PaymentProgressReport: React.FC = () => {
  const [dates, setDates] = React.useState<[string, string] | undefined>();
  const [salesOwnerId, setSalesOwnerId] = React.useState<number | undefined>();
  const { data, isLoading } = usePaymentProgress(dates?.[0], dates?.[1], salesOwnerId);
  const { data: users } = useUsers();

  if (isLoading || !data) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <Spin size="large" />
      </div>
    );
  }

  const gaugeOption = {
    series: [{
      type: 'gauge',
      startAngle: 180,
      endAngle: 0,
      min: 0,
      max: 100,
      radius: '100%',
      center: ['50%', '70%'],
      splitNumber: 10,
      axisLine: {
        lineStyle: {
          width: 20,
          color: [
            [0.3, '#ff4d4f'],
            [0.6, '#faad14'],
            [0.8, '#52c41a'],
            [1, '#1890ff'],
          ],
        },
      },
      pointer: { width: 5 },
      axisTick: { show: false },
      splitLine: { length: 15, lineStyle: { width: 2, color: '#999' } },
      axisLabel: { distance: 25, fontSize: 10 },
      detail: { valueAnimation: true, formatter: '{value}%', fontSize: 24, offsetCenter: [0, '20%'] },
      data: [{ value: data.progress_percentage, name: '回款进度' }],
    }],
  };

  const pieOption = {
    title: { text: '回款状态比例', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'item', formatter: '{b}: ¥{c} ({d}%)' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '55%'],
      data: [
        { value: data.total_actual_amount, name: '已回款', itemStyle: { color: '#52c41a' } },
        { value: data.total_pending_amount, name: '待回款', itemStyle: { color: '#faad14' } },
      ],
      label: { show: true, formatter: '{b}\n¥{c}' },
    }],
  };

  const columns = [
    { title: '合同编号', dataIndex: 'contract_code', key: 'contract_code', width: 180 },
    { title: '合同名称', dataIndex: 'contract_name', key: 'contract_name' },
    { 
      title: '合同金额', 
      dataIndex: 'contract_amount', 
      key: 'contract_amount',
      render: (v: number) => `¥${v?.toLocaleString() || 0}`,
    },
    { 
      title: '计划回款', 
      dataIndex: 'plan_amount', 
      key: 'plan_amount',
      render: (v: number) => `¥${v?.toLocaleString() || 0}`,
    },
    { 
      title: '已回款', 
      dataIndex: 'actual_amount', 
      key: 'actual_amount',
      render: (v: number) => `¥${v?.toLocaleString() || 0}`,
    },
    { 
      title: '待回款', 
      dataIndex: 'pending_amount', 
      key: 'pending_amount',
      render: (v: number) => `¥${v?.toLocaleString() || 0}`,
    },
    { 
      title: '逾期金额', 
      dataIndex: 'overdue_amount', 
      key: 'overdue_amount',
      render: (v: number) => v > 0 ? (
        <span style={{ color: '#ff4d4f' }}>¥{v.toLocaleString()}</span>
      ) : '-',
    },
    {
      title: '回款进度',
      dataIndex: 'progress_percentage',
      key: 'progress_percentage',
      width: 150,
      render: (v: number) => <Progress percent={v} size="small" />,
    },
    {
      title: '付款计划',
      key: 'payment_info',
      render: (_: any, record: any) => `${record.completed_count}/${record.payment_count}`,
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card>
        <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
          <Title level={4} style={{ margin: 0 }}>回款进度报表</Title>
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
          <Col span={4}>
            <Card>
              <Statistic 
                title="计划回款总额" 
                value={data.total_plan_amount} 
                prefix={<DollarOutlined />} 
                precision={0}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic 
                title="已回款总额" 
                value={data.total_actual_amount} 
                prefix="¥" 
                precision={0}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic 
                title="待回款总额" 
                value={data.total_pending_amount} 
                prefix="¥" 
                precision={0}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic 
                title="逾期金额" 
                value={data.overdue_amount} 
                prefix="¥" 
                precision={0}
                valueStyle={{ color: data.overdue_amount > 0 ? '#cf1322' : '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic 
                title="逾期合同数" 
                value={data.overdue_count} 
                prefix={<ExclamationCircleOutlined />}
                valueStyle={{ color: data.overdue_count > 0 ? '#cf1322' : '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic 
                title="合同总数" 
                value={data.contracts.length} 
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
        </Row>

        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={12}>
            <ReactECharts option={gaugeOption} style={{ height: 300 }} />
          </Col>
          <Col span={12}>
            <ReactECharts option={pieOption} style={{ height: 300 }} />
          </Col>
        </Row>

        <Card title="合同回款明细">
          <Table 
            columns={columns} 
            dataSource={data.contracts} 
            rowKey="contract_id" 
            pagination={{ pageSize: 10 }}
            summary={() => (
              <Table.Summary.Row>
                <Table.Summary.Cell index={0} colSpan={2}><strong>合计</strong></Table.Summary.Cell>
                <Table.Summary.Cell index={2}>
                  <strong>¥{data.contracts.reduce((sum, c) => sum + c.contract_amount, 0).toLocaleString()}</strong>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={3}>
                  <strong>¥{data.total_plan_amount.toLocaleString()}</strong>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={4}>
                  <strong>¥{data.total_actual_amount.toLocaleString()}</strong>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={5}>
                  <strong>¥{data.total_pending_amount.toLocaleString()}</strong>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={6}>
                  <strong style={{ color: '#cf1322' }}>¥{data.overdue_amount.toLocaleString()}</strong>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={7}>
                  <Progress percent={data.progress_percentage} size="small" />
                </Table.Summary.Cell>
                <Table.Summary.Cell index={8}>
                  {data.contracts.reduce((sum, c) => sum + c.completed_count, 0)}/{data.contracts.reduce((sum, c) => sum + c.payment_count, 0)}
                </Table.Summary.Cell>
              </Table.Summary.Row>
            )}
          />
        </Card>
      </Card>
    </div>
  );
};

export default PaymentProgressReport;