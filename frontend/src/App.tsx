import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider, App as AntApp } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import store from './store/store';

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

import Login from './pages/auth/Login';
import Logout from './pages/auth/Logout';
import FeishuCallback from './pages/auth/FeishuCallback';
import Dashboard from './pages/Dashboard';
import MyDashboard from './pages/MyDashboard';
import CustomerListPage from './pages/CustomerListPage';
import ProjectListPage from './pages/ProjectListPage';
import CustomerFullViewPage from './pages/CustomerFullViewPage';
import ChannelFullViewPage from './pages/ChannelFullViewPage';
import ChannelFollowUpPage from './pages/ChannelFollowUpPage';
import ChannelPerformancePage from './pages/ChannelPerformancePage';
import ChannelTrainingPage from './pages/ChannelTrainingPage';
import LeadFullViewPage from './pages/LeadFullViewPage';
import OpportunityFullViewPage from './pages/OpportunityFullViewPage';
import ProjectFullViewPage from './pages/ProjectFullViewPage';
import ContractFullViewPage from './pages/ContractFullViewPage';
import SalesFunnelReport from './pages/SalesFunnelReport';
import PerformanceReport from './pages/PerformanceReport';
import PaymentProgressReport from './pages/PaymentProgressReport';
import CustomerList from './components/lists/CustomerList';
import CustomerForm from './components/forms/CustomerForm';
import ChannelList from './components/lists/ChannelList';
import LeadList from './components/lists/LeadList';
import LeadForm from './components/forms/LeadForm';
import OpportunityList from './components/lists/OpportunityList';
import OpportunityForm from './components/forms/OpportunityForm';
import ProjectList from './components/lists/ProjectList';
import ProjectForm from './components/forms/ProjectForm';
import ContractList from './components/lists/ContractList';
import ContractForm from './components/forms/ContractForm';
import FollowUpList from './components/lists/FollowUpList';
import FollowUpForm from './components/forms/FollowUpForm';
import ProductList from './components/lists/ProductList';
import UserList from './components/lists/UserList';
import DictItemList from './components/lists/DictItemList';
import OperationLogList from './components/lists/OperationLogList';
import AlertRuleList from './components/lists/AlertRuleList';
import SalesTargetList from './components/lists/SalesTargetList';
import WorkOrderList from './components/lists/WorkOrderList';
import KnowledgeList from './components/lists/KnowledgeList';
import WorkOrderDetailPage from './pages/WorkOrderDetailPage';
import ProtectedRoute from './components/auth/ProtectedRoute';
import AuthBootstrap from './components/auth/AuthBootstrap';
import AppFeedbackBridge from './components/common/AppFeedbackBridge';

function App() {
  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <ConfigProvider
          locale={zhCN}
          theme={{
            token: {
              colorPrimary: '#0052cc',
              colorSuccess: '#52c41a',
              colorWarning: '#faad14',
              colorError: '#ff4d4f',
              borderRadius: 6,
              fontFamily: "'PingFang SC', 'Microsoft YaHei', -apple-system, sans-serif",
            },
          }}
        >
          <AntApp>
            <AppFeedbackBridge />
            <AuthBootstrap />
            <Router>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/logout" element={<Logout />} />
              <Route path="/auth/feishu/callback" element={<FeishuCallback />} />
              <Route path="/" element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }>
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="dashboard" element={<MyDashboard />} />
                <Route path="customers" element={<CustomerListPage />} />
                <Route path="customers/:id/full" element={<CustomerFullViewPage />} />
                <Route path="channels" element={<ChannelList />} />
                <Route path="channels/new" element={<ChannelList />} />
                <Route path="channels/:id/full" element={<ChannelFullViewPage />} />
                <Route path="leads" element={<LeadList />} />
                <Route path="leads/new" element={<LeadForm />} />
                <Route path="leads/:id/full" element={<LeadFullViewPage />} />
                <Route path="opportunities" element={<OpportunityList />} />
                <Route path="opportunities/new" element={<OpportunityForm />} />
                <Route path="opportunities/:id/full" element={<OpportunityFullViewPage />} />
                <Route path="projects" element={<ProjectListPage />} />
                <Route path="projects/:id/full" element={<ProjectFullViewPage />} />
                <Route path="reports/sales-funnel" element={<SalesFunnelReport />} />
                <Route path="reports/performance" element={<PerformanceReport />} />
                <Route path="reports/payment-progress" element={<PaymentProgressReport />} />
                <Route path="follow-ups" element={<Navigate to="/business-follow-ups" replace />} />
                <Route path="business-follow-ups" element={<FollowUpList mode="business" />} />
                <Route path="channel-follow-ups" element={<ChannelFollowUpPage />} />
                <Route path="channel-performance" element={<ChannelPerformancePage />} />
                <Route path="channel-training" element={<ChannelTrainingPage />} />
                <Route path="follow-ups/new" element={<FollowUpForm />} />
                <Route path="products" element={<ProductList />} />
                <Route path="users" element={<UserList />} />
                <Route path="dict-items" element={<DictItemList />} />
                <Route path="operation-logs" element={<OperationLogList />} />
                <Route path="alert-rules" element={<AlertRuleList />} />
                <Route path="sales-targets" element={<SalesTargetList />} />
                <Route path="work-orders" element={<WorkOrderList />} />
                <Route path="work-orders/:id" element={<WorkOrderDetailPage />} />
                <Route path="knowledge" element={<KnowledgeList />} />
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
