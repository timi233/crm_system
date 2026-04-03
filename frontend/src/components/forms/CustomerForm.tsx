import React, { useEffect } from 'react';
import { Form, Input, Select, DatePicker, Button, Card, Space, Cascader } from 'antd';
import { CustomerCreate, CustomerRead } from '../../types/customer';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../services/api';
import { useNavigate } from 'react-router-dom';
import { useRegionCascader, useDictItems } from '../../hooks/useDictItems';
import { useUsers } from '../../hooks/useUsers';
import { useChannels } from '../../hooks/useChannels';

const { Option } = Select;
const { TextArea } = Input;

interface CustomerFormProps {
  customer?: CustomerRead;
  onSuccess?: (customer: CustomerRead) => void;
  onCancel?: () => void;
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

interface CustomerFormValues {
  customer_name: string;
  credit_code: string;
  customer_industry: string;
  customer_region?: string[];
  customer_owner_id: number;
  channel_id?: number;
  main_contact?: string;
  phone?: string;
  customer_status: string;
  maintenance_expiry?: any;
  notes?: string;
}

const CustomerForm: React.FC<CustomerFormProps> = ({ customer, onSuccess, onCancel }) => {
  const [form] = Form.useForm<CustomerFormValues>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  const { data: regionOptions = [] } = useRegionCascader();
  const { data: industryItems = [] } = useDictItems('客户行业');
  const { data: statusItems = [] } = useDictItems('客户状态');
  const { data: users = [] } = useUsers();
  const { data: channels = [] } = useChannels();

  const industryOptions = industryItems.map(item => ({ value: item.name, label: item.name }));
  const statusOptions = statusItems.map(item => ({ value: item.name, label: item.name }));
  const userOptions = users.map(user => ({ value: user.id, label: user.name }));
  const channelOptions = channels.map(channel => ({ value: channel.id, label: channel.company_name }));
  
  const createCustomerMutation = useMutation({
    mutationFn: (customerData: CustomerCreate) => 
      api.post('/customers', customerData).then(res => res.data),
    onSuccess: (newCustomer) => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      if (onSuccess) {
        onSuccess(newCustomer);
      } else {
        navigate('/customers');
      }
    },
  });
  
  const updateCustomerMutation = useMutation({
    mutationFn: (customerData: CustomerCreate) => 
      api.put(`/customers/${customer?.id}`, customerData).then(res => res.data),
    onSuccess: (updatedCustomer) => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      if (onSuccess) {
        onSuccess(updatedCustomer);
      } else {
        navigate('/customers');
      }
    },
  });
  
  useEffect(() => {
    if (customer) {
      const regionArray = customer.customer_region ? customer.customer_region.split('/') : [];
      form.setFieldsValue({
        ...customer,
        customer_region: regionArray.length > 0 ? regionArray : undefined,
      });
    }
  }, [customer, form]);
  
  const onFinish = (values: CustomerFormValues) => {
    const submitData: CustomerCreate = {
      ...values,
      customer_region: values.customer_region ? values.customer_region.join('/') : '',
      maintenance_expiry: values.maintenance_expiry?.format?.('YYYY-MM-DD'),
    };
    
    if (customer) {
      updateCustomerMutation.mutate(submitData);
    } else {
      createCustomerMutation.mutate(submitData);
    }
  };
  
  return (
    <Card 
      title={customer ? '编辑客户' : '创建新客户'}
      style={{ maxWidth: 800 }}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        disabled={createCustomerMutation.isPending || updateCustomerMutation.isPending}
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
            <Button 
              type="primary" 
              htmlType="submit"
              loading={createCustomerMutation.isPending || updateCustomerMutation.isPending}
            >
              {customer ? '更新客户' : '创建客户'}
            </Button>
            <Button onClick={onCancel || (() => navigate('/customers'))}>取消</Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default CustomerForm;