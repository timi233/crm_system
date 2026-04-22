import React from 'react';
import { App, Form, Input, Button, Card, Typography, Divider } from 'antd';
import { LockOutlined, UserOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { loginStart, loginSuccess, loginFailure } from '../../store/slices/authSlice';
import authApi from '../../services/authService';

const { Title, Text } = Typography;

const Login: React.FC = () => {
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const onFinish = async (values: { email: string; password: string }) => {
    try {
      dispatch(loginStart());
      const { user, token } = await authApi.login(values);
      dispatch(loginSuccess({ user, token }));
      navigate('/');
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '登录失败，请检查邮箱和密码';
      dispatch(loginFailure(errorMessage));
    }
  };

  const handleFeishuLogin = async () => {
    try {
      const url = await authApi.getFeishuOAuthUrl();
      window.location.href = url;
    } catch (error: any) {
      message.error('获取飞书登录链接失败');
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <Card style={{ width: 400, padding: 24 }}>
        <Title level={2} style={{ textAlign: 'center', marginBottom: 24 }}>
          普悦销管系统
        </Title>
        <Form
          form={form}
          name="login"
          initialValues={{ remember: true }}
          onFinish={onFinish}
          autoComplete="off"
        >
          <Form.Item
            name="email"
            rules={[{ required: true, message: '请输入邮箱!' }, { type: 'email', message: '请输入有效的邮箱地址!' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="邮箱" />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码!' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" block size="large">
              登录
            </Button>
          </Form.Item>
        </Form>
        
        <Divider plain>
          <Text type="secondary">其他登录方式</Text>
        </Divider>
        
        <Button 
          block 
          size="large"
          onClick={handleFeishuLogin}
          style={{ marginTop: 16 }}
        >
          飞书登录
        </Button>
      </Card>
    </div>
  );
};

export default Login;
