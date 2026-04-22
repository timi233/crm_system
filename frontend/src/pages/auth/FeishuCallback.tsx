import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { App, Button, Spin, Typography } from 'antd';
import { useDispatch } from 'react-redux';
import { loginStart, loginSuccess, loginFailure } from '../../store/slices/authSlice';
import authApi from '../../services/authService';

const { Text, Paragraph } = Typography;

const FeishuCallback: React.FC = () => {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [searchParams] = useSearchParams();
  const handledRef = useRef(false);
  const [errorText, setErrorText] = useState<string | null>(null);
  const code =
    searchParams.get('code') ||
    searchParams.get('tmp_auth_code') ||
    searchParams.get('auth_code');
  const state = searchParams.get('state');

  useEffect(() => {
    if (handledRef.current) {
      return;
    }

    if (code && state) {
      handledRef.current = true;
      void handleFeishuLogin(code, state);
    } else {
      setErrorText('缺少飞书登录回调参数，请重新发起登录。');
    }
  }, [code, state, navigate]);

  const handleFeishuLogin = async (code: string, state: string) => {
    try {
      dispatch(loginStart());
      const { user, token } = await authApi.feishuLogin(code, state);
      dispatch(loginSuccess({ user, token }));
      navigate('/', { replace: true });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '飞书登录失败';
      dispatch(loginFailure(errorMessage));
      setErrorText(errorMessage);
      message.error(errorMessage);
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', flexDirection: 'column' }}>
      {errorText ? (
        <>
          <Paragraph type="danger" style={{ marginBottom: 16 }}>
            {errorText}
          </Paragraph>
          <Button type="primary" onClick={() => navigate('/login', { replace: true })}>
            返回登录页
          </Button>
        </>
      ) : (
        <>
          <Spin size="large" />
          <Text style={{ marginTop: 16 }}>正在通过飞书登录...</Text>
        </>
      )}
    </div>
  );
};

export default FeishuCallback;
