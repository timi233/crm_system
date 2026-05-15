import React, { useState } from 'react';
import { App, Table, Button, Space, Modal, Form, Input, Select, InputNumber, Switch, Tag, Row, Col } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useAlertRules, useCreateAlertRule, useUpdateAlertRule, useDeleteAlertRule, AlertRule } from '../../hooks/useAlerts';
import PageScaffold from '../../components/common/PageScaffold';
import PageModal from '../../components/common/PageModal';

const { Option } = Select;

const AlertRuleList: React.FC = () => {
  const { message, modal } = App.useApp();
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
    form.setFieldsValue({ is_active: true, severity: 'warning' });
    setIsModalVisible(true);
  };

  const handleEdit = (rule: AlertRule) => {
    setEditingRule(rule);
    form.setFieldsValue(rule);
    setIsModalVisible(true);
  };

  const handleDelete = (id: number) => {
    modal.confirm({
      title: '确定删除该预警规则吗？',
      content: '删除后相关的实时监控将停止。',
      okType: 'danger',
      onOk: async () => {
        try {
          await deleteMutation.mutateAsync(id);
          message.success('规则已删除');
        } catch (error) {}
      }
    });
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      if (editingRule) {
        await updateMutation.mutateAsync({ id: editingRule.id, rule: values });
        message.success('规则已更新');
      } else {
        await createMutation.mutateAsync(values);
        message.success('规则已创建');
      }
      setIsModalVisible(false);
      form.resetFields();
    } catch (error) {}
  };

  const columns = [
    {
      title: '规则名称',
      dataIndex: 'rule_name',
      key: 'rule_name',
    },
    {
      title: '预警对象',
      dataIndex: 'entity_type',
      key: 'entity_type',
      render: (type: string) => <Tag color="blue" style={{ border: 'none' }}>{type}</Tag>,
    },
    {
      title: '严重程度',
      dataIndex: 'severity',
      key: 'severity',
      render: (s: string) => <Tag color={s === 'danger' ? 'red' : 'orange'} style={{ border: 'none' }}>{s}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => <Tag color={active ? 'success' : 'default'} style={{ border: 'none' }}>{active ? '运行中' : '已停止'}</Tag>,
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: AlertRule) => (
        <Space size="middle">
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)}>删除</Button>
        </Space>
      ),
    },
  ];

  return (
    <PageScaffold
      title="预警规则配置"
      breadcrumbItems={[{ title: '首页' }, { title: '系统配置' }, { title: '预警规则' }]}
      extra={
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleCreate}
          size="large"
          className="btn--gradient"
          style={{ height: '40px', padding: '0 20px' }}
        >
          新建规则
        </Button>
      }
    >
      <Table
        columns={columns}
        dataSource={rules}
        loading={isLoading}
        rowKey="id"
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条数据`,
        }}
        className="customer-table"
        bordered={false}
      />

      <PageModal
        title={editingRule ? '编辑预警规则' : '创建自动预警逻辑'}
        open={isModalVisible}
        onClose={() => setIsModalVisible(false)}
        width={640}
        footer={[
          <Button key="cancel" onClick={() => setIsModalVisible(false)}>
            取消
          </Button>,
          <Button
            key="submit"
            type="primary"
            className="btn--gradient"
            onClick={handleSave}
            loading={createMutation.isPending || updateMutation.isPending}
          >
            保存并应用
          </Button>
        ]}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="rule_name"
            label="规则名称"
            rules={[{ required: true, message: '请输入规则名称!' }]}
          >
            <Input placeholder="例如：合同到期 30 天预警" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="entity_type"
                label="应用对象"
                rules={[{ required: true, message: '请选择应用对象!' }]}
              >
                <Select placeholder="选择监控的业务实体">
                  <Option value="contract">合同</Option>
                  <Option value="lead">线索</Option>
                  <Option value="opportunity">商机</Option>
                  <Option value="project">项目</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="severity"
                label="预警级别"
                rules={[{ required: true, message: '请选择级别!' }]}
              >
                <Select>
                  <Option value="warning">普通预警</Option>
                  <Option value="danger">紧急预警</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="is_active" label="当前状态" valuePropName="checked">
            <Switch checkedChildren="运行" unCheckedChildren="停止" />
          </Form.Item>

          <Form.Item name="condition_json" label="触发条件 (JSON)">
            <Input.TextArea rows={4} placeholder='{"field": "expiry_date", "operator": "less_than", "value": 30}' />
          </Form.Item>

          <Form.Item name="description" label="规则说明">
            <Input.TextArea rows={2} placeholder="规则的详细业务背景说明..." />
          </Form.Item>
        </Form>
      </PageModal>
    </PageScaffold>
  );
};

export default AlertRuleList;
