import React, { useEffect } from 'react';
import { App, Form, Input, Select, Button, Space, DatePicker, InputNumber, Row, Col } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useCreateOpportunity } from '../../hooks/useOpportunities';
import { useDictItems } from '../../hooks/useDictItems';
import { useCustomers } from '../../hooks/useCustomers';
import { useUsers } from '../../hooks/useUsers';
import { useChannels } from '../../hooks/useChannels';
import PageScaffold from '../common/PageScaffold';
import { ArrowLeftOutlined } from '@ant-design/icons';

import { fromWan } from '../../utils/currency';

const { Option } = Select;
const { TextArea } = Input;

const OpportunityForm: React.FC = () => {
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const { data: stageItems = [] } = useDictItems('商机阶段');
  const { data: sourceItems = [] } = useDictItems('商机来源');
  const { data: productItems = [] } = useDictItems('产品品牌');
  const { data: customers = [] } = useCustomers();
  const { data: users = [] } = useUsers();
  const { data: channels = [] } = useChannels();

  const stageOptions = stageItems.map(item => ({ value: item.name, label: item.name }));
  const sourceOptions = sourceItems.map(item => ({ value: item.name, label: item.name }));
  const productOptions = productItems.map(item => ({ value: item.name, label: item.name }));
  const customerOptions = customers.map(c => ({ value: c.id, label: c.customer_name }));
  const userOptions = users.map(u => ({ value: u.id, label: u.name }));
  const channelOptions = channels.map(c => ({ value: c.id, label: c.company_name }));

  const createMutation = useCreateOpportunity();

  useEffect(() => {
    form.setFieldsValue({ opportunity_stage: '需求方案' });
  }, [form]);

  const onFinish = async (values: any) => {
    try {
      const payload = {
        ...values,
        expected_contract_amount: fromWan(values.expected_contract_amount)
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
    <PageScaffold
      title="录入新商机"
      breadcrumbItems={[{ title: '首页' }, { title: '商机管理', href: '/opportunities' }, { title: '新建商机' }]}
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
            name="opportunity_name"
            label={<span style={{ fontWeight: 600 }}>商机名称</span>}
            rules={[{ required: true, message: '请输入商机名称' }]}
          >
            <Input placeholder="例如：某医院信息化系统建设项目" size="large" />
          </Form.Item>

          <Row gutter={24}>
            <Col span={12}>
              <Form.Item
                name="terminal_customer_id"
                label="终端客户"
                rules={[{ required: true, message: '请选择客户' }]}
              >
                <Select placeholder="搜索客户" showSearch optionFilterProp="children" size="large">
                  {customerOptions.map(opt => (
                    <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="sales_owner_id"
                label="销售负责人"
                rules={[{ required: true, message: '请选择负责人' }]}
              >
                <Select placeholder="内部负责人" showSearch optionFilterProp="children" size="large">
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
                name="opportunity_stage"
                label="商机阶段"
                rules={[{ required: true, message: '请选择阶段' }]}
              >
                <Select placeholder="选择阶段" size="large">
                  {stageOptions.map(opt => (
                    <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="opportunity_source" label="商机来源">
                <Select placeholder="选择来源" allowClear size="large">
                  {sourceOptions.map(opt => (
                    <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={24}>
            <Col span={12}>
              <Form.Item name="channel_id" label="协同渠道 (合作伙伴)">
                <Select placeholder="选择渠道" allowClear showSearch optionFilterProp="label" options={channelOptions} size="large" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="expected_contract_amount" label="预计合同金额 (万元)">
                <InputNumber style={{ width: '100%' }} placeholder="0.0" precision={1} size="large" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="products" label="涉及产品品牌">
            <Select mode="multiple" placeholder="选择产品（可多选）" allowClear size="large">
              {productOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="expected_close_date" label="预计成交日期">
            <DatePicker style={{ width: '100%' }} size="large" />
          </Form.Item>

          <Form.Item name="notes" label="商机详情备注">
            <TextArea rows={4} placeholder="如有其他补充信息请录入..." />
          </Form.Item>

          <div style={{ marginTop: 32, paddingTop: 24, borderTop: '1px solid #f1f5f9', display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
            <Button size="large" onClick={() => navigate('/opportunities')}>
              取消返回
            </Button>
            <Button type="primary" size="large" className="btn--gradient" htmlType="submit" loading={createMutation.isPending}>
              确认录入商机
            </Button>
          </div>
        </Form>
      </div>
    </PageScaffold>
  );
};

export default OpportunityForm;
