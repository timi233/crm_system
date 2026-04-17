import React, { useState } from 'react';
import { Card, Table, Button, Space, Empty, Typography, Tag } from 'antd';
import { ReloadOutlined, EyeOutlined } from '@ant-design/icons';
import type { DispatchRecord } from '../../types/dispatch';
import type { DispatchRecordQueryParams } from '../../services/dispatchRecordService';
import { useDispatchRecords } from '../../hooks/useDispatchRecords';
import { DispatchStatusBadge } from './DispatchStatusBadge';

const { Text } = Typography;

interface DispatchHistoryTableProps {
  lead_id?: number;
  opportunity_id?: number;
  project_id?: number;
}

type ExpandedRecord = DispatchRecord & { key: string };

const DispatchHistoryTable: React.FC<DispatchHistoryTableProps> = ({
  lead_id,
  opportunity_id,
  project_id,
}) => {
  const [expandedRowKeys, setExpandedRowKeys] = useState<string[]>([]);

  const params: DispatchRecordQueryParams = {
    lead_id,
    opportunity_id,
    project_id,
  };

  const { data: records = [], isLoading, refetch, isRefetching } = useDispatchRecords(params);

  const priorityColor = (priority: string): string => {
    const priorityLower = priority.toLowerCase();
    if (priorityLower.includes('high') || priorityLower.includes('紧急')) return 'red';
    if (priorityLower.includes('medium') || priorityLower.includes('中')) return 'orange';
    if (priorityLower.includes('low') || priorityLower.includes('低')) return 'green';
    return 'default';
  };

  const columns = [
    {
      title: '工单编号',
      dataIndex: 'work_order_no',
      key: 'work_order_no',
      width: 160,
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: DispatchRecord['status']) => <DispatchStatusBadge status={status} />,
    },
    {
      title: '服务工程师',
      dataIndex: 'technician_names',
      key: 'technician_names',
      width: 150,
      render: (names: string[]) => names && names.length > 0 ? names.join(', ') : '未分配',
    },
    {
      title: '工单类型',
      dataIndex: 'order_type',
      key: 'order_type',
      width: 120,
    },
    {
      title: '客户名称',
      dataIndex: 'customer_name',
      key: 'customer_name',
      width: 150,
      ellipsis: true,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '服务时间',
      key: 'service_time',
      width: 180,
      render: (_: any, record: DispatchRecord) => {
        if (!record.estimated_start_date) return '-';
        const start = new Date(record.estimated_start_date);
        const end = new Date(record.estimated_end_date || record.estimated_start_date);
        const startPeriod = record.estimated_start_period || '上午';
        const endPeriod = record.estimated_end_period || '下午';
        
        const days = Math.floor((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
        let totalDays = days;
        if (startPeriod === '上午' && endPeriod === '下午') {
          totalDays = days + 1;
        } else if (startPeriod === '下午' && endPeriod === '上午') {
          totalDays = days;
        } else {
          totalDays = days + 0.5;
        }
        
        if (days === 0) {
          return `${start.toLocaleDateString('zh-CN')} (${totalDays}天)`;
        }
        return `${start.toLocaleDateString('zh-CN')} 至 ${end.toLocaleDateString('zh-CN')} (${totalDays}天)`;
      },
    },
  ];

  const expandedRowRender = (record: ExpandedRecord) => (
    <Card size="small" style={{ margin: '12px 24px', backgroundColor: '#fafafa' }}>
      <Space direction="vertical" size="small" style={{ width: '100%' }}>
        <div>
          <Text strong>工单 ID: </Text>
          <Text copyable>{record.work_order_id}</Text>
        </div>
        {record.description && (
          <div>
            <Text strong>描述: </Text>
            <Text>{record.description}</Text>
          </div>
        )}
        <div>
          <Text strong>来源类型: </Text>
          <Tag>{record.source_type}</Tag>
          <Text strong style={{ marginLeft: 16 }}>来源 ID: </Text>
          <Text>{record.source_id}</Text>
        </div>
        {record.previous_status && (
          <div>
            <Text strong>前一状态: </Text>
            <DispatchStatusBadge status={record.previous_status} />
          </div>
        )}
        {record.dispatched_at && (
          <div>
            <Text strong>派工时间: </Text>
            <Text>{new Date(record.dispatched_at).toLocaleString('zh-CN')}</Text>
          </div>
        )}
        {record.completed_at && (
          <div>
            <Text strong>完成时间: </Text>
            <Text>{new Date(record.completed_at).toLocaleString('zh-CN')}</Text>
          </div>
        )}
        {record.technician_names && record.technician_names.length > 0 && (
          <div>
            <Text strong>服务工程师: </Text>
            <Space>
              {record.technician_names.map((name) => (
                <Tag key={name} color="purple">
                  {name}
                </Tag>
              ))}
            </Space>
          </div>
        )}
      </Space>
    </Card>
  );

  const onExpand = (expanded: boolean, record: ExpandedRecord) => {
    if (expanded) {
      setExpandedRowKeys([record.key]);
    } else {
      setExpandedRowKeys([]);
    }
  };

  return (
    <Card
      title="派工历史"
      extra={
        <Button
          icon={<ReloadOutlined spin={isRefetching} />}
          onClick={() => refetch()}
          size="small"
        >
          刷新
        </Button>
      }
      size="small"
    >
      <Table
        columns={columns}
        dataSource={records.map((record) => ({ ...record, key: String(record.id) }))}
        loading={isLoading}
        rowKey="id"
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条`,
        }}
        size="middle"
        expandable={{
          expandedRowRender,
          expandRowByClick: true,
          expandedRowKeys,
          onExpand,
          expandIcon: ({ expanded, record }) => (
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined rotate={expanded ? 90 : 0} />}
              onClick={(e) => {
                e.stopPropagation();
                const newKeys = expanded ? [] : [String(record.id)];
                setExpandedRowKeys(newKeys);
              }}
            />
          ),
        }}
        locale={{
          emptyText: (
            <Empty description="暂无派工记录" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          ),
        }}
        scroll={{ x: 1000 }}
      />
    </Card>
  );
};

export default DispatchHistoryTable;
