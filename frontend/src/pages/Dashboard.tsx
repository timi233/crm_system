import React from 'react';
import { Layout, Menu, theme, Button, Badge, Space, Dropdown } from 'antd';
import { DashboardOutlined, TeamOutlined, ShopOutlined, FundProjectionScreenOutlined, PhoneOutlined, BookOutlined, UserOutlined, LogoutOutlined, BulbOutlined, HistoryOutlined, HomeOutlined, WarningOutlined, TrophyOutlined, ToolOutlined, QuestionCircleOutlined, FileTextOutlined, BellOutlined, CheckSquareOutlined } from '@ant-design/icons';
import { useNavigate, Outlet, useLocation } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../store/store';
import { logout } from '../store/slices/authSlice';
import { getRoleLabel } from '../utils/roles';
import { useUnreadCount } from '../hooks/useNotifications';

const { Header, Sider, Content } = Layout;

const Dashboard: React.FC = () => {
  const { user, capabilities } = useSelector((state: RootState) => state.auth);
  const [collapsed, setCollapsed] = React.useState(false);
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const { data: unreadCount } = useUnreadCount();
  const {
    token: { colorBgContainer },
  } = theme.useToken();

  const getMenuItems = () => {
    const businessItems = [
      { key: '/dashboard', label: '我的工作台', icon: <HomeOutlined /> },
      { key: '/todos', label: '待办中心', icon: <CheckSquareOutlined /> },
      { key: '/customers', label: '终端客户', icon: <TeamOutlined /> },
      { key: '/leads', label: '线索管理', icon: <BulbOutlined /> },
      { key: '/opportunities', label: '商机管理', icon: <FundProjectionScreenOutlined /> },
      { key: '/projects', label: '项目管理', icon: <DashboardOutlined /> },
      { key: '/business-follow-ups', label: '业务跟进', icon: <PhoneOutlined /> },
      { key: '/work-orders', label: '工单管理', icon: <ToolOutlined /> },
      { key: '/knowledge', label: '知识库', icon: <QuestionCircleOutlined /> },
    ];

    if (capabilities['work_report:read'] && user?.role !== 'finance') {
      businessItems.push({ key: '/work-reports', label: '日报/周报', icon: <FileTextOutlined /> });
    }

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
    if (capabilities['handover:read']) {
      managementItems.push({ key: '/handovers', label: '离职交接', icon: <UserOutlined /> });
    }
    managementItems.push({
      key: '/notifications',
      label: (
        <span>
          通知中心
          <Badge count={unreadCount?.count || 0} showZero={false} size="small" style={{ marginLeft: 8 }} />
        </span>
      ),
      icon: <BellOutlined />,
    });
    if (capabilities['operation_log:read']) {
      managementItems.push({ key: '/operation-logs', label: '操作日志', icon: <HistoryOutlined /> });
    }

    return [
      { type: 'group' as const, label: collapsed ? '业务' : '业务管理', children: businessItems },
      ...(channelItems.length > 0 ? [{ type: 'group' as const, label: collapsed ? '渠道' : '渠道管理', children: channelItems }] : []),
      ...(managementItems.length > 0 ? [{ type: 'group' as const, label: collapsed ? '系统' : '系统管理', children: managementItems }] : []),
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
      <Sider
        width={250}
        collapsible
        collapsed={collapsed}
        onCollapse={(value) => setCollapsed(value)}
        className="app-sider hide-scrollbar"
        collapsedWidth={80}
        style={{
          background: 'var(--sidebar-bg)',
          borderRight: '1px solid rgba(125, 211, 252, 0.14)',
          position: 'fixed',
          height: '100vh',
          left: 0,
          top: 0,
          bottom: 0,
          zIndex: 100,
          overflowY: 'auto',
          transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
        }}
      >
        <div style={{
          height: '64px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'flex-start',
          padding: collapsed ? '0' : '0 22px',
          borderBottom: '1px solid rgba(125, 211, 252, 0.14)',
          marginBottom: '8px',
          overflow: 'hidden'
        }}>
          <div style={{
            background: 'var(--primary-gradient)',
            width: '32px',
            minWidth: '32px',
            height: '32px',
            borderRadius: '8px',
            marginRight: collapsed ? '0' : '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontWeight: 'bold',
            fontSize: '18px',
            boxShadow: '0 0 22px rgba(34, 211, 238, 0.28)',
            transition: 'all 0.2s'
          }}>
            P
          </div>
          {!collapsed && (
            <span style={{
              fontSize: '18px',
              fontWeight: 700,
              color: '#e5f2ff',
              letterSpacing: '0',
              whiteSpace: 'nowrap',
              opacity: 1,
              transition: 'opacity 0.2s'
            }}>
              普悦销管系统
            </span>
          )}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          className="app-sider-menu"
          style={{
            height: 'calc(100% - 72px)',
            borderRight: 0,
            padding: collapsed ? '0 8px' : '0 12px',
            background: 'transparent',
          }}
          items={getMenuItems()}
          onClick={({ key }) => handleMenuClick(key)}
        />
      </Sider>
      <Layout style={{ marginLeft: collapsed ? 80 : 250, transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)' }}>
        <Header style={{
          background: 'rgba(255, 255, 255, 0.94)',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid #dbeafe',
          boxShadow: '0 10px 30px rgba(15, 23, 42, 0.04)',
          position: 'sticky',
          top: 0,
          zIndex: 99,
          height: '64px'
        }}>
          <div />
          <Space size={24}>
            <Badge count={unreadCount?.count || 0} size="small">
              <Button
                type="text"
                icon={<BellOutlined style={{ fontSize: '18px', color: '#64748b' }} />}
                onClick={() => navigate('/notifications')}
              />
            </Badge>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ textAlign: 'right', lineHeight: 1.2 }}>
                <div style={{ fontSize: '14px', fontWeight: 600, color: '#1e293b' }}>{user?.name}</div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>{getRoleLabel(user?.role)}</div>
              </div>
              <Dropdown
                menu={{
                  items: [
                    { key: 'logout', label: '登出系统', icon: <LogoutOutlined />, danger: true, onClick: handleLogout },
                  ],
                }}
                placement="bottomRight"
              >
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  background: '#f1f5f9',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  border: '1px solid #e2e8f0'
                }}>
                  <UserOutlined style={{ fontSize: '18px', color: '#64748b' }} />
                </div>
              </Dropdown>
            </div>
          </Space>
        </Header>
        <Content style={{ padding: '24px', minHeight: 280, background: 'var(--bg-main)' }}>
          <div className="fade-in">
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};

export default Dashboard;
