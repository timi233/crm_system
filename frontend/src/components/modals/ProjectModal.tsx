import React, { useState, useEffect } from 'react';
import { Form, Input, Select, Button, Space, DatePicker, InputNumber, App, Row, Col } from 'antd';
import { useDictItems } from '../../hooks/useDictItems';
import { useCustomers } from '../../hooks/useCustomers';
import { useUsers } from '../../hooks/useUsers';
import { useChannels } from '../../hooks/useChannels';
import EntityProductSelect from '../common/EntityProductSelect';
import PageModal from '../common/PageModal';

const { Option } = Select;
const { TextArea } = Input;

interface ProjectDrawerProps {
  visible: boolean;
  project?: any;
  onSave?: (project: any, productList?: any[]) => void;
  onCancel: () => void;
}

const PROJECT_STATUS_LIST = ['执行中', '已完成', '已终止'];

const ProjectDrawer: React.FC<ProjectDrawerProps> = ({ visible, project, onSave, onCancel }) => {
  const [form] = Form.useForm();
  const [productList, setProductList] = useState<any[]>([]);
  const { message } = App.useApp();

  const { data: productItems = [] } = useDictItems('产品品牌');
  const { data: customers = [] } = useCustomers();
  const { data: users = [] } = useUsers();
  const { data: channels = [] } = useChannels();

  const productOptions = productItems.map(item => ({ value: item.name, label: item.name }));
  const customerOptions = customers.map(c => ({ value: c.id, label: c.customer_name }));
  const userOptions = users.map(u => ({ value: u.id, label: u.name }));
  const channelOptions = channels.map(ch => ({ value: ch.id, label: ch.company_name }));

  useEffect(() => {
    if (visible && project) {
      form.setFieldsValue(project);
    } else if (visible) {
      form.resetFields();
      form.setFieldsValue({ project_status: '执行中', business_type: 'New Project' });
    }
  }, [visible, project, form]);

  const onFinish = async (values: any) => {
    try {
      const payload = {
        ...values,
        winning_date: values.winning_date?.format?.('YYYY-MM-DD') || values.winning_date,
        acceptance_date: values.acceptance_date?.format?.('YYYY-MM-DD') || values.acceptance_date,
        first_payment_date: values.first_payment_date?.format?.('YYYY-MM-DD') || values.first_payment_date,
      };

      if (onSave) {
        await onSave(payload, productList);
      }
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  return (
    <PageModal
      title={project ? '编辑项目详情' : '新建项目工程'}
      width={800}
      open={visible}
      onClose={onCancel}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          取消
        </Button>,
        <Button
          key="submit"
          type="primary"
          className="btn--gradient"
          onClick={() => form.submit()}
        >
          保存并同步
        </Button>
      ]}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
      >
        <Row gutter={16}>
          <Col span={24}>
            <Form.Item
              name="project_name"
              label="项目名称"
              rules={[{ required: true, message: '请输入项目名称' }]}
            >
              <Input placeholder="例如：某市电子政务云平台二期" />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="terminal_customer_id"
              label="终端客户"
              rules={[{ required: true, message: '请选择终端客户' }]}
            >
              <Select placeholder="搜索终端客户" showSearch optionFilterProp="children">
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
              rules={[{ required: true, message: '请选择销售负责人' }]}
            >
              <Select placeholder="选择负责人" showSearch optionFilterProp="children">
                {userOptions.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="business_type"
              label="业务类型"
              rules={[{ required: true, message: '请选择业务类型' }]}
            >
              <Select placeholder="选择类型">
                <Option value="New Project">新项目</Option>
                <Option value="Maintenance">维保项目</Option>
                <Option value="Upgrade">升级项目</Option>
                <Option value="Other">其他</Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="project_status"
              label="项目状态"
              rules={[{ required: true, message: '请选择项目状态' }]}
            >
              <Select placeholder="当前阶段">
                {PROJECT_STATUS_LIST.map(status => (
                  <Option key={status} value={status}>{status}</Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Form.Item name="products" label="涉及产品品牌">
          <Select
            mode="multiple"
            placeholder="请选择产品品牌（可多选）"
            allowClear
          >
            {productOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>{opt.label}</Option>
            ))}
          </Select>
        </Form.Item>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="downstream_contract_amount"
              label="下游合同金额"
              rules={[{ required: true, message: '请输入下游合同金额' }]}
            >
              <InputNumber
                placeholder="0.00"
                style={{ width: '100%' }}
                min={0}
                precision={2}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="upstream_procurement_amount" label="上游采购金额">
              <InputNumber
                placeholder="0.00"
                style={{ width: '100%' }}
                min={0}
                precision={2}
              />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="winning_date" label="中标日期">
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="channel_id" label="关联渠道">
              <Select placeholder="选择关联渠道" showSearch optionFilterProp="children" allowClear>
                {channelOptions.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <EntityProductSelect entityType="project" entityId={0} level={3} onChange={setProductList} />

        <Form.Item name="notes" label="项目备注">
          <TextArea rows={3} placeholder="请输入其他说明信息..." />
        </Form.Item>
      </Form>
    </PageModal>
  );
};

export default ProjectDrawer;
