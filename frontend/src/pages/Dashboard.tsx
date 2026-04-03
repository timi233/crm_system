import React from 'react';
import { Layout, Menu, theme, Button } from 'antd';
import { DashboardOutlined, TeamOutlined, ShopOutlined, FundProjectionScreenOutlined, FileDoneOutlined, PhoneOutlined, BookOutlined, UserOutlined, LogoutOutlined, BulbOutlined, HistoryOutlined, BarChartOutlined, FunnelPlotOutlined, DollarOutlined, LineChartOutlined, HomeOutlined, WarningOutlined, TrophyOutlined } from '@ant-design/icons';
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

  const getMenuItems = () => {
    const baseItems = [
      { key: '/dashboard', label: '我的工作台', icon: <HomeOutlined /> },
      { key: '/customers', label: '终端客户', icon: <TeamOutlined /> },
      { key: '/channels', label: '渠道档案', icon: <ShopOutlined /> },
      { key: '/leads', label: '线索管理', icon: <BulbOutlined /> },
      { key: '/opportunities', label: '商机管理', icon: <FundProjectionScreenOutlined /> },
      { key: '/projects', label: '项目管理', icon: <DashboardOutlined /> },
      { key: '/contracts', label: '合同管理', icon: <FileDoneOutlined /> },
      { key: '/follow-ups', label: '跟进记录', icon: <PhoneOutlined /> },
      {
        key: 'reports',
        label: '报表统计',
        icon: <BarChartOutlined />,
        children: [
          { key: '/reports/sales-funnel', label: '销售漏斗', icon: <FunnelPlotOutlined /> },
          { key: '/reports/performance', label: '业绩统计', icon: <DollarOutlined /> },
          { key: '/reports/payment-progress', label: '回款进度', icon: <LineChartOutlined /> },
        ],
      },
    ];

    if (user?.role === 'admin') {
      baseItems.push({ key: '/dict-items', label: '数据字典', icon: <BookOutlined /> });
      baseItems.push({ key: '/alert-rules', label: '预警中心', icon: <WarningOutlined /> });
      baseItems.push({ key: '/sales-targets', label: '目标管理', icon: <TrophyOutlined /> });
      baseItems.push({ key: '/users', label: '用户管理', icon: <UserOutlined /> });
      baseItems.push({ key: '/operation-logs', label: '操作日志', icon: <HistoryOutlined /> });
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
          普悦销管系统
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