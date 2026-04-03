import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Spin, Typography } from 'antd';
import { useDispatch } from 'react-redux';
import { loginStart, loginSuccess, loginFailure } from '../../store/slices/authSlice';
import authApi from '../../services/authService';

const { Text } = Typography;

const FeishuCallback: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const code = searchParams.get('code');
    if (code) {
      handleFeishuLogin(code);
    } else {
      navigate('/login');
    }
  }, [searchParams]);

  const handleFeishuLogin = async (code: string) => {
    try {
      dispatch(loginStart());
      const { user, token } = await authApi.feishuLogin(code);
      dispatch(loginSuccess({ user, token }));
      navigate('/');
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '飞书登录失败';
      dispatch(loginFailure(errorMessage));
      navigate('/login');
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', flexDirection: 'column' }}>
      <Spin size="large" />
      <Text style={{ marginTop: 16 }}>正在通过飞书登录...</Text>
    </div>
  );
};

export default FeishuCallback;