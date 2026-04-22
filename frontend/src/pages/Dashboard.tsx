import React from 'react';
import { Layout, Menu, theme, Button } from 'antd';
import { DashboardOutlined, TeamOutlined, ShopOutlined, FundProjectionScreenOutlined, PhoneOutlined, BookOutlined, UserOutlined, LogoutOutlined, BulbOutlined, HistoryOutlined, HomeOutlined, WarningOutlined, TrophyOutlined, ToolOutlined, QuestionCircleOutlined } from '@ant-design/icons';
import { useNavigate, Outlet, useLocation } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../store/store';
import { logout } from '../store/slices/authSlice';
import { getRoleLabel } from '../utils/roles';

const { Header, Sider, Content } = Layout;

const Dashboard: React.FC = () => {
  const { user, capabilities } = useSelector((state: RootState) => state.auth);
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const {
    token: { colorBgContainer },
  } = theme.useToken();

  const getMenuItems = () => {
    const businessItems = [
      { key: '/dashboard', label: '我的工作台', icon: <HomeOutlined /> },
      { key: '/customers', label: '终端客户', icon: <TeamOutlined /> },
      { key: '/leads', label: '线索管理', icon: <BulbOutlined /> },
      { key: '/opportunities', label: '商机管理', icon: <FundProjectionScreenOutlined /> },
      { key: '/projects', label: '项目管理', icon: <DashboardOutlined /> },
      { key: '/business-follow-ups', label: '业务跟进', icon: <PhoneOutlined /> },
      { key: '/work-orders', label: '工单管理', icon: <ToolOutlined /> },
      { key: '/knowledge', label: '知识库', icon: <QuestionCircleOutlined /> },
    ];

    const channelItems = [];
    if (capabilities['channel:read']) {
      channelItems.push({ key: '/channels', label: '渠道档案', icon: <ShopOutlined /> });
      channelItems.push({ key: '/channel-follow-ups', label: '渠道跟进', icon: <PhoneOutlined /> });
    }
    if (capabilities['channel_performance:read']) {
      channelItems.push({ key: '/channel-performance', label: '渠道业绩', icon: <FundProjectionScreenOutlined /> });
    }
    if (capabilities['channel_training:read']) {
      channelItems.push({ key: '/channel-training', label: '渠道培训', icon: <BookOutlined /> });
    }

    const managementItems = [];
    
    if (capabilities['dict_item:read']) {
      managementItems.push({ key: '/dict-items', label: '数据字典', icon: <BookOutlined /> });
    }
    if (capabilities['alert_rule:manage']) {
      managementItems.push({ key: '/alert-rules', label: '预警中心', icon: <WarningOutlined /> });
    }
    if (capabilities['sales_target:read']) {
      managementItems.push({ key: '/sales-targets', label: '目标管理', icon: <TrophyOutlined /> });
    }
    if (capabilities['user:read']) {
      managementItems.push({ key: '/users', label: '用户管理', icon: <UserOutlined /> });
    }
    if (capabilities['operation_log:read']) {
      managementItems.push({ key: '/operation-logs', label: '操作日志', icon: <HistoryOutlined /> });
    }

    return [
      { type: 'group' as const, label: '业务管理', children: businessItems },
      ...(channelItems.length > 0 ? [{ type: 'group' as const, label: '渠道管理', children: channelItems }] : []),
      ...(managementItems.length > 0 ? [{ type: 'group' as const, label: '系统管理', children: managementItems }] : []),
    ];
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
          欢迎, {user?.name} ({getRoleLabel(user?.role)})
          <Button type="link" onClick={handleLogout} style={{ color: 'white', marginLeft: 16 }}>
            <LogoutOutlined /> 登出
          </Button>
        </div>
      </Header>
      <Layout>
        <Sider width={200} collapsible collapsedWidth={80} style={{ background: colorBgContainer }}>
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
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
