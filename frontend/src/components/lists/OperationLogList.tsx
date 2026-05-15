import React, { useState } from 'react';
import { Table, Tag, Select, DatePicker, Space, Descriptions, Modal, Typography, Badge, Button } from 'antd';
import { HistoryOutlined, UserOutlined, ClockCircleOutlined, ReloadOutlined, EyeOutlined } from '@ant-design/icons';
import { useOperationLogs, OperationLog, ACTION_TYPE_LABELS, ENTITY_TYPE_LABELS, getActionColor } from '../../hooks/useOperationLogs';
import PageScaffold from '../common/PageScaffold';
import PageModal from '../common/PageModal';

const { Option } = Select;
const { RangePicker } = DatePicker;
const { Text, Title } = Typography;

const OperationLogList: React.FC = () => {
  const [actionFilter, setActionFilter] = useState<string | undefined>();
  const [entityFilter, setEntityFilter] = useState<string | undefined>();
  const [dateRange, setDateRange] = useState<[string, string] | undefined>();
  const [selectedLog, setSelectedLog] = useState<OperationLog | null>(null);

  const { data: logs = [], isLoading, refetch } = useOperationLogs({
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
      title: '操作时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time: string) => (
        <span style={{ color: '#64748b', fontSize: '13px' }}>
          {new Date(time).toLocaleString('zh-CN')}
        </span>
      ),
    },
    {
      title: '操作账户',
      dataIndex: 'user_name',
      key: 'user_name',
      width: 120,
      render: (name: string) => (
        <Space size={4}>
          <UserOutlined style={{ color: 'var(--primary-color)' }} />
          <span style={{ fontWeight: 600 }}>{name}</span>
        </Space>
      ),
    },
    {
      title: '操作',
      dataIndex: 'action_type',
      key: 'action_type',
      width: 100,
      render: (type: string) => (
        <Tag color={getActionColor(type)} style={{ border: 'none' }}>
          {ACTION_TYPE_LABELS[type] || type}
        </Tag>
      ),
    },
    {
      title: '业务类型',
      dataIndex: 'entity_type',
      key: 'entity_type',
      width: 100,
      render: (type: string) => ENTITY_TYPE_LABELS[type] || type,
    },
    {
      title: '影响对象',
      key: 'entity',
      width: 200,
      render: (_: unknown, record: OperationLog) => (
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <Text strong style={{ fontSize: '13px' }}>{record.entity_name || record.entity_code || `ID: ${record.entity_id}`}</Text>
          {record.entity_code && <Text type="secondary" style={{ fontSize: '11px' }}>{record.entity_code}</Text>}
        </div>
      ),
    },
    {
      title: '摘要说明',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text: string) => <span style={{ color: '#475569' }}>{text}</span>
    },
    {
      title: '终端IP',
      dataIndex: 'ip_address',
      key: 'ip_address',
      width: 130,
      render: (ip: string) => <Text type="secondary" style={{ fontSize: '12px', fontFamily: 'var(--font-mono)' }}>{ip || '-'}</Text>,
    },
    {
      title: '查看',
      key: 'view',
      width: 60,
      fixed: 'right' as const,
      render: (_: any, record: OperationLog) => (
        <Button size="small" type="text" icon={<EyeOutlined />} onClick={() => setSelectedLog(record)} />
      )
    }
  ];

  return (
    <PageScaffold
      title="操作审计日志"
      breadcrumbItems={[{ title: '首页' }, { title: '系统设置' }, { title: '审计日志' }]}
      extra={<Button icon={<ReloadOutlined />} onClick={() => refetch()} />}
      filters={
        <Space size={16} wrap>
          <Select
            placeholder="所有操作类型"
            value={actionFilter}
            onChange={setActionFilter}
            style={{ width: 150 }}
            allowClear
            size="middle"
          >
            {Object.entries(ACTION_TYPE_LABELS).map(([key, label]) => (
              <Option key={key} value={key}>{label}</Option>
            ))}
          </Select>
          <Select
            placeholder="所有对象类型"
            value={entityFilter}
            onChange={setEntityFilter}
            style={{ width: 150 }}
            allowClear
            size="middle"
          >
            {Object.entries(ENTITY_TYPE_LABELS).map(([key, label]) => (
              <Option key={key} value={key}>{label}</Option>
            ))}
          </Select>
          <RangePicker onChange={handleDateChange} size="middle" />
        </Space>
      }
    >
      <Table
        columns={columns}
        dataSource={logs}
        loading={isLoading}
        rowKey="id"
        pagination={{
          pageSize: 20,
          showSizeChanger: true,
          showTotal: (total) => `共记录 ${total} 条操作`
        }}
        scroll={{ x: 1000 }}
        className="customer-table"
        bordered={false}
        onRow={(record) => ({
          onClick: () => setSelectedLog(record),
          style: { cursor: 'pointer' },
        })}
      />

      <PageModal
        title="操作日志详细信息"
        open={!!selectedLog}
        onClose={() => setSelectedLog(null)}
        width={720}
        footer={[<Button key="close" onClick={() => setSelectedLog(null)}>我知道了</Button>]}
      >
        {selectedLog && (
          <div className="fade-in">
            <Descriptions column={2} size="middle" layout="vertical">
              <Descriptions.Item label="发生时间">
                <span style={{ fontWeight: 600 }}>{new Date(selectedLog.created_at).toLocaleString('zh-CN')}</span>
              </Descriptions.Item>
              <Descriptions.Item label="执行账户">
                <Space size={4}><Badge status="processing" />{selectedLog.user_name}</Space>
              </Descriptions.Item>
              <Descriptions.Item label="操作指令">
                <Tag color={getActionColor(selectedLog.action_type)} style={{ border: 'none' }}>
                  {ACTION_TYPE_LABELS[selectedLog.action_type] || selectedLog.action_type}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="业务对象">
                {ENTITY_TYPE_LABELS[selectedLog.entity_type] || selectedLog.entity_type}
              </Descriptions.Item>
              <Descriptions.Item label="对象识别码">
                <Text code>{selectedLog.entity_code || '-'}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="对象显示名称">
                {selectedLog.entity_name || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="来源 IP" span={2}>
                <Text type="secondary">{selectedLog.ip_address || '-'}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="详情描述" span={2}>
                <div style={{ background: '#f8fafc', padding: '12px 16px', borderRadius: '8px', border: '1px solid #f1f5f9' }}>
                  {selectedLog.description}
                </div>
              </Descriptions.Item>
            </Descriptions>

            {(selectedLog.old_value || selectedLog.new_value) && (
              <div style={{ marginTop: 24 }}>
                <Title level={5} style={{ fontSize: '14px', marginBottom: 12 }}>数据变更细节</Title>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div>
                    <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>修改前</div>
                    <pre style={{
                      margin: 0,
                      padding: '12px',
                      background: '#f8fafc',
                      borderRadius: '8px',
                      fontSize: '11px',
                      fontFamily: 'var(--font-mono)',
                      maxHeight: 300,
                      overflow: 'auto',
                      border: '1px solid #f1f5f9'
                    }}>
                      {selectedLog.old_value && Object.keys(selectedLog.old_value).length > 0
                        ? JSON.stringify(selectedLog.old_value, null, 2)
                        : '（无初始数据）'}
                    </pre>
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>修改后</div>
                    <pre style={{
                      margin: 0,
                      padding: '12px',
                      background: '#eff6ff',
                      borderRadius: '8px',
                      fontSize: '11px',
                      fontFamily: 'var(--font-mono)',
                      maxHeight: 300,
                      overflow: 'auto',
                      border: '1px solid #dbeafe',
                      color: '#1e40af'
                    }}>
                      {selectedLog.new_value && Object.keys(selectedLog.new_value).length > 0
                        ? JSON.stringify(selectedLog.new_value, null, 2)
                        : '（无变更数据）'}
                    </pre>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </PageModal>
    </PageScaffold>
  );
};

export default OperationLogList;
