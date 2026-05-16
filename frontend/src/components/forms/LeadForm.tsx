import React, { useEffect, useMemo } from 'react';
import { App, Form, Input, Select, Button, Space, Checkbox, InputNumber, Row, Col } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useCreateLead } from '../../hooks/useLeads';
import { useDictItems } from '../../hooks/useDictItems';
import { useCustomers } from '../../hooks/useCustomers';
import { useUsers } from '../../hooks/useUsers';
import { useChannels } from '../../hooks/useChannels';
import PageScaffold from '../common/PageScaffold';
import { ArrowLeftOutlined } from '@ant-design/icons';

import { fromWan } from '../../utils/currency';

const { Option } = Select;
const { TextArea } = Input;

const LEAD_STAGES = ['初步接触', '意向沟通', '需求挖掘中'];

interface LeadFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
}

const LeadForm: React.FC<LeadFormProps> = ({ onSuccess, onCancel }) => {
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const { data: sourceItems = [] } = useDictItems('商机来源');
  const { data: productItems = [] } = useDictItems('产品品牌');
  const { data: customers = [] } = useCustomers();
  const { data: users = [] } = useUsers();
  const { data: channels = [] } = useChannels();

  const sourceOptions = sourceItems.map(item => ({ value: item.name, label: item.name }));
  const productOptions = productItems.map(item => ({ value: item.name, label: item.name }));
  const customerOptions = customers.map(c => ({ value: c.id, label: c.customer_name }));
  const userOptions = users.map(u => ({ value: u.id, label: u.name }));
  const channelOptions = channels.map(c => ({ value: c.id, label: c.company_name }));

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
      const payload = {
        ...values,
        estimated_budget: fromWan(values.estimated_budget)
      };
      await createMutation.mutateAsync(payload);
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
    <PageScaffold
      title="录入销售线索"
      breadcrumbItems={[{ title: '首页' }, { title: '线索管理', href: '/leads' }, { title: '新建线索' }]}
      extra={<Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>返回</Button>}
    >
      <div style={{ maxWidth: 900, margin: '0 auto', background: 'white', padding: '32px 40px', borderRadius: '16px', border: '1px solid #f1f5f9', boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)' }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          disabled={createMutation.isPending}
        >
          <Form.Item
            name="lead_name"
            label={<span style={{ fontWeight: 600 }}>线索名称</span>}
            rules={[{ required: true, message: '请输入线索名称' }]}
          >
            <Input placeholder="请描述线索的核心内容，如：某公司系统扩容采购意向" size="large" />
          </Form.Item>

          <Row gutter={24}>
            <Col span={12}>
              <Form.Item
                name="terminal_customer_id"
                label="关联终端客户"
                rules={[{ required: true, message: '请选择终端客户' }]}
              >
                <Select
                  placeholder="搜索并选择客户"
                  showSearch
                  optionFilterProp="children"
                  onChange={handleCustomerChange}
                  size="large"
                >
                  {customerOptions.map(opt => (
                    <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="sales_owner_id"
                label="内部销售负责人"
                rules={[{ required: true, message: '请选择销售负责人' }]}
              >
                <Select placeholder="选择跟进此线索的销售" showSearch optionFilterProp="children" size="large">
                  {userOptions.map(opt => (
                    <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={24}>
            <Col span={12}>
              <Form.Item
                name="lead_stage"
                label="当前跟进阶段"
                rules={[{ required: true, message: '请选择线索阶段' }]}
              >
                <Select placeholder="选择阶段" size="large">
                  {LEAD_STAGES.map(stage => (
                    <Option key={stage} value={stage}>{stage}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="lead_source" label="线索来源方式">
                <Select placeholder="选择线索来源" allowClear size="large">
                  {sourceOptions.map(opt => (
                    <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={24}>
            <Col span={12}>
              <Form.Item
                name="source_channel_id"
                label="归因渠道（创建后不可改）"
              >
                <Select placeholder="选择最初来源渠道" allowClear showSearch optionFilterProp="label" options={channelOptions} size="large" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="channel_id"
                label="协同渠道（可随时修改）"
              >
                <Select placeholder="选择当前协同渠道" allowClear showSearch optionFilterProp="label" options={channelOptions} size="large" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="products" label="涉及产品品牌">
            <Select mode="multiple" placeholder="选择意向产品（可多选）" allowClear size="large">
              {productOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>

          <Row gutter={24}>
            <Col span={12}>
              <Form.Item name="contact_person" label="对接联系人">
                <Input placeholder="姓名" size="large" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="contact_phone" label="联系电话">
                <Input placeholder="手机或固件" size="large" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="estimated_budget" label="预估成交金额 (万元)">
            <InputNumber
              placeholder="0.0"
              style={{ width: '100%' }}
              min={0}
              precision={1}
              size="large"
            />
          </Form.Item>

          <div style={{ marginBottom: 24, padding: '16px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #f1f5f9' }}>
            <div style={{ marginBottom: 8, fontWeight: 600, fontSize: '13px', color: '#64748b' }}>关键信息确认</div>
            <Space size={32}>
              <Form.Item name="has_confirmed_requirement" valuePropName="checked" noStyle>
                <Checkbox>已确认客户需求</Checkbox>
              </Form.Item>
              <Form.Item name="has_confirmed_budget" valuePropName="checked" noStyle>
                <Checkbox>已确认项目预算</Checkbox>
              </Form.Item>
            </Space>
          </div>

          <Form.Item name="notes" label="备注说明">
            <TextArea rows={4} placeholder="如有其他补充信息请录入..." />
          </Form.Item>

          <div style={{ marginTop: 32, paddingTop: 24, borderTop: '1px solid #f1f5f9', display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
            <Button size="large" onClick={onCancel || (() => navigate('/leads'))}>
              取消并返回
            </Button>
            <Button type="primary" size="large" className="btn--gradient" htmlType="submit" loading={createMutation.isPending}>
              确认创建并入库
            </Button>
          </div>
        </Form>
      </div>
    </PageScaffold>
  );
};

export default LeadForm;
