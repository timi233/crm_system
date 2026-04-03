import React, { useState } from 'react';
import { Card, Table, Button, Space, Modal, Form, Select, InputNumber, message, Popconfirm, Tag, Collapse, Descriptions } from 'antd';
import { PlusOutlined, DeleteOutlined, TrophyOutlined, SplitCellsOutlined, EyeOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';

const { Option } = Select;
const { Panel } = Collapse;

type YearTarget = {
  id: number;
  user_id: number;
  target_year: number;
  target_amount: number;
  decomposed: boolean;
  quarterly_count: number;
  monthly_count: number;
  created_at?: string;
};

type ChildTarget = {
  id: number;
  target_type: string;
  target_period: number;
  target_amount: number;
  has_children: boolean;
};

type User = {
  id: number;
  name: string;
};

const SalesTargetList: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isDecomposeModalVisible, setIsDecomposeModalVisible] = useState(false);
  const [selectedYearTarget, setSelectedYearTarget] = useState<YearTarget | null>(null);
  const [expandedRowKeys, setExpandedRowKeys] = useState<number[]>([]);
  const [childrenData, setChildrenData] = useState<Record<number, ChildTarget[]>>({});
  const [form] = Form.useForm();
  const [decomposeForm] = Form.useForm();
  const queryClient = useQueryClient();

  const { data: yearTargets = [], isLoading } = useQuery({
    queryKey: ['sales-targets', 'yearly-with-status'],
    queryFn: () => api.get<YearTarget[]>('/sales-targets/yearly-with-status').then(res => res.data),
  });

  const { data: users = [] } = useQuery({
    queryKey: ['users'],
    queryFn: () => api.get<User[]>('/users').then(res => res.data),
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => api.post('/sales-targets/year', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sales-targets'] });
      message.success('年目标创建成功');
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || '创建失败');
    },
  });

  const decomposeMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      api.post(`/sales-targets/${id}/decompose-quarterly`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sales-targets'] });
      message.success('分解成功，已自动生成季度目标和月度目标');
      setIsDecomposeModalVisible(false);
      decomposeForm.resetFields();
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || '分解失败');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/sales-targets/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sales-targets'] });
      message.success('删除成功');
    },
  });

  const fetchChildren = async (targetId: number) => {
    try {
      const res = await api.get(`/sales-targets/${targetId}/children`);
      setChildrenData(prev => ({ ...prev, [targetId]: res.data.children }));
    } catch (error) {
      console.error('Failed to fetch children:', error);
    }
  };

  const handleCreate = () => {
    form.resetFields();
    form.setFieldsValue({ target_year: new Date().getFullYear() });
    setIsModalVisible(true);
  };

  const handleDecompose = (target: YearTarget) => {
    setSelectedYearTarget(target);
    const avgQuarter = Math.round(target.target_amount / 4);
    decomposeForm.setFieldsValue({
      q1: avgQuarter,
      q2: avgQuarter,
      q3: avgQuarter,
      q4: avgQuarter,
    });
    setIsDecomposeModalVisible(true);
  };

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id);
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      await createMutation.mutateAsync(values);
      setIsModalVisible(false);
      form.resetFields();
    } catch (error) {}
  };

  const handleDecomposeOk = async () => {
    try {
      const values = await decomposeForm.validateFields();
      await decomposeMutation.mutateAsync({
        id: selectedYearTarget!.id,
        data: values,
      });
    } catch (error) {}
  };

  const handleExpand = (expanded: boolean, record: YearTarget) => {
    if (expanded && !childrenData[record.id]) {
      fetchChildren(record.id);
    }
    setExpandedRowKeys(expanded ? [...expandedRowKeys, record.id] : expandedRowKeys.filter(k => k !== record.id));
  };

  const getUserName = (userId: number) => {
    const user = users.find(u => u.id === userId);
    return user?.name || `用户${userId}`;
  };

  const getQuarterLabel = (period: number) => `Q${period}`;
  const getMonthLabel = (period: number) => `${period}月`;

  const columns = [
    {
      title: '销售人员',
      dataIndex: 'user_id',
      key: 'user_id',
      render: (userId: number) => getUserName(userId),
    },
    {
      title: '年份',
      dataIndex: 'target_year',
      key: 'target_year',
      render: (year: number) => `${year}年`,
    },
    {
      title: '年目标金额',
      dataIndex: 'target_amount',
      key: 'target_amount',
      render: (amount: number) => `¥${amount?.toLocaleString() || 0}`,
    },
    {
      title: '分解状态',
      dataIndex: 'decomposed',
      key: 'decomposed',
      render: (decomposed: boolean, record: YearTarget) => (
        decomposed 
          ? <Tag color="green">已分解 ({record.quarterly_count}季度/{record.monthly_count}月)</Tag>
          : <Tag color="orange">待分解</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: YearTarget) => (
        <Space size="small">
          {!record.decomposed && (
            <Button
              size="small"
              type="primary"
              icon={<SplitCellsOutlined />}
              onClick={() => handleDecompose(record)}
            >
              分解
            </Button>
          )}
          <Popconfirm
            title="确定删除? 删除后关联的季度和月度目标也会被删除"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const currentYear = new Date().getFullYear();

  return (
    <Card
      title={
        <Space>
          <TrophyOutlined />
          销售目标管理（年度目标）
        </Space>
      }
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建年目标
        </Button>
      }
    >
      <Table
        columns={columns}
        dataSource={yearTargets}
        loading={isLoading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        expandable={{
          expandedRowKeys: expandedRowKeys,
          onExpandedRowsChange: (keys) => setExpandedRowKeys(keys as number[]),
          onExpand: handleExpand,
          expandedRowRender: (record) => {
            const children = childrenData[record.id] || [];
            const quarters = children.filter(c => c.target_type === 'quarterly');
            
            return (
              <div style={{ padding: '0 24px' }}>
                <h4 style={{ marginBottom: 12 }}>季度目标</h4>
                <Descriptions bordered size="small" column={4}>
                  {quarters.map(q => (
                    <Descriptions.Item key={q.id} label={getQuarterLabel(q.target_period)}>
                      ¥{q.target_amount?.toLocaleString()}
                    </Descriptions.Item>
                  ))}
                </Descriptions>
                {quarters.length === 0 && <div style={{ color: '#999' }}>暂无季度目标</div>}
              </div>
            );
          },
          rowExpandable: (record) => record.decomposed,
        }}
      />

      <Modal
        title="新建年度目标"
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => setIsModalVisible(false)}
        okText="创建"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="user_id"
            label="销售人员"
            rules={[{ required: true, message: '请选择销售人员' }]}
          >
            <Select placeholder="选择销售人员" showSearch optionFilterProp="children">
              {users.filter(u => u.id !== 1).map(u => (
                <Option key={u.id} value={u.id}>{u.name}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="target_year"
            label="年份"
            rules={[{ required: true }]}
          >
            <Select placeholder="选择年份">
              {[currentYear - 1, currentYear, currentYear + 1].map(y => (
                <Option key={y} value={y}>{y}年</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="target_amount"
            label="年度目标金额"
            rules={[{ required: true, message: '请输入目标金额' }]}
          >
            <InputNumber
              style={{ width: '100%' }}
              placeholder="输入金额"
              min={0}
              precision={0}
              formatter={value => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
            />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`分解年度目标 - ${selectedYearTarget?.target_year}年 - ${getUserName(selectedYearTarget?.user_id || 0)}`}
        open={isDecomposeModalVisible}
        onOk={handleDecomposeOk}
        onCancel={() => setIsDecomposeModalVisible(false)}
        okText="确认分解"
        cancelText="取消"
        width={500}
      >
        <p style={{ marginBottom: 16 }}>
          年度目标总额：<strong>¥{selectedYearTarget?.target_amount?.toLocaleString()}</strong>
        </p>
        <Form form={decomposeForm} layout="vertical">
          <Form.Item name="q1" label="第一季度目标" rules={[{ required: true }]}>
            <InputNumber
              style={{ width: '100%' }}
              placeholder="Q1金额"
              min={0}
              precision={0}
              formatter={value => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
            />
          </Form.Item>
          <Form.Item name="q2" label="第二季度目标" rules={[{ required: true }]}>
            <InputNumber
              style={{ width: '100%' }}
              placeholder="Q2金额"
              min={0}
              precision={0}
              formatter={value => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
            />
          </Form.Item>
          <Form.Item name="q3" label="第三季度目标" rules={[{ required: true }]}>
            <InputNumber
              style={{ width: '100%' }}
              placeholder="Q3金额"
              min={0}
              precision={0}
              formatter={value => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
            />
          </Form.Item>
          <Form.Item name="q4" label="第四季度目标" rules={[{ required: true }]}>
            <InputNumber
              style={{ width: '100%' }}
              placeholder="Q4金额"
              min={0}
              precision={0}
              formatter={value => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
            />
          </Form.Item>
        </Form>
        <p style={{ color: '#888', fontSize: 12 }}>
          提示：季度目标将自动分解为月度目标（每月 = 季度目标 ÷ 3）
        </p>
      </Modal>
    </Card>
  );
};

export default SalesTargetList;