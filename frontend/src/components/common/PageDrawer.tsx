import React, { ReactNode } from 'react';
import { Drawer, Spin } from 'antd';

export interface PageDrawerProps {
  title: string;
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  width?: number;
  loading?: boolean;
}

const PageDrawer: React.FC<PageDrawerProps> = ({ 
  title, 
  open, 
  onClose, 
  children,
  width = 520,
  loading = false,
}) => (
  <Drawer
    title={title}
    open={open}
    onClose={onClose}
    width={width}
    maskClosable={false}
    destroyOnClose
  >
    {loading ? (
      <div style={{ textAlign: 'center', padding: '40px 0' }}>
        <Spin tip="加载中..." />
      </div>
    ) : (
      children
    )}
  </Drawer>
);

export default PageDrawer;
