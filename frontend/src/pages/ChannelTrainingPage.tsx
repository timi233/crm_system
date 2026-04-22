import React, { useMemo, useState } from 'react';
import {
  Alert,
  App,
  Button,
  Card,
  Col,
  Form,
  Input,
  Modal,
  Popconfirm,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
} from 'antd';
import { DeleteOutlined, DownloadOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons';
import { useSelector } from 'react-redux';

import { useChannelTrainingOverview } from '../hooks/useChannelTrainingOverview';
import {
  ExecutionPlan,
  useCreateExecutionPlan,
  useDeleteExecutionPlan,
  useExecutionPlans,
  useUpdateExecutionPlan,
} from '../hooks/useExecutionPlans';
import { useManageableChannels } from '../hooks/useManageableChannels';
import { useUsers } from '../hooks/useUsers';
import { RootState } from '../store/store';

const ChannelTrainingPage: React.FC = () => {
  const { message } = App.useApp();
  const { capabilities, user } = useSelector((state: RootState) => state.auth);
const canReadTraining = Boolean(capabilities['channel_training:read']);
const canManageTraining = Boolean(capabilities['channel_training:manage_page'] || capabilities['channel_training:manage']);

  const [keyword, setKeyword] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [planModalOpen, setPlanModalOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState<ExecutionPlan | null>(null);
  const [form] = Form.useForm();

  const { data, isLoading } = useChannelTrainingOverview();
  const { data: planList = [], isLoading: planListLoading } = useExecutionPlans({
    plan_category: 'training',
  });
  const { data: channels = [] } = useManageableChannels();
  const { data: users = [] } = useUsers(Boolean(canManageTraining && (user?.role === 'admin' || user?.role === 'business')));
  const createPlanMutation = useCreateExecutionPlan();
  const updatePlanMutation = useUpdateExecutionPlan();
  const deletePlanMutation = useDeleteExecutionPlan();
  const followUps = data?.follow_ups || [];
  const trainingPlanRows = useMemo(
    () =>
      [...planList]
        .filter((plan) => plan.plan_category === 'training')
        .sort((a, b) => String(b.created_at || '').localeCompare(String(a.created_at || ''))),
    [planList]
  );

  const filteredPlans = useMemo(() => {
    const text = keyword.trim().toLowerCase();
    return trainingPlanRows.filter((plan) => {
      const textMatched =
        !text ||
        String(plan.channel_name || '').toLowerCase().includes(text) ||
        String(plan.plan_content || '').toLowerCase().includes(text) ||
        String(plan.plan_period).toLowerCase().includes(text);
      const statusMatched = statusFilter === 'all' || plan.status === statusFilter;
      return textMatched && statusMatched;
    });
  }, [keyword, trainingPlanRows, statusFilter]);

  const filteredFollowUps = useMemo(() => {
    const text = keyword.trim().toLowerCase();
    return followUps.filter((followUp) => {
      return (
        !text ||
        String(followUp.channel_name || '').toLowerCase().includes(text) ||
        String(followUp.follow_up_content || '').toLowerCase().includes(text) ||
        String(followUp.visit_purpose || '').toLowerCase().includes(text)
      );
    });
  }, [followUps, keyword]);

  const statusOptions = useMemo(() => {
    const values = Array.from(new Set(trainingPlanRows.map((plan) => plan.status).filter(Boolean)));
    return values.map((value) => ({ label: value, value }));
  }, [trainingPlanRows]);

  const exportTrainingPlans = () => {
    if (filteredPlans.length === 0) {
      message.warning('没有可导出的培训计划数据');
      return;
    }
    const headers = ['渠道', '计划周期', '计划类型', '状态', '计划内容', '负责人'];
    const lines = filteredPlans.map((item) => [
      item.channel_name,
      item.plan_period,
      item.plan_type,
      item.status,
      item.plan_content,
      item.user_name || '',
    ]);
    const csv = [headers, ...lines]
      .map((line) =>
        line.map((cell) => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(',')
      )
      .join('\n');
    const blob = new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `channel-training-plans-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  const exportTrainingFollowUps = () => {
    if (filteredFollowUps.length === 0) {
      message.warning('没有可导出的培训跟进数据');
      return;
    }
    const headers = ['日期', '渠道', '方式', '拜访目的', '跟进内容', '跟进人'];
    const lines = filteredFollowUps.map((item) => [
      item.follow_up_date,
      item.channel_name || '',
      item.follow_up_method,
      item.visit_purpose || '',
      item.follow_up_content,
      item.follower_name || '',
    ]);
    const csv = [headers, ...lines]
      .map((line) =>
        line.map((cell) => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(',')
      )
      .join('\n');
    const blob = new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `channel-training-followups-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  const openCreatePlanModal = () => {
    setEditingPlan(null);
    form.resetFields();
    form.setFieldsValue({
      plan_type: 'monthly',
      plan_category: 'training',
      status: 'planned',
      user_id: user?.id,
    });
    setPlanModalOpen(true);
  };

  const openEditPlanModal = (plan: ExecutionPlan) => {
    setEditingPlan(plan);
    form.setFieldsValue(plan);
    setPlanModalOpen(true);
  };

  const handleSavePlan = async () => {
    try {
      const values = await form.validateFields();
      const payload = {
        channel_id: values.channel_id,
        user_id: values.user_id,
        plan_type: values.plan_type,
        plan_category: 'training' as const,
        plan_period: values.plan_period,
        plan_content: values.plan_content,
        execution_status: values.execution_status ?? null,
        key_obstacles: values.key_obstacles ?? null,
        next_steps: values.next_steps ?? null,
        status: values.status,
      };

      if (editingPlan) {
        await updatePlanMutation.mutateAsync({ id: editingPlan.id, payload });
        message.success('培训计划已更新');
      } else {
        await createPlanMutation.mutateAsync(payload);
        message.success('培训计划已创建');
      }

      setPlanModalOpen(false);
      setEditingPlan(null);
      form.resetFields();
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  const handleDeletePlan = async (planId: number) => {
    try {
      await deletePlanMutation.mutateAsync(planId);
      message.success('培训计划已删除');
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '删除失败');
    }
  };

  const planColumns = [
    {
      title: '渠道',
      dataIndex: 'channel_name',
      key: 'channel_name',
      width: 220,
    },
    {
      title: '周期',
      dataIndex: 'plan_period',
      key: 'plan_period',
      width: 140,
    },
    {
      title: '类型',
      dataIndex: 'plan_type',
      key: 'plan_type',
      width: 100,
      render: (value: string) => <Tag color="blue">{value}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (value: string) => {
        if (value === 'completed') return <Tag color="green">已完成</Tag>;
        if (value === 'in-progress') return <Tag color="processing">进行中</Tag>;
        if (value === 'planned') return <Tag color="gold">计划中</Tag>;
        return <Tag>{value}</Tag>;
      },
    },
    {
      title: '内容',
      dataIndex: 'plan_content',
      key: 'plan_content',
      ellipsis: true,
    },
    {
      title: '执行情况',
      dataIndex: 'execution_status',
      key: 'execution_status',
      width: 180,
      ellipsis: true,
      render: (value: string) => value || '-',
    },
    {
      title: '下一步',
      dataIndex: 'next_steps',
      key: 'next_steps',
      width: 180,
      ellipsis: true,
      render: (value: string) => value || '-',
    },
    {
      title: '负责人',
      dataIndex: 'user_name',
      key: 'user_name',
      width: 120,
      render: (value: string) => value || '-',
    },
    ...(canManageTraining
      ? [
          {
            title: '操作',
            key: 'actions',
            width: 140,
            render: (_: unknown, record: ExecutionPlan) => (
              <Space>
                <Button size="small" icon={<EditOutlined />} onClick={() => openEditPlanModal(record)}>
                  编辑
                </Button>
                <Popconfirm title="确定删除该培训计划？" onConfirm={() => handleDeletePlan(record.id)}>
                  <Button size="small" danger icon={<DeleteOutlined />} />
                </Popconfirm>
              </Space>
            ),
          },
        ]
      : []),
  ];

  const followUpColumns = [
    {
      title: '日期',
      dataIndex: 'follow_up_date',
      key: 'follow_up_date',
      width: 120,
    },
    {
      title: '渠道',
      dataIndex: 'channel_name',
      key: 'channel_name',
      width: 220,
      render: (value: string) => value || '-',
    },
    {
      title: '方式',
      dataIndex: 'follow_up_method',
      key: 'follow_up_method',
      width: 100,
    },
    {
      title: '拜访目的',
      dataIndex: 'visit_purpose',
      key: 'visit_purpose',
      width: 130,
      render: (value: string) => <Tag color="geekblue">{value || '培训相关'}</Tag>,
    },
    {
      title: '内容',
      dataIndex: 'follow_up_content',
      key: 'follow_up_content',
      ellipsis: true,
    },
    {
      title: '跟进人',
      dataIndex: 'follower_name',
      key: 'follower_name',
      width: 120,
      render: (value: string) => value || '-',
    },
  ];

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      {!canReadTraining && (
        <Alert
          type="warning"
          showIcon
          message="当前账号无渠道培训查看权限"
          description="如需开通，请联系管理员配置 channel_training:read 能力。"
        />
      )}
      {canManageTraining && (
        <Card
          title="管理操作"
          extra={<Tag color="purple">渠道培训录入</Tag>}
        >
          <Space wrap>
            <Button type="primary" size="large" icon={<PlusOutlined />} onClick={openCreatePlanModal}>
              新增培训计划
            </Button>
          </Space>
        </Card>
      )}
      <Row gutter={16}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="培训计划数" value={data?.training_plan_count || 0} />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="已完成计划" value={data?.completed_training_plan_count || 0} />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="培训跟进记录" value={data?.training_follow_up_count || 0} />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="覆盖渠道数" value={data?.covered_channel_count || 0} />
          </Card>
        </Col>
      </Row>

      <Card
        title="培训计划"
        extra={
          <Space>
            <Input.Search
              allowClear
              placeholder="按渠道/内容/周期搜索"
              onSearch={setKeyword}
              onChange={(event) => setKeyword(event.target.value)}
              style={{ width: 260 }}
            />
            <Select
              value={statusFilter}
              onChange={setStatusFilter}
              style={{ width: 140 }}
              options={[{ label: '全部状态', value: 'all' }, ...statusOptions]}
            />
            <Button icon={<DownloadOutlined />} onClick={exportTrainingPlans}>
              导出计划
            </Button>
            {canManageTraining ? (
              <Button type="primary" icon={<PlusOutlined />} onClick={openCreatePlanModal}>
                新增培训计划
              </Button>
            ) : null}
          </Space>
        }
      >
        <Table
          rowKey="id"
          loading={isLoading || planListLoading}
          columns={planColumns}
          dataSource={filteredPlans}
          pagination={{ pageSize: 8 }}
          scroll={{ x: 1000 }}
          locale={{ emptyText: '暂无培训相关计划' }}
        />
      </Card>

      <Card
        title="培训跟进记录"
        extra={
          <Button icon={<DownloadOutlined />} onClick={exportTrainingFollowUps}>
            导出跟进
          </Button>
        }
      >
        <Table
          rowKey="id"
          loading={isLoading}
          columns={followUpColumns}
          dataSource={filteredFollowUps}
          pagination={{ pageSize: 8 }}
          scroll={{ x: 1000 }}
          locale={{ emptyText: '暂无培训相关跟进记录' }}
        />
      </Card>

      <Modal
        title={editingPlan ? '编辑培训计划' : '新增培训计划'}
        open={planModalOpen}
        onOk={handleSavePlan}
        onCancel={() => {
          setPlanModalOpen(false);
          setEditingPlan(null);
        }}
        confirmLoading={createPlanMutation.isPending || updatePlanMutation.isPending}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="channel_id"
            label="渠道"
            rules={[{ required: true, message: '请选择渠道' }]}
          >
            <Select
              showSearch
              optionFilterProp="label"
              options={channels.map((channel) => ({
                value: channel.id,
                label: `${channel.channel_code} - ${channel.company_name}`,
              }))}
            />
          </Form.Item>
          <Space style={{ width: '100%' }} size="middle" wrap>
            <Form.Item
              name="user_id"
              label="负责人"
              rules={[{ required: true, message: '请选择负责人' }]}
            >
              <Select
                disabled={!(user?.role === 'admin' || user?.role === 'business')}
                style={{ width: 180 }}
                options={
                  user?.role === 'admin' || user?.role === 'business'
                    ? users.map((item) => ({ value: item.id, label: item.name }))
                    : [{ value: user?.id, label: user?.name || '当前用户' }]
                }
              />
            </Form.Item>
            <Form.Item name="plan_type" label="计划类型" rules={[{ required: true, message: '请选择计划类型' }]}>
              <Select
                style={{ width: 140 }}
                options={[
                  { value: 'monthly', label: '月度' },
                  { value: 'weekly', label: '周度' },
                ]}
              />
            </Form.Item>
            <Form.Item name="status" label="状态" rules={[{ required: true, message: '请选择状态' }]}>
              <Select
                style={{ width: 140 }}
                options={[
                  { value: 'planned', label: '计划中' },
                  { value: 'in-progress', label: '进行中' },
                  { value: 'completed', label: '已完成' },
                  { value: 'archived', label: '已归档' },
                ]}
              />
            </Form.Item>
          </Space>
          <Form.Item
            name="plan_period"
            label="计划周期"
            rules={[{ required: true, message: '请输入计划周期' }]}
          >
            <Input placeholder="例如：2026-04 或 2026-W17" />
          </Form.Item>
          <Form.Item
            name="plan_content"
            label="培训内容"
            rules={[{ required: true, message: '请输入培训内容' }]}
          >
            <Input.TextArea rows={4} placeholder="填写培训主题、课程内容或培训安排" />
          </Form.Item>
          <Form.Item name="execution_status" label="执行情况">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="key_obstacles" label="关键阻碍">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="next_steps" label="下一步计划">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </Space>
  );
};

export default ChannelTrainingPage;
