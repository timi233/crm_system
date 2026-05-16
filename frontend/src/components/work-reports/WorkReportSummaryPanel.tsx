import React from 'react';
import { Card, Descriptions, Empty, Tag, Typography, Collapse, Table } from 'antd';
import { StructuredSnapshot } from '../../hooks/useWorkReports';
import { formatWan } from '../../utils/currency';

const { Text } = Typography;

type Props = {
  snapshot?: StructuredSnapshot;
  reportType: 'daily' | 'weekly';
};

const SummarySection: React.FC<{
  title: string;
  count: number;
  items: Array<{ id: number; [key: string]: unknown }>;
  columns: Array<{ key: string; label: string }>;
}> = ({ title, count, items, columns }) => {
  if (count === 0) {
    return (
      <div style={{ marginBottom: 16 }}>
        <Text strong>{title}</Text>
        <Tag color="default" style={{ marginLeft: 8 }}>0 条</Tag>
        <Empty description="暂无数据" image={Empty.PRESENTED_IMAGE_SIMPLE} style={{ marginTop: 8 }} />
      </div>
    );
  }

  const tableColumns = columns.map(col => ({
    title: col.label,
    dataIndex: col.key,
    key: col.key,
    render: (value: unknown) => {
      if (typeof value === 'number' && col.key === 'amount') {
        return formatWan(value);
      }
      if (typeof value === 'string' && value.length > 50) {
        return value.slice(0, 50) + '...';
      }
      return value ?? '-';
    },
  }));

  return (
    <div style={{ marginBottom: 16 }}>
      <Text strong>{title}</Text>
      <Tag color="blue" style={{ marginLeft: 8 }}>{count} 条</Tag>
      <Table
        dataSource={items}
        columns={tableColumns}
        rowKey="id"
        size="small"
        pagination={false}
        scroll={{ y: 150 }}
        style={{ marginTop: 8 }}
      />
    </div>
  );
};

const WorkReportSummaryPanel: React.FC<Props> = ({ snapshot, reportType }) => {
  if (!snapshot) {
    return (
      <Card title="结构化汇总">
        <Empty description="暂无汇总数据，请点击重新生成" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      </Card>
    );
  }

  if (reportType === 'weekly') {
    const dailyReports = snapshot.daily_reports || [];
    const summary = snapshot.summary || {};

    if (dailyReports.length === 0) {
      return (
        <Card title="本周日报汇总">
          <Empty description="本周暂无日报" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        </Card>
      );
    }

    return (
      <Card title="本周日报汇总">
        <Descriptions bordered size="small" column={3} style={{ marginBottom: 16 }}>
          <Descriptions.Item label="跟进记录">{summary.total_follow_ups || 0}</Descriptions.Item>
          <Descriptions.Item label="新增线索">{summary.total_leads || 0}</Descriptions.Item>
          <Descriptions.Item label="新增商机">{summary.total_opportunities || 0}</Descriptions.Item>
          <Descriptions.Item label="新增项目">{summary.total_projects || 0}</Descriptions.Item>
          <Descriptions.Item label="新增合同">{summary.total_contracts || 0}</Descriptions.Item>
          <Descriptions.Item label="工单">{summary.total_work_orders || 0}</Descriptions.Item>
          <Descriptions.Item label="渠道">{summary.total_channels || 0}</Descriptions.Item>
        </Descriptions>

        <Collapse
          items={dailyReports.map(dr => ({
            key: dr.id,
            label: `${dr.report_date} - ${dr.status === 'submitted' ? '已提交' : dr.status === 'draft' ? '草稿' : '已撤回'}`,
            children: (
              <Descriptions size="small" column={3}>
                <Descriptions.Item label="跟进">{dr.summary?.follow_ups || 0}</Descriptions.Item>
                <Descriptions.Item label="线索">{dr.summary?.leads || 0}</Descriptions.Item>
                <Descriptions.Item label="商机">{dr.summary?.opportunities || 0}</Descriptions.Item>
                <Descriptions.Item label="项目">{dr.summary?.projects || 0}</Descriptions.Item>
                <Descriptions.Item label="合同">{dr.summary?.contracts || 0}</Descriptions.Item>
                <Descriptions.Item label="工单">{dr.summary?.work_orders || 0}</Descriptions.Item>
                <Descriptions.Item label="渠道">{dr.summary?.channels || 0}</Descriptions.Item>
              </Descriptions>
            ),
          }))}
        />
      </Card>
    );
  }

  return (
    <Card title="当日系统操作汇总">
      <SummarySection
        title="跟进记录"
        count={snapshot.follow_ups?.count || 0}
        items={snapshot.follow_ups?.items || []}
        columns={[
          { key: 'id', label: 'ID' },
          { key: 'type', label: '类型' },
          { key: 'content', label: '内容' },
        ]}
      />

      <SummarySection
        title="新增线索"
        count={snapshot.leads?.count || 0}
        items={snapshot.leads?.items || []}
        columns={[
          { key: 'id', label: 'ID' },
          { key: 'name', label: '名称' },
          { key: 'status', label: '阶段' },
        ]}
      />

      <SummarySection
        title="新增商机"
        count={snapshot.opportunities?.count || 0}
        items={snapshot.opportunities?.items || []}
        columns={[
          { key: 'id', label: 'ID' },
          { key: 'name', label: '名称' },
          { key: 'stage', label: '阶段' },
          { key: 'amount', label: '金额(万元)' },
        ]}
      />

      <SummarySection
        title="新增项目"
        count={snapshot.projects?.count || 0}
        items={snapshot.projects?.items || []}
        columns={[
          { key: 'id', label: 'ID' },
          { key: 'name', label: '名称' },
          { key: 'status', label: '状态' },
        ]}
      />

      <SummarySection
        title="新增合同"
        count={snapshot.contracts?.count || 0}
        items={snapshot.contracts?.items || []}
        columns={[
          { key: 'id', label: 'ID' },
          { key: 'code', label: '编号' },
          { key: 'amount', label: '金额(万元)' },
        ]}
      />

      <SummarySection
        title="工单"
        count={snapshot.work_orders?.count || 0}
        items={snapshot.work_orders?.items || []}
        columns={[
          { key: 'id', label: 'ID' },
          { key: 'title', label: '描述' },
          { key: 'status', label: '状态' },
        ]}
      />

      <SummarySection
        title="渠道"
        count={snapshot.channels?.count || 0}
        items={snapshot.channels?.items || []}
        columns={[
          { key: 'id', label: 'ID' },
          { key: 'name', label: '名称' },
          { key: 'status', label: '状态' },
        ]}
      />
    </Card>
  );
};

export default WorkReportSummaryPanel;
