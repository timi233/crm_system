import React from 'react';
import { Layout, Menu, theme, Button } from 'antd';
import { DashboardOutlined, TeamOutlined, ShopOutlined, FundProjectionScreenOutlined, FileDoneOutlined, PhoneOutlined, AppstoreOutlined, UserOutlined, LogoutOutlined } from '@ant-design/icons';
import { useNavigate, Outlet } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../store/store';
import { logout } from '../store/slices/authSlice';

const { Header, Sider, Content } = Layout;

const Dashboard: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const {
    token: { colorBgContainer },
  } = theme.useToken();

  // Generate menu items based on user role
  const getMenuItems = () => {
    const baseItems = [
      { key: '/customers', label: '终端客户', icon: <TeamOutlined /> },
      { key: '/channels', label: '渠道档案', icon: <ShopOutlined /> },
      { key: '/opportunities', label: '商机管理', icon: <FundProjectionScreenOutlined /> },
      { key: '/projects', label: '项目管理', icon: <DashboardOutlined /> },
      { key: '/contracts', label: '合同管理', icon: <FileDoneOutlined /> },
      { key: '/follow-ups', label: '跟进记录', icon: <PhoneOutlined /> },
      { key: '/products', label: '产品字典', icon: <AppstoreOutlined /> },
    ];

    // Add admin-only items
    if (user?.role === 'admin') {
      baseItems.push({ key: '/users', label: '用户管理', icon: <UserOutlined /> });
    }

    return baseItems;
  };

  const handleMenuClick = (key: string) => {
    navigate(key);
  };

  const handleLogout = () => {
    dispatch(logout());
    navigate('/login');
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ color: 'white', fontSize: '20px', fontWeight: 'bold' }}>
          业财一体CRM系统
        </div>
        <div style={{ color: 'white' }}>
          欢迎, {user?.name} ({user?.role})
          <Button type="link" onClick={handleLogout} style={{ color: 'white', marginLeft: 16 }}>
            <LogoutOutlined /> 登出
          </Button>
        </div>
      </Header>
      <Layout>
        <Sider width={200} style={{ background: colorBgContainer }}>
          <Menu
            mode="inline"
            defaultSelectedKeys={['/']}
            style={{ height: '100%', borderRight: 0 }}
            items={getMenuItems()}
            onClick={({ key }) => handleMenuClick(key)}
          />
        </Sider>
        <Layout style={{ padding: '24px' }}>
          <Content style={{ background: colorBgContainer, padding: 24, minHeight: 280 }}>
            <Outlet />
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
};

export default Dashboard;