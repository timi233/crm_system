import React from 'react';
import { Card, Row, Col, Statistic, Table, Spin, DatePicker, Typography, Select, Space } from 'antd';
import { UserOutlined, TeamOutlined, FundProjectionScreenOutlined, FileDoneOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { useSalesFunnel } from '../hooks/useReports';
import { useUsers } from '../hooks/useUsers';

const { Title } = Typography;
const { RangePicker } = DatePicker;

const SalesFunnelReport: React.FC = () => {
  const [dates, setDates] = React.useState<[string, string] | undefined>();
  const [salesOwnerId, setSalesOwnerId] = React.useState<number | undefined>();
  const { data, isLoading } = useSalesFunnel(dates?.[0], dates?.[1], salesOwnerId);
  const { data: users } = useUsers();

  if (isLoading || !data) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <Spin size="large" />
      </div>
    );
  }

  const leadStageData = Object.entries(data.leads.by_stage).map(([name, value]) => ({ name, value }));
  const oppStageData = Object.entries(data.opportunities.by_stage).map(([name, value]) => ({ name, value }));
  const projectStatusData = Object.entries(data.projects.by_status).map(([name, value]) => ({ name, value }));
  const contractStatusData = Object.entries(data.contracts.by_status).map(([name, value]) => ({ name, value }));

  const funnelOption = {
    title: { text: '销售漏斗', left: 'center' },
    tooltip: { trigger: 'item', formatter: '{b}: {c}' },
    series: [{
      type: 'funnel',
      left: '10%',
      top: 60,
      bottom: 20,
      width: '80%',
      min: 0,
      max: 100,
      minSize: '0%',
      maxSize: '100%',
      sort: 'none',
      gap: 2,
      label: { show: true, position: 'inside' },
      itemStyle: { borderColor: '#fff', borderWidth: 1 },
      data: [
        { value: data.leads.total, name: '线索' },
        { value: data.opportunities.total, name: '商机' },
        { value: data.projects.total, name: '项目' },
        { value: data.contracts.total, name: '合同' },
      ],
    }],
  };

  const pieOption = (title: string, chartData: { name: string; value: number }[]) => ({
    title: { text: title, left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '55%'],
      data: chartData,
      label: { show: true, formatter: '{b}\n{c}' },
    }],
  });

  const conversionColumns = [
    { title: '转化阶段', dataIndex: 'stage', key: 'stage' },
    { title: '转化率', dataIndex: 'rate', key: 'rate', render: (v: number) => `${v}%` },
  ];

  const conversionData = [
    { key: '1', stage: '线索 → 商机', rate: data.conversion_rates.lead_to_opportunity },
    { key: '2', stage: '商机 → 项目', rate: data.conversion_rates.opportunity_to_project },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card>
        <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
          <Title level={4} style={{ margin: 0 }}>销售漏斗报表</Title>
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
            <Card><Statistic title="线索总数" value={data.leads.total} prefix={<UserOutlined />} /></Card>
          </Col>
          <Col span={4}>
            <Card><Statistic title="商机总数" value={data.opportunities.total} prefix={<TeamOutlined />} /></Card>
          </Col>
          <Col span={4}>
            <Card><Statistic title="项目总数" value={data.projects.total} prefix={<FundProjectionScreenOutlined />} /></Card>
          </Col>
          <Col span={4}>
            <Card><Statistic title="合同总数" value={data.contracts.total} prefix={<FileDoneOutlined />} /></Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic 
                title="预计合同总额" 
                value={data.opportunities.total_amount} 
                prefix="¥" 
                precision={0}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic 
                title="合同签约总额" 
                value={data.contracts.total_amount} 
                prefix="¥" 
                precision={0}
              />
            </Card>
          </Col>
        </Row>

        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={12}>
            <ReactECharts option={funnelOption} style={{ height: 400 }} />
          </Col>
          <Col span={12}>
            <Card title="转化率统计">
              <Table columns={conversionColumns} dataSource={conversionData} pagination={false} size="small" />
            </Card>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <ReactECharts option={pieOption('线索阶段分布', leadStageData)} style={{ height: 300 }} />
          </Col>
          <Col span={12}>
            <ReactECharts option={pieOption('商机阶段分布', oppStageData)} style={{ height: 300 }} />
          </Col>
        </Row>

        <Row gutter={16} style={{ marginTop: 16 }}>
          <Col span={12}>
            <ReactECharts option={pieOption('项目状态分布', projectStatusData)} style={{ height: 300 }} />
          </Col>
          <Col span={12}>
            <ReactECharts option={pieOption('合同状态分布', contractStatusData)} style={{ height: 300 }} />
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default SalesFunnelReport;