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
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Decorative background elements */}
      <div style={{
        position: 'absolute',
        top: '-10%',
        right: '-5%',
        width: '40%',
        height: '40%',
        background: 'radial-gradient(circle, rgba(0, 82, 204, 0.05) 0%, transparent 70%)',
        zIndex: 0
      }} />
      <div style={{
        position: 'absolute',
        bottom: '-10%',
        left: '-5%',
        width: '40%',
        height: '40%',
        background: 'radial-gradient(circle, rgba(102, 126, 234, 0.05) 0%, transparent 70%)',
        zIndex: 0
      }} />

      <Card style={{
        width: 440,
        padding: '24px 16px',
        borderRadius: '16px',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        border: '1px solid white',
        zIndex: 1
      }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            background: 'var(--primary-gradient)',
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            margin: '0 auto 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontWeight: 'bold',
            fontSize: '24px',
            boxShadow: '0 4px 12px rgba(0, 82, 204, 0.2)'
          }}>
            P
          </div>
          <Title level={2} style={{ margin: '0 0 8px', fontWeight: 800, letterSpacing: '-1px' }}>
            普悦销管系统
          </Title>
          <Text type="secondary" style={{ fontSize: '15px' }}>
            现代化的CRM管理解决方案
          </Text>
        </div>

        <Form
          form={form}
          name="login"
          initialValues={{ remember: true }}
          onFinish={onFinish}
          autoComplete="off"
          layout="vertical"
        >
          <Form.Item
            name="email"
            label="邮箱地址"
            rules={[{ required: true, message: '请输入邮箱!' }, { type: 'email', message: '请输入有效的邮箱地址!' }]}
          >
            <Input
              prefix={<UserOutlined style={{ color: '#94a3b8' }} />}
              placeholder="name@company.com"
              size="large"
              style={{ borderRadius: '8px' }}
            />
          </Form.Item>

          <Form.Item
            name="password"
            label="密码"
            rules={[{ required: true, message: '请输入密码!' }]}
          >
            <Input.Password
              prefix={<LockOutlined style={{ color: '#94a3b8' }} />}
              placeholder="••••••••"
              size="large"
              style={{ borderRadius: '8px' }}
            />
          </Form.Item>

          <Form.Item style={{ marginTop: 8 }}>
            <Button
              type="primary"
              htmlType="submit"
              block
              size="large"
              className="btn--gradient"
              style={{ height: '48px', fontSize: '16px', fontWeight: 600 }}
            >
              登 录
            </Button>
          </Form.Item>
        </Form>

        <Divider plain>
          <Text type="secondary" style={{ fontSize: '13px' }}>快速登录</Text>
        </Divider>

        <Button
          block
          size="large"
          onClick={handleFeishuLogin}
          style={{
            marginTop: 8,
            height: '48px',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '10px',
            fontWeight: 500,
            border: '1px solid #e2e8f0',
            background: 'white'
          }}
        >
          <img
            src="https://lf3-static.bytednsdoc.com/obj/eden-cn/aphqeh7u3vhu_zlp/ljhwZthlaukjlkulzlp/feishu-logo.png"
            alt="Feishu"
            style={{ width: '20px' }}
          />
          飞书账号登录
        </Button>
      </Card>
    </div>
  );
};

export default Login;
