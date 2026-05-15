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
  <div style={{ width: '100%' }}>
    <div style={{ marginBottom: '24px' }}>
      {breadcrumbItems && breadcrumbItems.length > 0 && (
        <Breadcrumb
          items={breadcrumbItems}
          style={{ marginBottom: '12px', fontSize: '13px' }}
        />
      )}
      <Flex justify="space-between" align="center">
        <Title level={2} style={{ margin: 0, fontWeight: 800, letterSpacing: '-0.75px', color: '#0f172a' }}>
          {title}
        </Title>
        {extra && <Space size={12}>{extra}</Space>}
      </Flex>
    </div>

    {filters && (
      <div style={{
        background: 'white',
        padding: '20px 24px',
        borderRadius: '12px',
        marginBottom: '24px',
        border: '1px solid #f1f5f9',
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)'
      }}>
        {filters}
      </div>
    )}

    <div style={{
      background: 'transparent',
      padding: '0',
      borderRadius: '0',
      border: 'none',
      boxShadow: 'none'
    }}>
      {children}
    </div>
  </div>
);

export default PageScaffold;
