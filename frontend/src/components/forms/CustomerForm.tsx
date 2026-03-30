import React, { useEffect } from 'react';
import { Form, Input, Select, DatePicker, Button, Card, Space } from 'antd';
import { CustomerCreate, CustomerRead } from '../../types/customer';
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '../../services/api';
import { useNavigate } from 'react-router-dom';

const { Option } = Select;
const { TextArea } = Input;

interface CustomerFormProps {
  customer?: CustomerRead;
  onSuccess?: (customer: CustomerRead) => void;
  onCancel?: () => void;
}

const CustomerForm: React.FC<CustomerFormProps> = ({ customer, onSuccess, onCancel }) => {
  const [form] = Form.useForm<CustomerCreate>();
  const navigate = useNavigate();
  
  // Fetch users for customer owner selection
  const { data: users = [], isLoading: loadingUsers } = useQuery({
    queryKey: ['users'],
    queryFn: () => api.get('/users').then(res => res.data),
  });
  
  // Create customer mutation
  const createCustomerMutation = useMutation({
    mutationFn: (customerData: CustomerCreate) => 
      api.post('/customers', customerData).then(res => res.data),
    onSuccess: (newCustomer) => {
      if (onSuccess) {
        onSuccess(newCustomer);
      } else {
        // If no onSuccess callback provided, navigate back to customer list
        navigate('/customers');
      }
    },
  });
  
  // Update customer mutation  
  const updateCustomerMutation = useMutation({
    mutationFn: (customerData: CustomerCreate) => 
      api.put(`/customers/${customer?.id}`, customerData).then(res => res.data),
    onSuccess: (updatedCustomer) => {
      if (onSuccess) {
        onSuccess(updatedCustomer);
      } else {
        // If no onSuccess callback provided, navigate back to customer list
        navigate('/customers');
      }
    },
  });
  
  useEffect(() => {
    if (customer) {
      form.setFieldsValue(customer);
    }
  }, [customer, form]);
  
  const onFinish = (values: CustomerCreate) => {
    if (customer) {
      updateCustomerMutation.mutate(values);
    } else {
      createCustomerMutation.mutate(values);
    }
  };
  
  const industryOptions = [
    'Manufacturing',
    'Finance', 
    'Government',
    'Healthcare',
    'Education',
    'Energy',
    'Other'
  ];
  
  const statusOptions = [
    'Potential',
    'Active',
    'Existing', 
    'Lost'
  ];
  
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
          <Input placeholder="请输入工商注册全称" />
        </Form.Item>
        
        <Form.Item label="客户简称" name="customer_nickname">
          <Input placeholder="日常沟通用简称" />
        </Form.Item>
        
        <Form.Item
          label="客户行业"
          name="customer_industry"
          rules={[{ required: true, message: '请选择客户行业' }]}
        >
          <Select placeholder="请选择客户所属行业">
            {industryOptions.map(industry => (
              <Option key={industry} value={industry}>
                {industry}
              </Option>
            ))}
          </Select>
        </Form.Item>
        
        <Form.Item
          label="客户区域"
          name="customer_region"
          rules={[{ required: true, message: '请输入客户所在区域' }]}
        >
          <Input placeholder="按城市填写，如：济南、青岛等" />
        </Form.Item>
        
        <Form.Item
          label="客户负责人"
          name="customer_owner_id"
          rules={[{ required: true, message: '请选择客户负责人' }]}
        >
          <Select 
            placeholder="选择负责跟进此客户的销售"
            loading={loadingUsers}
          >
            {users.map(user => (
              <Option key={user.id} value={user.id}>
                {user.name}
              </Option>
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
            {statusOptions.map(status => (
              <Option key={status} value={status}>
                {status}
              </Option>
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