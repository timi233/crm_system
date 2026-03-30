import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import store from './store/store';

import Login from './pages/auth/Login';
import Logout from './pages/auth/Logout';
import Dashboard from './pages/Dashboard';
import CustomerList from './components/lists/CustomerList';
import CustomerForm from './components/forms/CustomerForm';
import ChannelList from './components/lists/ChannelList';
import OpportunityList from './components/lists/OpportunityList';
import ProjectList from './components/lists/ProjectList';
import ContractList from './components/lists/ContractList';
import FollowUpList from './components/lists/FollowUpList';
import ProductList from './components/lists/ProductList';
import UserList from './components/lists/UserList';
import ProtectedRoute from './components/auth/ProtectedRoute';

const queryClient = new QueryClient();

function App() {
  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <ConfigProvider locale={zhCN}>
          <Router>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/logout" element={<Logout />} />
              <Route path="/" element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }>
                <Route index element={<Navigate to="/customers" replace />} />
                <Route path="customers" element={<CustomerList />} />
                <Route path="customers/new" element={<CustomerForm />} />
                <Route path="customers/:id/edit" element={<CustomerForm />} />
                <Route path="channels" element={<ChannelList />} />
                <Route path="opportunities" element={<OpportunityList />} />
                <Route path="projects" element={<ProjectList />} />
                <Route path="contracts" element={<ContractList />} />
                <Route path="follow-ups" element={<FollowUpList />} />
                <Route path="products" element={<ProductList />} />
                <Route path="users" element={<UserList />} />
              </Route>
            </Routes>
          </Router>
        </ConfigProvider>
      </QueryClientProvider>
    </Provider>
  );
}

export default App;
