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
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 90,
      render: (priority: string) => <Tag color={priorityColor(priority)}>{priority}</Tag>,
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
      title: '更新时间',
      dataIndex: 'status_updated_at',
      key: 'status_updated_at',
      width: 160,
      render: (date?: string) => (date ? new Date(date).toLocaleString('zh-CN') : '-'),
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
        {record.technician_ids && record.technician_ids.length > 0 && (
          <div>
            <Text strong>技术人员 IDs: </Text>
            <Space>
              {record.technician_ids.map((techId) => (
                <Tag key={techId} color="purple">
                  {techId}
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
