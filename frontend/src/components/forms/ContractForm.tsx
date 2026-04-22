import React, { useEffect } from 'react';
import { App, Card, Form, Input, Select, Button, Space, DatePicker, InputNumber } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useCreateContract, ContractCreate } from '../../hooks/useContracts';
import { useProjects } from '../../hooks/useProjects';
import { useCustomers } from '../../hooks/useCustomers';
import { useChannels } from '../../hooks/useChannels';

const { Option } = Select;
const { TextArea } = Input;

const CONTRACT_DIRECTIONS = [
  { value: 'Downstream', label: '下游合同（销售）' },
  { value: 'Upstream', label: '上游合同（采购）' },
];

const CONTRACT_STATUSES = [
  { value: 'draft', label: '草稿' },
  { value: 'pending', label: '审批中' },
  { value: 'signed', label: '已签署' },
];

const ContractForm: React.FC = () => {
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const { data: projects = [] } = useProjects();
  const { data: customers = [] } = useCustomers();
  const { data: channels = [] } = useChannels();

  const projectOptions = projects.map(p => ({ value: p.id, label: `${p.project_code} - ${p.project_name}` }));
  const customerOptions = customers.map(c => ({ value: c.id, label: c.customer_name }));
  const channelOptions = channels.map(ch => ({ value: ch.id, label: ch.company_name }));

  const createMutation = useCreateContract();

  const contractDirection = Form.useWatch('contract_direction', form);

  useEffect(() => {
    form.setFieldsValue({ contract_direction: 'Downstream', contract_status: 'draft' });
  }, [form]);

  const onFinish = async (values: any) => {
    try {
      const payload: ContractCreate = {
        ...values,
        signing_date: values.signing_date?.format?.('YYYY-MM-DD'),
        effective_date: values.effective_date?.format?.('YYYY-MM-DD'),
        expiry_date: values.expiry_date?.format?.('YYYY-MM-DD'),
      };

      await createMutation.mutateAsync(payload);
      message.success('合同创建成功');
      navigate('/contracts');
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  return (
    <Card title="新建合同" style={{ maxWidth: 800 }}>
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        disabled={createMutation.isPending}
      >
        <Form.Item
          name="contract_name"
          label="合同名称"
          rules={[{ required: true, message: '请输入合同名称' }]}
        >
          <Input placeholder="请输入合同名称" />
        </Form.Item>

        <Form.Item
          name="project_id"
          label="关联项目"
          rules={[{ required: true, message: '请选择关联项目' }]}
        >
          <Select placeholder="请选择项目" showSearch optionFilterProp="children">
            {projectOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>{opt.label}</Option>
            ))}
          </Select>
        </Form.Item>

        <Space style={{ width: '100%' }} size="large">
          <Form.Item
            name="contract_direction"
            label="合同类型"
            rules={[{ required: true }]}
            style={{ width: 200 }}
          >
            <Select>
              {CONTRACT_DIRECTIONS.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="contract_status"
            label="合同状态"
            style={{ width: 150 }}
          >
            <Select>
              {CONTRACT_STATUSES.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="contract_amount"
            label="合同金额"
            rules={[{ required: true, message: '请输入合同金额' }]}
            style={{ width: 150 }}
          >
            <InputNumber placeholder="金额" style={{ width: '100%' }} min={0} precision={2} />
          </Form.Item>
        </Space>

        {contractDirection === 'Downstream' && (
          <Form.Item
            name="terminal_customer_id"
            label="终端客户"
            rules={[{ required: true, message: '下游合同必须关联客户' }]}
          >
            <Select placeholder="请选择终端客户" showSearch optionFilterProp="children">
              {customerOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>
        )}

        {contractDirection === 'Upstream' && (
          <Form.Item
            name="channel_id"
            label="渠道/供应商"
            rules={[{ required: true, message: '上游合同必须关联供应商' }]}
          >
            <Select placeholder="请选择渠道/供应商" showSearch optionFilterProp="children">
              {channelOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>
        )}

        <Space style={{ width: '100%' }} size="large">
          <Form.Item name="signing_date" label="签订日期" style={{ width: 150 }}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="effective_date" label="生效日期" style={{ width: 150 }}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="expiry_date" label="到期日期" style={{ width: 150 }}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
        </Space>

        <Form.Item name="notes" label="备注">
          <TextArea rows={3} placeholder="合同备注信息" />
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={createMutation.isPending}>
              创建合同
            </Button>
            <Button onClick={() => navigate('/contracts')}>
              取消
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default ContractForm;
