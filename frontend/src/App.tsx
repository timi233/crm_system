import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider, App as AntApp, Spin } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import store from './store/store';

import Login from './pages/auth/Login';
import Logout from './pages/auth/Logout';
import FeishuCallback from './pages/auth/FeishuCallback';
import Dashboard from './pages/Dashboard';
import MyDashboard from './pages/MyDashboard';
import CustomerListPage from './pages/CustomerListPage';
import ProjectListPage from './pages/ProjectListPage';

const CustomerFullViewPage = React.lazy(() => import('./pages/CustomerFullViewPage'));
const ChannelFullViewPage = React.lazy(() => import('./pages/ChannelFullViewPage'));
const ChannelFollowUpPage = React.lazy(() => import('./pages/ChannelFollowUpPage'));
const ChannelPerformancePage = React.lazy(() => import('./pages/ChannelPerformancePage'));
const ChannelTrainingPage = React.lazy(() => import('./pages/ChannelTrainingPage'));
const LeadFullViewPage = React.lazy(() => import('./pages/LeadFullViewPage'));
const OpportunityFullViewPage = React.lazy(() => import('./pages/OpportunityFullViewPage'));
const ProjectFullViewPage = React.lazy(() => import('./pages/ProjectFullViewPage'));
const ContractFullViewPage = React.lazy(() => import('./pages/ContractFullViewPage'));
const SalesFunnelReport = React.lazy(() => import('./pages/SalesFunnelReport'));
const PerformanceReport = React.lazy(() => import('./pages/PerformanceReport'));
const PaymentProgressReport = React.lazy(() => import('./pages/PaymentProgressReport'));
const WorkOrderDetailPage = React.lazy(() => import('./pages/WorkOrderDetailPage'));
const WorkReportPage = React.lazy(() => import('./pages/WorkReportPage'));
const WorkReportDetailPage = React.lazy(() => import('./pages/WorkReportDetailPage'));
const HandoverListPage = React.lazy(() => import('./pages/HandoverListPage'));
const HandoverDetailPage = React.lazy(() => import('./pages/HandoverDetailPage'));
const NotificationCenterPage = React.lazy(() => import('./pages/NotificationCenterPage'));
const TodoCenterPage = React.lazy(() => import('./pages/TodoCenterPage'));

// Lazy load list and form components
const CustomerList = React.lazy(() => import('./components/lists/CustomerList'));
const CustomerForm = React.lazy(() => import('./components/forms/CustomerForm'));
const ChannelList = React.lazy(() => import('./components/lists/ChannelList'));
const LeadList = React.lazy(() => import('./components/lists/LeadList'));
const LeadForm = React.lazy(() => import('./components/forms/LeadForm'));
const OpportunityList = React.lazy(() => import('./components/lists/OpportunityList'));
const OpportunityForm = React.lazy(() => import('./components/forms/OpportunityForm'));
const ProjectList = React.lazy(() => import('./components/lists/ProjectList'));
const ProjectForm = React.lazy(() => import('./components/forms/ProjectForm'));
const ContractList = React.lazy(() => import('./components/lists/ContractList'));
const ContractForm = React.lazy(() => import('./components/forms/ContractForm'));
const FollowUpList = React.lazy(() => import('./components/lists/FollowUpList'));
const FollowUpForm = React.lazy(() => import('./components/forms/FollowUpForm'));
const ProductList = React.lazy(() => import('./components/lists/ProductList'));
const UserList = React.lazy(() => import('./components/lists/UserList'));
const DictItemList = React.lazy(() => import('./components/lists/DictItemList'));
const OperationLogList = React.lazy(() => import('./components/lists/OperationLogList'));
const AlertRuleList = React.lazy(() => import('./components/lists/AlertRuleList'));
const SalesTargetTree = React.lazy(() => import('./components/lists/SalesTargetTree'));
const WorkOrderList = React.lazy(() => import('./components/lists/WorkOrderList'));
const KnowledgeList = React.lazy(() => import('./components/lists/KnowledgeList'));
const ProtectedRoute = React.lazy(() => import('./components/auth/ProtectedRoute'));
const AuthBootstrap = React.lazy(() => import('./components/auth/AuthBootstrap'));
const AppFeedbackBridge = React.lazy(() => import('./components/common/AppFeedbackBridge'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      gcTime: 1000 * 60 * 10,
      refetchOnWindowFocus: false,
      retry: 1,
    },
    mutations: {
      retry: 1,
    },
  },
});

const RouteFallback = () => (
  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
    <Spin size="large" tip="加载中...">
      <div style={{ width: 1, height: 1 }} />
    </Spin>
  </div>
);

const protectedElement = (
  children: React.ReactNode,
  requiredCapability?: string | string[]
) => (
  <Suspense fallback={<RouteFallback />}>
    <ProtectedRoute requiredCapability={requiredCapability}>
      {children}
    </ProtectedRoute>
  </Suspense>
);

function App() {
  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <ConfigProvider
          locale={zhCN}
          theme={{
            token: {
              colorPrimary: '#0052cc',
              colorSuccess: '#10B981',
              colorWarning: '#F59E0B',
              colorError: '#EF4444',
              colorInfo: '#0052cc',
              borderRadius: 8,
              fontFamily: "'Inter', 'SF Pro Text', 'PingFang SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
              colorBgLayout: '#f8fafc',
            },
            components: {
              Button: {
                fontWeight: 600,
                controlHeight: 38,
                borderRadius: 6,
              },
              Card: {
                headerBg: 'transparent',
                borderRadiusLG: 12,
                boxShadowTertiary: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
              },
              Table: {
                headerBg: '#f1f5f9',
                headerColor: '#475569',
                headerBorderRadius: 8,
                rowHoverBg: '#f8fafc',
              },
              Menu: {
                itemBorderRadius: 8,
                itemSelectedBg: '#eef2ff',
                itemSelectedColor: '#0052cc',
              },
              Layout: {
                headerBg: '#ffffff',
                headerPadding: '0 24px',
                siderBg: '#ffffff',
              },
            },
          }}
        >
          <AntApp>
            <Suspense fallback={<RouteFallback />}>
              <AppFeedbackBridge />
              <AuthBootstrap />
            </Suspense>
            <Router>
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/logout" element={<Logout />} />
                <Route path="/auth/feishu/callback" element={<FeishuCallback />} />
                <Route path="/" element={protectedElement(<Dashboard />)}>
                  <Route index element={<Navigate to="/dashboard" replace />} />
                  <Route path="dashboard" element={protectedElement(<MyDashboard />, 'dashboard:read')} />
                  <Route path="customers" element={protectedElement(<CustomerListPage />, 'customer:read')} />
                  <Route path="channels" element={protectedElement(<ChannelList />, 'channel:read')} />
                  <Route path="leads" element={protectedElement(<LeadList />, 'lead:read')} />
                  <Route path="opportunities" element={protectedElement(<OpportunityList />, 'opportunity:read')} />
                  <Route path="projects" element={protectedElement(<ProjectListPage />, 'project:read')} />
                  <Route path="contracts" element={protectedElement(<ContractList />, 'contract:read')} />
                  <Route path="work-orders" element={protectedElement(<WorkOrderList />, 'work_order:read')} />

                  <Route path="customers/:id/full" element={protectedElement(<CustomerFullViewPage />, 'customer:read')} />
                  <Route path="channels/new" element={protectedElement(<ChannelList />, 'channel:create')} />
                  <Route path="channels/:id/full" element={protectedElement(<ChannelFullViewPage />, 'channel:read')} />
                  <Route path="leads/new" element={protectedElement(<LeadForm />, 'lead:create')} />
                  <Route path="leads/:id/full" element={protectedElement(<LeadFullViewPage />, 'lead:read')} />
                  <Route path="opportunities/new" element={protectedElement(<OpportunityForm />, 'opportunity:create')} />
                  <Route path="opportunities/:id/full" element={protectedElement(<OpportunityFullViewPage />, 'opportunity:read')} />
                  <Route path="projects/:id/full" element={protectedElement(<ProjectFullViewPage />, 'project:read')} />
                  <Route path="contracts/new" element={protectedElement(<ContractForm />, 'contract:create')} />
                  <Route path="contracts/:id/full" element={protectedElement(<ContractFullViewPage />, 'contract:read')} />
                  <Route path="reports/sales-funnel" element={protectedElement(<SalesFunnelReport />, 'report:read')} />
                  <Route path="reports/performance" element={protectedElement(<PerformanceReport />, 'report:read')} />
                  <Route path="reports/payment-progress" element={protectedElement(<PaymentProgressReport />, 'report:read')} />
                  <Route path="follow-ups" element={<Navigate to="/business-follow-ups" replace />} />
                  <Route path="business-follow-ups" element={protectedElement(<FollowUpList mode="business" />, 'follow_up:read')} />
                  <Route path="channel-follow-ups" element={protectedElement(<FollowUpList mode="channel" />, 'channel:read')} />
                  <Route path="channel-performance" element={protectedElement(<ChannelPerformancePage />, 'channel_performance:read')} />
                  <Route path="channel-training" element={protectedElement(<ChannelTrainingPage />, 'channel_training:read')} />
                  <Route path="follow-ups/new" element={protectedElement(<FollowUpForm />, 'follow_up:create')} />
                  <Route path="products" element={protectedElement(<ProductList />, 'product:read')} />
                  <Route path="users" element={protectedElement(<UserList />, 'user:read')} />
                  <Route path="dict-items" element={protectedElement(<DictItemList />, 'dict_item:read')} />
                  <Route path="operation-logs" element={protectedElement(<OperationLogList />, 'operation_log:read')} />
                  <Route path="alert-rules" element={protectedElement(<AlertRuleList />, 'alert_rule:manage')} />
                  <Route path="sales-targets" element={protectedElement(<SalesTargetTree />, 'sales_target:read')} />
                  <Route path="knowledge" element={protectedElement(<KnowledgeList />, 'knowledge:read')} />
                  <Route path="work-orders/:id" element={protectedElement(<WorkOrderDetailPage />, 'work_order:read')} />
                  <Route path="work-reports" element={protectedElement(<WorkReportPage />, 'work_report:read')} />
                  <Route path="work-reports/:id" element={protectedElement(<WorkReportDetailPage />, 'work_report:read')} />
                  <Route path="handovers" element={protectedElement(<HandoverListPage />, 'handover:read')} />
                  <Route path="handovers/:id" element={protectedElement(<HandoverDetailPage />, 'handover:read')} />
                  <Route path="notifications" element={protectedElement(<NotificationCenterPage />)} />
                  <Route path="todos" element={protectedElement(<TodoCenterPage />)} />
                </Route>
              </Routes>
            </Router>
          </AntApp>
        </ConfigProvider>
      </QueryClientProvider>
    </Provider>
  );
}

export default App;
