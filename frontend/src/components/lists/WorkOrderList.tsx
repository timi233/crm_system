import React, { useState } from 'react';
import { Table, Button, Space, Card, Tag, Input, Select, message } from 'antd';
import { PlusOutlined, EyeOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useWorkOrders } from '../../hooks/useWorkOrders';
import type { WorkOrder } from '../../types/workOrder';
import { useUsers } from '../../hooks/useUsers';

const { Option } = Select;
const { Search } = Input;

const WORK_ORDER_STATUS = ['PENDING', 'ACCEPTED', 'IN_SERVICE', 'DONE', 'CANCELLED', 'REJECTED'];
const WORK_ORDER_STATUS_LABELS: Record<string, string> = {
  PENDING: '待处理',
  ACCEPTED: '已接收',
  IN_SERVICE: '服务中',
  DONE: '已完成',
  CANCELLED: '已取消',
  REJECTED: '已拒绝',
};

const ORDER_TYPE_LABELS: Record<string, string> = {
  CF: '公司外勤',
  CO: '公司内勤',
  MF: '维修保养',
  MO: '其他',
};

const PRIORITY_LABELS: Record<string, string> = {
  NORMAL: '普通',
  URGENT: '紧急',
  VERY_URGENT: '非常紧急',
};

const WorkOrderList: React.FC = () => {
  const navigate = useNavigate();
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [priorityFilter, setPriorityFilter] = useState<string | null>(null);

  const { data: workOrders = [], isLoading } = useWorkOrders();
  const { data: users = [] } = useUsers();

  const userOptions = users.map(u => ({ value: u.id, label: u.name }));

  const filteredWorkOrders = workOrders.filter(workOrder => {
    const matchesSearch = !searchText ||
      workOrder.customer_name?.toLowerCase().includes(searchText.toLowerCase());
    const matchesStatus = !statusFilter || workOrder.status === statusFilter;
    const matchesPriority = !priorityFilter || workOrder.priority === priorityFilter;
    return matchesSearch && matchesStatus && matchesPriority;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PENDING': return 'blue';
      case 'ACCEPTED': return 'green';
      case 'IN_SERVICE': return 'orange';
      case 'DONE': return 'success';
      case 'CANCELLED': return 'red';
      case 'REJECTED': return 'red';
      default: return 'default';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'VERY_URGENT': return 'red';
      case 'URGENT': return 'orange';
      case 'NORMAL': return 'blue';
      default: return 'default';
    }
  };

  const handleView = (workOrder: WorkOrder) => {
    navigate(`/work-orders/${workOrder.id}`);
  };

  const handleCreate = () => {
    message.info('工单需通过派工流程创建：请从线索、商机或项目详情页发起派工申请');
  };

  const columns = [
    {
      title: '工单号',
      dataIndex: 'work_order_no',
      key: 'work_order_no',
      width: 150,
    },
    {
      title: '客户名称',
      dataIndex: 'customer_name',
      key: 'customer_name',
    },
    {
      title: '订单类型',
      dataIndex: 'order_type',
      key: 'order_type',
      width: 100,
      render: (type: string) => ORDER_TYPE_LABELS[type] || type,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>{WORK_ORDER_STATUS_LABELS[status] || status}</Tag>
      ),
    },
    {
      title: '销售负责人',
      dataIndex: 'related_sales_name',
      key: 'related_sales_name',
      width: 120,
      render: (name: string) => name || '-',
    },
    {
      title: '技术员',
      dataIndex: 'technician_names',
      key: 'technician_names',
      width: 150,
      render: (names: string[]) => names.length > 0 ? names.join(', ') : '未分配',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (date: string) => date ? new Date(date).toLocaleString('zh-CN') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: WorkOrder) => (
        <Space size="small">
          <Button 
            size="small" 
            icon={<EyeOutlined />} 
            onClick={() => handleView(record)}
          >
            查看
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <Card
      title="派工单管理"
      extra={
        <Button icon={<PlusOutlined />} onClick={handleCreate}>
          如何创建工单？
        </Button>
      }
    >
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Search
            placeholder="搜索客户名称"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 200 }}
          />
          <Select
            placeholder="筛选状态"
            value={statusFilter}
            onChange={setStatusFilter}
            style={{ width: 140 }}
            allowClear
          >
            {WORK_ORDER_STATUS.map(status => (
              <Option key={status} value={status}>{WORK_ORDER_STATUS_LABELS[status]}</Option>
            ))}
          </Select>
          <Select
            placeholder="筛选优先级"
            value={priorityFilter}
            onChange={setPriorityFilter}
            style={{ width: 140 }}
            allowClear
          >
            {Object.entries(PRIORITY_LABELS).map(([key, label]) => (
              <Option key={key} value={key}>{label}</Option>
            ))}
          </Select>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={filteredWorkOrders}
        loading={isLoading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        scroll={{ x: 1200 }}
      />
    </Card>
  );
};

export default WorkOrderList;
