import React from 'react';
import { Breadcrumb, Flex, Space, Typography } from 'antd';

const { Title } = Typography;

export interface PageScaffoldProps {
  title: string;
  breadcrumbItems?: { title: string; href?: string }[];
  extra?: React.ReactNode;
  filters?: React.ReactNode;
  children: React.ReactNode;
}

const PageScaffold: React.FC<PageScaffoldProps> = ({ 
  title, 
  breadcrumbItems, 
  extra, 
  filters,
  children 
}) => (
  <Space direction="vertical" size={16} style={{ width: '100%' }}>
    {breadcrumbItems && breadcrumbItems.length > 0 && (
      <Breadcrumb 
        items={breadcrumbItems} 
        style={{ margin: '16px 0' }}
      />
    )}
    <Flex justify="space-between" align="center">
      <Title level={4} style={{ margin: 0 }}>
        {title}
      </Title>
      {extra && <Space>{extra}</Space>}
    </Flex>
    {filters && <div style={{ marginBottom: 16 }}>{filters}</div>}
    {children}
  </Space>
);

export default PageScaffold;
