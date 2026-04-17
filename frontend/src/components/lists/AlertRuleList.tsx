import React, { useState } from 'react';
import { Card, Table, Button, Space, Modal, Form, Input, Select, InputNumber, Switch, message, Popconfirm, Tag, Drawer } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, WarningOutlined } from '@ant-design/icons';
import { 
  useAlertRules, 
  useCreateAlertRule, 
  useUpdateAlertRule, 
  useDeleteAlertRule,
  AlertRule,
  AlertRuleCreate 
} from '../../hooks/useAlerts';

const { Option } = Select;
const { TextArea } = Input;

const ENTITY_TYPES = [
  { value: 'opportunities', label: '商机' },
  { value: 'contracts', label: '合同' },
  { value: 'leads', label: '线索' },
  { value: 'follow-ups', label: '跟进记录' },
];

const PRIORITIES = [
  { value: 'high', label: '高', color: 'red' },
  { value: 'medium', label: '中', color: 'orange' },
  { value: 'low', label: '低', color: 'blue' },
];

const RULE_TYPES = [
  { value: '预警', label: '预警' },
  { value: '提醒', label: '提醒' },
];

const AlertRuleList: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingRule, setEditingRule] = useState<AlertRule | null>(null);
  const [form] = Form.useForm();

  const { data: rules = [], isLoading } = useAlertRules();
  const createMutation = useCreateAlertRule();
  const updateMutation = useUpdateAlertRule();
  const deleteMutation = useDeleteAlertRule();

  const handleCreate = () => {
    setEditingRule(null);
    form.resetFields();
    form.setFieldsValue({ priority: 'medium', threshold_days: 0, threshold_amount: 0, is_active: true });
    setIsModalVisible(true);
  };

  const handleEdit = (rule: AlertRule) => {
    setEditingRule(rule);
    form.setFieldsValue(rule);
    setIsModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteMutation.mutateAsync(id);
      message.success('删除成功');
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '删除失败');
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      const payload: AlertRuleCreate = {
        rule_code: values.rule_code,
        rule_name: values.rule_name,
        rule_type: values.rule_type,
        entity_type: values.entity_type,
        priority: values.priority,
        threshold_days: values.threshold_days,
        threshold_amount: values.threshold_amount,
        description: values.description,
        is_active: values.is_active,
      };

      if (editingRule) {
        await updateMutation.mutateAsync({ id: editingRule.id, rule: payload });
        message.success('更新成功');
      } else {
        await createMutation.mutateAsync(payload);
        message.success('创建成功');
      }

      setIsModalVisible(false);
      form.resetFields();
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  const getPriorityTag = (priority: string) => {
    const config = PRIORITIES.find(p => p.value === priority) || PRIORITIES[1];
    return <Tag color={config.color}>{config.label}</Tag>;
  };

  const getEntityTypeLabel = (entityType: string) => {
    const config = ENTITY_TYPES.find(e => e.value === entityType);
    return config?.label || entityType;
  };

  const columns = [
    {
      title: '规则编码',
      dataIndex: 'rule_code',
      key: 'rule_code',
      width: 150,
    },
    {
      title: '规则名称',
      dataIndex: 'rule_name',
      key: 'rule_name',
      width: 150,
    },
    {
      title: '类型',
      dataIndex: 'rule_type',
      key: 'rule_type',
      width: 80,
    },
    {
      title: '关联实体',
      dataIndex: 'entity_type',
      key: 'entity_type',
      width: 100,
      render: (entityType: string) => getEntityTypeLabel(entityType),
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      render: (priority: string) => getPriorityTag(priority),
    },
    {
      title: '阈值(天)',
      dataIndex: 'threshold_days',
      key: 'threshold_days',
      width: 80,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'default'}>{isActive ? '启用' : '禁用'}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: AlertRule) => (
        <Space size="small">
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Popconfirm
            title="确定删除该规则吗？"
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

  return (
    <Card
      title={
        <Space>
          <WarningOutlined />
          预警中心
        </Space>
      }
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建规则
        </Button>
      }
    >
      <Table
        columns={columns}
        dataSource={rules}
        loading={isLoading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        scroll={{ x: 1000 }}
      />

      <Drawer
        title={editingRule ? '编辑预警规则' : '新建预警规则'}
        open={isModalVisible}
        onClose={() => setIsModalVisible(false)}
        width={520}
        maskClosable={false}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="rule_code"
            label="规则编码"
            rules={[{ required: true, message: '请输入规则编码' }]}
          >
            <Input placeholder="如：OPP_STALLED" disabled={!!editingRule} />
          </Form.Item>

          <Form.Item
            name="rule_name"
            label="规则名称"
            rules={[{ required: true, message: '请输入规则名称' }]}
          >
            <Input placeholder="如：商机停滞预警" />
          </Form.Item>

          <Space style={{ width: '100%' }} size="large">
            <Form.Item
              name="rule_type"
              label="规则类型"
              rules={[{ required: true }]}
              style={{ width: 150 }}
            >
              <Select placeholder="选择类型">
                {RULE_TYPES.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              name="entity_type"
              label="关联实体"
              rules={[{ required: true }]}
              style={{ width: 150 }}
            >
              <Select placeholder="选择实体">
                {ENTITY_TYPES.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              name="priority"
              label="优先级"
              rules={[{ required: true }]}
              style={{ width: 120 }}
            >
              <Select placeholder="选择优先级">
                {PRIORITIES.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>
          </Space>

          <Space style={{ width: '100%' }} size="large">
            <Form.Item
              name="threshold_days"
              label="阈值 (天)"
              style={{ width: 150 }}
            >
              <InputNumber placeholder="天数" style={{ width: '100%' }} min={0} />
            </Form.Item>

            <Form.Item
              name="threshold_amount"
              label="阈值 (金额)"
              style={{ width: 150 }}
            >
              <InputNumber placeholder="金额" style={{ width: '100%' }} min={0} />
            </Form.Item>
          </Space>

          <Form.Item name="description" label="描述">
            <TextArea rows={3} placeholder="规则描述" />
          </Form.Item>

          <Form.Item name="is_active" label="启用状态" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>
          
          <Form.Item>
            <Button type="primary" onClick={handleModalOk} loading={createMutation.isPending || updateMutation.isPending} block>
              保存
            </Button>
          </Form.Item>
        </Form>
      </Drawer>
    </Card>
  );
};

export default AlertRuleList;