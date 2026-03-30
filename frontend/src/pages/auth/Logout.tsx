import React, { useEffect } from 'react';
import { Typography, Spin } from 'antd';
import { useDispatch } from 'react-redux';
import { logout } from '../../store/slices/authSlice';
import { useNavigate } from 'react-router-dom';

const { Title } = Typography;

const Logout: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  useEffect(() => {
    // Perform logout actions
    dispatch(logout());
    // Redirect to login after a brief delay
    const timer = setTimeout(() => {
      navigate('/login');
    }, 1000);
    
    return () => clearTimeout(timer);
  }, [dispatch, navigate]);

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <div style={{ textAlign: 'center' }}>
        <Spin size="large" />
        <Title level={4} style={{ marginTop: 16 }}>
          正在登出...
        </Title>
      </div>
    </div>
  );
};

export default Logout;