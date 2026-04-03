import React, { useState } from 'react';
import { Table, Card, Tag, Select, DatePicker, Space, Descriptions, Modal, Typography, Badge } from 'antd';
import { HistoryOutlined, UserOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { useOperationLogs, OperationLog, ACTION_TYPE_LABELS, ENTITY_TYPE_LABELS, getActionColor } from '../../hooks/useOperationLogs';

const { Option } = Select;
const { RangePicker } = DatePicker;
const { Text } = Typography;

const OperationLogList: React.FC = () => {
  const [actionFilter, setActionFilter] = useState<string | undefined>();
  const [entityFilter, setEntityFilter] = useState<string | undefined>();
  const [dateRange, setDateRange] = useState<[string, string] | undefined>();
  const [selectedLog, setSelectedLog] = useState<OperationLog | null>(null);

  const { data: logs = [], isLoading } = useOperationLogs({
    action_type: actionFilter,
    entity_type: entityFilter,
    start_date: dateRange?.[0],
    end_date: dateRange?.[1],
    limit: 200,
  });

  const handleDateChange = (dates: any) => {
    if (dates) {
      setDateRange([dates[0].format('YYYY-MM-DD'), dates[1].format('YYYY-MM-DD')]);
    } else {
      setDateRange(undefined);
    }
  };

  const columns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time: string) => (
        <Space>
          <ClockCircleOutlined />
          {new Date(time).toLocaleString('zh-CN')}
        </Space>
      ),
    },
    {
      title: '操作人',
      dataIndex: 'user_name',
      key: 'user_name',
      width: 100,
      render: (name: string) => (
        <Space>
          <UserOutlined />
          {name}
        </Space>
      ),
    },
    {
      title: '操作类型',
      dataIndex: 'action_type',
      key: 'action_type',
      width: 100,
      render: (type: string) => (
        <Tag color={getActionColor(type)}>
          {ACTION_TYPE_LABELS[type] || type}
        </Tag>
      ),
    },
    {
      title: '对象类型',
      dataIndex: 'entity_type',
      key: 'entity_type',
      width: 100,
      render: (type: string) => ENTITY_TYPE_LABELS[type] || type,
    },
    {
      title: '对象',
      key: 'entity',
      width: 200,
      render: (_: unknown, record: OperationLog) => (
        <Space direction="vertical" size={0}>
          <Text strong>{record.entity_name || record.entity_code || `ID: ${record.entity_id}`}</Text>
          {record.entity_code && <Text type="secondary" style={{ fontSize: 12 }}>{record.entity_code}</Text>}
        </Space>
      ),
    },
    {
      title: '操作描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: 'IP地址',
      dataIndex: 'ip_address',
      key: 'ip_address',
      width: 130,
      render: (ip: string) => ip || '-',
    },
  ];

  return (
    <Card
      title={
        <Space>
          <HistoryOutlined />
          操作日志
        </Space>
      }
    >
      <div style={{ marginBottom: 16 }}>
        <Space wrap>
          <Select
            placeholder="操作类型"
            value={actionFilter}
            onChange={setActionFilter}
            style={{ width: 120 }}
            allowClear
          >
            {Object.entries(ACTION_TYPE_LABELS).map(([key, label]) => (
              <Option key={key} value={key}>{label}</Option>
            ))}
          </Select>
          <Select
            placeholder="对象类型"
            value={entityFilter}
            onChange={setEntityFilter}
            style={{ width: 120 }}
            allowClear
          >
            {Object.entries(ENTITY_TYPE_LABELS).map(([key, label]) => (
              <Option key={key} value={key}>{label}</Option>
            ))}
          </Select>
          <RangePicker onChange={handleDateChange} />
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={logs}
        loading={isLoading}
        rowKey="id"
        pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (total) => `共 ${total} 条` }}
        scroll={{ x: 1000 }}
        onRow={(record) => ({
          onClick: () => setSelectedLog(record),
          style: { cursor: 'pointer' },
        })}
      />

      <Modal
        title="操作详情"
        open={!!selectedLog}
        onCancel={() => setSelectedLog(null)}
        footer={null}
        width={700}
      >
        {selectedLog && (
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="操作时间">
              {new Date(selectedLog.created_at).toLocaleString('zh-CN')}
            </Descriptions.Item>
            <Descriptions.Item label="操作人">
              <Badge status="processing" text={selectedLog.user_name} />
            </Descriptions.Item>
            <Descriptions.Item label="操作类型">
              <Tag color={getActionColor(selectedLog.action_type)}>
                {ACTION_TYPE_LABELS[selectedLog.action_type] || selectedLog.action_type}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="对象类型">
              {ENTITY_TYPE_LABELS[selectedLog.entity_type] || selectedLog.entity_type}
            </Descriptions.Item>
            <Descriptions.Item label="对象编号">
              {selectedLog.entity_code || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="对象名称">
              {selectedLog.entity_name || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="IP地址" span={2}>
              {selectedLog.ip_address || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="操作描述" span={2}>
              {selectedLog.description}
            </Descriptions.Item>
            {selectedLog.old_value && Object.keys(selectedLog.old_value).length > 0 && (
              <Descriptions.Item label="变更前数据" span={2}>
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all', maxHeight: 200, overflow: 'auto' }}>
                  {JSON.stringify(selectedLog.old_value, null, 2)}
                </pre>
              </Descriptions.Item>
            )}
            {selectedLog.new_value && Object.keys(selectedLog.new_value).length > 0 && (
              <Descriptions.Item label="变更后数据" span={2}>
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all', maxHeight: 200, overflow: 'auto' }}>
                  {JSON.stringify(selectedLog.new_value, null, 2)}
                </pre>
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Modal>
    </Card>
  );
};

export default OperationLogList;