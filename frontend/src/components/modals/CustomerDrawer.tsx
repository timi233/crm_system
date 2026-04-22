import React, { useEffect } from 'react';
import { Drawer, Form, Input, Select, DatePicker, Button, Space, Cascader, App } from 'antd';
import { useRegionCascader, useDictItems } from '../../hooks/useDictItems';
import { useUsers } from '../../hooks/useUsers';
import { useChannels } from '../../hooks/useChannels';
import api from '../../services/api';

const { Option } = Select;
const { TextArea } = Input;

interface CustomerDrawerProps {
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

const CustomerDrawer: React.FC<CustomerDrawerProps> = ({ visible, customer, onSave, onCancel }) => {
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
    <Drawer
      title={customer ? '编辑客户' : '创建新客户'}
      width={600}
      open={visible}
      onClose={onCancel}
      destroyOnClose
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
          <Input placeholder="请输入客户全称" />
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
        
        <Form.Item
          label="客户行业"
          name="customer_industry"
          rules={[{ required: true, message: '请选择客户行业' }]}
        >
          <Select placeholder="请选择客户所属行业" showSearch>
            {industryOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>{opt.label}</Option>
            ))}
          </Select>
        </Form.Item>
        
        <Form.Item
          label="客户区域"
          name="customer_region"
          rules={[{ required: true, message: '请选择客户所在区域' }]}
        >
          <Cascader
            options={regionOptions}
            placeholder="请选择省/市"
            showSearch
          />
        </Form.Item>
        
        <Form.Item
          label="客户负责人"
          name="customer_owner_id"
          rules={[{ required: true, message: '请选择客户负责人' }]}
        >
          <Select placeholder="选择负责跟进此客户的销售" showSearch optionFilterProp="children">
            {userOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>{opt.label}</Option>
            ))}
          </Select>
        </Form.Item>
        
        <Form.Item label="关联渠道" name="channel_id">
          <Select placeholder="请选择渠道(可选)" showSearch optionFilterProp="children" allowClear>
            {channelOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>{opt.label}</Option>
            ))}
          </Select>
        </Form.Item>
        
        <Form.Item label="主要联系人" name="main_contact">
          <Input placeholder="客户侧主要对接人姓名" />
        </Form.Item>
        
        <Form.Item label="联系电话" name="phone">
          <Input placeholder="联系电话" />
        </Form.Item>
        
        <Form.Item
          label="客户状态"
          name="customer_status"
          rules={[{ required: true, message: '请选择客户状态' }]}
        >
          <Select placeholder="客户当前状态">
            {statusOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>{opt.label}</Option>
            ))}
          </Select>
        </Form.Item>
        
        <Form.Item label="维保到期时间" name="maintenance_expiry">
          <DatePicker 
            placeholder="选择维保合同到期日" 
            style={{ width: '100%' }}
          />
        </Form.Item>
        
        <Form.Item label="备注" name="notes">
          <TextArea rows={4} placeholder="其他备注信息" />
        </Form.Item>
        
        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit">
              {customer ? '更新客户' : '创建客户'}
            </Button>
            <Button onClick={onCancel}>取消</Button>
          </Space>
        </Form.Item>
      </Form>
    </Drawer>
  );
};

export default CustomerDrawer;