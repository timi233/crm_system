import React, { useEffect } from 'react';
import { Form, Input, Select, DatePicker, Button, Space, Cascader, App, Row, Col } from 'antd';
import { useRegionCascader, useDictItems } from '../../hooks/useDictItems';
import { useUsers } from '../../hooks/useUsers';
import { useChannels } from '../../hooks/useChannels';
import api from '../../services/api';
import PageModal from '../common/PageModal';

const { Option } = Select;
const { TextArea } = Input;

interface CustomerModalProps {
  visible: boolean;
  customer?: any;
  onSave?: (customer: any) => void;
  onCancel: () => void;
}

const checkCreditCodeExists = async (creditCode: string, excludeId?: number): Promise<boolean> => {
  try {
    const params = new URLSearchParams({ credit_code: creditCode });
    if (excludeId) params.append('exclude_id', String(excludeId));
    const response = await api.get(`/customers/check-credit-code?${params.toString()}`);
    return response.data.exists;
  } catch (error) {
    return false;
  }
};

const CustomerModal: React.FC<CustomerModalProps> = ({ visible, customer, onSave, onCancel }) => {
  const [form] = Form.useForm();
  const { message } = App.useApp();

  const { data: regionOptions = [] } = useRegionCascader();
  const { data: industryItems = [] } = useDictItems('客户行业');
  const { data: statusItems = [] } = useDictItems('客户状态');
  const { data: users = [] } = useUsers();
  const { data: channels = [] } = useChannels();

  const industryOptions = industryItems.map(item => ({ value: item.name, label: item.name }));
  const statusOptions = statusItems.map(item => ({ value: item.name, label: item.name }));
  const userOptions = users.map(user => ({ value: user.id, label: user.name }));
  const channelOptions = channels.map(channel => ({ value: channel.id, label: channel.company_name }));

  useEffect(() => {
    if (visible && customer) {
      const regionArray = customer.customer_region ? customer.customer_region.split('/') : [];
      form.setFieldsValue({
        ...customer,
        customer_region: regionArray.length > 0 ? regionArray : undefined,
      });
    } else if (visible) {
      form.resetFields();
    }
  }, [visible, customer, form]);

  const onFinish = async (values: any) => {
    try {
      const submitData = {
        ...values,
        customer_region: values.customer_region ? values.customer_region.join('/') : '',
        maintenance_expiry: values.maintenance_expiry?.format?.('YYYY-MM-DD'),
      };

      if (onSave) {
        await onSave(submitData);
      }
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  return (
    <PageModal
      title={customer ? '编辑客户资料' : '建立新客户档案'}
      width={720}
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
        <Form.Item
          label="客户名称"
          name="customer_name"
          rules={[{ required: true, message: '请输入客户名称' }]}
        >
          <Input placeholder="请录入公司或单位完整名称" />
        </Form.Item>

        <Form.Item
          label="统一社会信用代码"
          name="credit_code"
          rules={[
            { required: true, message: '请输入统一社会信用代码' },
            { len: 18, message: '统一社会信用代码应为18位' },
            {
              validator: async (_, value) => {
                if (!value || value.length !== 18) return Promise.resolve();
                const exists = await checkCreditCodeExists(value, customer?.id);
                if (exists) {
                  return Promise.reject(new Error('该统一社会信用代码已存在'));
                }
                return Promise.resolve();
              }
            }
          ]}
        >
          <Input placeholder="18位统一社会信用代码" maxLength={18} />
        </Form.Item>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="所属行业"
              name="customer_industry"
              rules={[{ required: true, message: '请选择客户行业' }]}
            >
              <Select placeholder="选择所属行业" showSearch>
                {industryOptions.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              label="所在区域"
              name="customer_region"
              rules={[{ required: true, message: '请选择区域' }]}
            >
              <Cascader
                options={regionOptions}
                placeholder="请选择省/市"
                showSearch
              />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="客户负责人"
              name="customer_owner_id"
              rules={[{ required: true, message: '请选择客户负责人' }]}
            >
              <Select placeholder="选择负责人" showSearch optionFilterProp="children">
                {userOptions.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="关联渠道" name="channel_id">
              <Select placeholder="选择协同渠道(可选)" showSearch optionFilterProp="children" allowClear>
                {channelOptions.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="主要联系人" name="main_contact">
              <Input placeholder="姓名" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="联系电话" name="phone">
              <Input placeholder="手机或座机" />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="客户状态"
              name="customer_status"
              rules={[{ required: true, message: '请选择客户状态' }]}
            >
              <Select placeholder="请选择当前状态">
                {statusOptions.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="维保到期时间" name="maintenance_expiry">
              <DatePicker
                placeholder="合同到期日期"
                style={{ width: '100%' }}
              />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item label="备注信息" name="notes">
          <TextArea rows={3} placeholder="如有其他补充信息请录入..." />
        </Form.Item>
      </Form>
    </PageModal>
  );
};

export default CustomerModal;
