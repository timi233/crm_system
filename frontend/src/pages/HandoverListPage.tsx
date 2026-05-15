import React, { useState } from 'react';
import { Table, Button, Space, Card, Tag, Select, Input } from 'antd';
import { EyeOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useHandoverRequests } from '../hooks/useHandovers';
import { useUsers } from '../hooks/useUsers';

const { Search } = Input;

const STATUS_LABELS: Record<string, string> = {
  pending_assignment: '待分配',
  pending_execution: '待执行',
  executing: '执行中',
  completed: '已完成',
  canceled: '已取消',
  failed: '失败',
};

const STATUS_COLORS: Record<string, string> = {
  pending_assignment: 'orange',
  pending_execution: 'blue',
  executing: 'processing',
  completed: 'success',
  canceled: 'default',
  failed: 'error',
};

const HandoverListPage: React.FC = () => {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);
  const [searchText, setSearchText] = useState('');

  const { data: handovers = [], isLoading } = useHandoverRequests({
    status: statusFilter,
    limit: 100,
  });
  const { data: users = [] } = useUsers();

  const userMap = new Map<number, string>(users.map((u: any) => [u.id, u.name]));

  const filtered = handovers.filter((h) => {
    if (!searchText) return true;
    const fromName = String(userMap.get(h.from_user_id) || '');
    const toName = h.to_user_id ? String(userMap.get(h.to_user_id) || '') : '';
    const keyword = searchText.toLowerCase();
    return fromName.toLowerCase().includes(keyword) || toName.toLowerCase().includes(keyword);
  });

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 70,
    },
    {
      title: '离职人员',
      dataIndex: 'from_user_id',
      key: 'from_user_id',
      render: (userId: number) => userMap.get(userId) || `用户 #${userId}`,
    },
    {
      title: '接收人',
      dataIndex: 'to_user_id',
      key: 'to_user_id',
      render: (userId: number | null) => (userId ? userMap.get(userId) || `用户 #${userId}` : '-'),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={STATUS_COLORS[status] || 'default'}>
          {STATUS_LABELS[status] || status}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (val: string) => (val ? new Date(val).toLocaleString('zh-CN') : '-'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Button
          icon={<EyeOutlined />}
          size="small"
          onClick={() => navigate(`/handovers/${record.id}`)}
        >
          查看详情
        </Button>
      ),
    },
  ];

  return (
    <Card title="离职交接管理">
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Search
            placeholder="搜索离职人员或接收人"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 200 }}
          />
          <Select
            placeholder="筛选状态"
            value={statusFilter}
            onChange={(v) => setStatusFilter(v || undefined)}
            style={{ width: 150 }}
            allowClear
          >
            {Object.entries(STATUS_LABELS).map(([key, label]) => (
              <Select.Option key={key} value={key}>
                {label}
              </Select.Option>
            ))}
          </Select>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={filtered}
        loading={isLoading}
        rowKey="id"
        pagination={{ pageSize: 20 }}
        locale={{ emptyText: '暂无交接记录' }}
      />
    </Card>
  );
};

export default HandoverListPage;
