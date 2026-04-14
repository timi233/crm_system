import React, { useEffect } from 'react';
import { Card, Form, Input, Select, Button, Space, Checkbox, InputNumber, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useCreateLead } from '../../hooks/useLeads';
import { useDictItems } from '../../hooks/useDictItems';
import { useCustomers } from '../../hooks/useCustomers';
import { useUsers } from '../../hooks/useUsers';

const { Option } = Select;
const { TextArea } = Input;

const LEAD_STAGES = ['初步接触', '意向沟通', '需求挖掘中'];

interface LeadFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
}

const LeadForm: React.FC<LeadFormProps> = ({ onSuccess, onCancel }) => {
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const { data: sourceItems = [] } = useDictItems('商机来源');
  const { data: customers = [] } = useCustomers();
  const { data: users = [] } = useUsers();

  const sourceOptions = sourceItems.map(item => ({ value: item.name, label: item.name }));
  const customerOptions = customers.map(c => ({ value: c.id, label: c.customer_name }));
  const userOptions = users.map(u => ({ value: u.id, label: u.name }));

  const createMutation = useCreateLead();

  useEffect(() => {
    form.setFieldsValue({ lead_stage: '初步接触', has_confirmed_requirement: false, has_confirmed_budget: false });
  }, [form]);

  const handleCustomerChange = (customerId: number) => {
    const customer = customers.find(c => c.id === customerId);
    if (customer) {
      form.setFieldsValue({
        contact_person: customer.main_contact || '',
        contact_phone: customer.phone || '',
      });
    }
  };

  const onFinish = async (values: any) => {
    try {
      await createMutation.mutateAsync(values);
      message.success('线索创建成功');
      if (onSuccess) {
        onSuccess();
      } else {
        navigate('/leads');
      }
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  return (
    <Card title="新建线索" style={{ maxWidth: 800 }}>
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        disabled={createMutation.isPending}
      >
        <Form.Item
          name="lead_name"
          label="线索名称"
          rules={[{ required: true, message: '请输入线索名称' }]}
        >
          <Input placeholder="请输入线索名称" />
        </Form.Item>

        <Form.Item
          name="terminal_customer_id"
          label="终端客户"
          rules={[{ required: true, message: '请选择终端客户' }]}
        >
          <Select
            placeholder="请选择终端客户"
            showSearch
            optionFilterProp="children"
            onChange={handleCustomerChange}
          >
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
          name="lead_stage"
          label="线索阶段"
          rules={[{ required: true, message: '请选择线索阶段' }]}
        >
          <Select placeholder="请选择线索阶段">
            {LEAD_STAGES.map(stage => (
              <Option key={stage} value={stage}>{stage}</Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item name="lead_source" label="线索来源">
          <Select placeholder="请选择线索来源" allowClear>
            {sourceOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>{opt.label}</Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item name="contact_person" label="联系人">
          <Input
            placeholder="选择终端客户后自动带入，也可手动修改"
          />
        </Form.Item>

        <Form.Item name="contact_phone" label="联系电话">
          <Input
            placeholder="选择终端客户后自动带入，也可手动修改"
          />
        </Form.Item>

        <Form.Item name="estimated_budget" label="预估预算">
          <InputNumber
            placeholder="请输入预估预算"
            style={{ width: '100%' }}
            min={0}
            precision={2}
          />
        </Form.Item>

        <Space style={{ marginBottom: 16 }}>
          <Form.Item name="has_confirmed_requirement" valuePropName="checked" noStyle>
            <Checkbox>已确认需求</Checkbox>
          </Form.Item>
          <Form.Item name="has_confirmed_budget" valuePropName="checked" noStyle>
            <Checkbox>已确认预算</Checkbox>
          </Form.Item>
        </Space>

        <Form.Item name="notes" label="备注">
          <TextArea rows={3} placeholder="请输入备注信息" />
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={createMutation.isPending}>
              创建线索
            </Button>
            <Button onClick={onCancel || (() => navigate('/leads'))}>
              取消
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default LeadForm;