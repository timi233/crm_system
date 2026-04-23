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
const SalesTargetList = React.lazy(() => import('./components/lists/SalesTargetList'));
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
              borderRadius: 6,
              fontFamily: "'SF Pro Text', 'PingFang SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
            },
            components: {
              Button: {
                fontWeight: 500,
              },
              Card: {
                headerBg: 'transparent',
              },
              Table: {
                headerBg: '#f8fafc',
                headerColor: '#1e293b',
                rowHoverBg: '#f1f5f9',
              },
            },
          }}
        >
          <AntApp>
            <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
              <AppFeedbackBridge />
              <AuthBootstrap />
            </Suspense>
            <Router>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/logout" element={<Logout />} />
              <Route path="/auth/feishu/callback" element={<FeishuCallback />} />
              <Route path="/" element={
                <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                </Suspense>
              }>
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="dashboard" element={<MyDashboard />} />
                <Route path="customers" element={<CustomerListPage />} />
                <Route path="channels" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <ChannelList />
                  </Suspense>
                } />
                <Route path="leads" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <LeadList />
                  </Suspense>
                } />
                <Route path="opportunities" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <OpportunityList />
                  </Suspense>
                } />
                <Route path="projects" element={<ProjectListPage />} />
                <Route path="contracts" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <ContractList />
                  </Suspense>
                } />
                <Route path="work-orders" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <WorkOrderList />
                  </Suspense>
                } />

                <Route path="customers/:id/full" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <CustomerFullViewPage />
                  </Suspense>
                } />
                <Route path="channels/new" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <ChannelList />
                  </Suspense>
                } />
                <Route path="channels/:id/full" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <ChannelFullViewPage />
                  </Suspense>
                } />
                <Route path="leads/new" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <LeadForm />
                  </Suspense>
                } />
                <Route path="leads/:id/full" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <LeadFullViewPage />
                  </Suspense>
                } />
                <Route path="opportunities/new" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <OpportunityForm />
                  </Suspense>
                } />
                <Route path="opportunities/:id/full" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <OpportunityFullViewPage />
                  </Suspense>
                } />
                <Route path="projects/:id/full" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <ProjectFullViewPage />
                  </Suspense>
                } />
                <Route path="contracts/new" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <ContractForm />
                  </Suspense>
                } />
                <Route path="contracts/:id/full" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <ContractFullViewPage />
                  </Suspense>
                } />
                <Route path="reports/sales-funnel" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <SalesFunnelReport />
                  </Suspense>
                } />
                <Route path="reports/performance" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <PerformanceReport />
                  </Suspense>
                } />
                <Route path="reports/payment-progress" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <PaymentProgressReport />
                  </Suspense>
                } />
                <Route path="follow-ups" element={<Navigate to="/business-follow-ups" replace />} />
                <Route path="business-follow-ups" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <FollowUpList mode="business" />
                  </Suspense>
                } />
                <Route path="channel-follow-ups" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <ChannelFollowUpPage />
                  </Suspense>
                } />
                <Route path="channel-performance" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <ChannelPerformancePage />
                  </Suspense>
                } />
                <Route path="channel-training" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <ChannelTrainingPage />
                  </Suspense>
                } />
                <Route path="follow-ups/new" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <FollowUpForm />
                  </Suspense>
                } />
                <Route path="products" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <ProductList />
                  </Suspense>
                } />
                <Route path="users" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <UserList />
                  </Suspense>
                } />
                <Route path="dict-items" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <DictItemList />
                  </Suspense>
                } />
                <Route path="operation-logs" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <OperationLogList />
                  </Suspense>
                } />
                <Route path="alert-rules" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <AlertRuleList />
                  </Suspense>
                } />
                <Route path="sales-targets" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <SalesTargetList />
                  </Suspense>
                } />
                <Route path="knowledge" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <KnowledgeList />
                  </Suspense>
                } />
                <Route path="work-orders/:id" element={
                  <Suspense fallback={<Spin size="large" tip="加载中..." style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />}>
                    <WorkOrderDetailPage />
                  </Suspense>
                } />
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
