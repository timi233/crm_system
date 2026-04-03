import React, { useEffect } from 'react';
import { Card, Form, Input, Select, Button, Space, DatePicker, InputNumber, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useCreateOpportunity } from '../../hooks/useOpportunities';
import { useDictItems } from '../../hooks/useDictItems';
import { useCustomers } from '../../hooks/useCustomers';
import { useUsers } from '../../hooks/useUsers';
import { useChannels } from '../../hooks/useChannels';

const { Option } = Select;
const { TextArea } = Input;

const OpportunityForm: React.FC = () => {
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const { data: stageItems = [] } = useDictItems('商机阶段');
  const { data: sourceItems = [] } = useDictItems('商机来源');
  const { data: customers = [] } = useCustomers();
  const { data: users = [] } = useUsers();
  const { data: channels = [] } = useChannels();

  const stageOptions = stageItems.map(item => ({ value: item.name, label: item.name }));
  const sourceOptions = sourceItems.map(item => ({ value: item.name, label: item.name }));
  const customerOptions = customers.map(c => ({ value: c.id, label: c.customer_name }));
  const userOptions = users.map(u => ({ value: u.id, label: u.name }));
  const channelOptions = channels.map(ch => ({ value: ch.id, label: ch.company_name }));

  const createMutation = useCreateOpportunity();

  useEffect(() => {
    form.setFieldsValue({ opportunity_stage: '需求方案', lead_grade: 'B' });
  }, [form]);

  const onFinish = async (values: any) => {
    try {
      const payload = {
        ...values,
        expected_close_date: values.expected_close_date?.format?.('YYYY-MM-DD') || values.expected_close_date,
      };
      await createMutation.mutateAsync(payload);
      message.success('商机创建成功');
      navigate('/opportunities');
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  return (
    <Card title="新建商机" style={{ maxWidth: 800 }}>
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        disabled={createMutation.isPending}
      >
        <Form.Item
          name="opportunity_name"
          label="商机名称"
          rules={[{ required: true, message: '请输入商机名称' }]}
        >
          <Input placeholder="请输入商机名称" />
        </Form.Item>

        <Form.Item
          name="terminal_customer_id"
          label="终端客户"
          rules={[{ required: true, message: '请选择终端客户' }]}
        >
          <Select placeholder="请选择终端客户" showSearch optionFilterProp="children">
            {customerOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>{opt.label}</Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="sales_owner_id"
          label="销售负责人"
          rules={[{ required: true, message: '请选择销售负责人' }]}
        >
          <Select placeholder="请选择销售负责人" showSearch optionFilterProp="children">
            {userOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>{opt.label}</Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="opportunity_stage"
          label="商机阶段"
          rules={[{ required: true, message: '请选择商机阶段' }]}
        >
          <Select placeholder="请选择商机阶段">
            {stageOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>{opt.label}</Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="opportunity_source"
          label="商机来源"
          rules={[{ required: true, message: '请选择商机来源' }]}
        >
          <Select placeholder="请选择商机来源">
            {sourceOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>{opt.label}</Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="lead_grade"
          label="线索等级"
          rules={[{ required: true, message: '请选择线索等级' }]}
        >
          <Select placeholder="请选择线索等级">
            <Option value="A">A</Option>
            <Option value="B">B</Option>
            <Option value="C">C</Option>
            <Option value="D">D</Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="expected_contract_amount"
          label="预计合同金额"
          rules={[{ required: true, message: '请输入预计合同金额' }]}
        >
          <InputNumber
            placeholder="请输入预计合同金额"
            style={{ width: '100%' }}
            min={0}
            precision={2}
          />
        </Form.Item>

        <Form.Item name="expected_close_date" label="预计关闭日期">
          <DatePicker style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item name="channel_id" label="关联渠道">
          <Select placeholder="请选择渠道(可选)" showSearch optionFilterProp="children" allowClear>
            {channelOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>{opt.label}</Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item name="notes" label="备注">
          <TextArea rows={3} placeholder="请输入备注信息" />
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={createMutation.isPending}>
              创建商机
            </Button>
            <Button onClick={() => navigate('/opportunities')}>
              取消
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default OpportunityForm;