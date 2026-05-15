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
      <Sider
        width={250}
        collapsible
        className="hide-scrollbar"
        collapsedWidth={80}
        style={{
          background: '#ffffff',
          borderRight: '1px solid #f1f5f9',
          position: 'fixed',
          height: '100vh',
          left: 0,
          top: 0,
          bottom: 0,
          zIndex: 100,
          overflowY: 'auto',
        }}
      >
        <div style={{
          height: '64px',
          display: 'flex',
          alignItems: 'center',
          padding: '0 24px',
          borderBottom: '1px solid #f1f5f9',
          marginBottom: '8px'
        }}>
          <div style={{
            background: 'var(--primary-gradient)',
            width: '32px',
            height: '32px',
            borderRadius: '8px',
            marginRight: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontWeight: 'bold',
            fontSize: '18px'
          }}>
            P
          </div>
          {!false && (
            <span style={{
              fontSize: '18px',
              fontWeight: 700,
              color: '#0f172a',
              letterSpacing: '-0.5px'
            }}>
              普悦销管系统
            </span>
          )}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          style={{ height: 'calc(100% - 72px)', borderRight: 0, padding: '0 12px' }}
          items={getMenuItems()}
          onClick={({ key }) => handleMenuClick(key)}
        />
      </Sider>
      <Layout style={{ marginLeft: 250, transition: 'all 0.2s' }}>
        <Header style={{
          background: '#ffffff',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid #f1f5f9',
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
        <Content style={{ padding: '24px', minHeight: 280, background: '#f8fafc' }}>
          <div className="fade-in">
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};

export default Dashboard;
