import React, { ReactNode } from 'react';
import { Drawer, Space, Typography } from 'antd';

const { Title } = Typography;

export interface SidebarDrawerProps {
  title: string;
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  width?: number;
  footer?: ReactNode;
}

const SidebarDrawer: React.FC<SidebarDrawerProps> = ({ 
  title, 
  open, 
  onClose, 
  children,
  width = 480,
  footer,
}) => (
  <Drawer
    title={title}
    open={open}
    onClose={onClose}
    width={width}
    maskClosable={false}
    destroyOnClose
    footer={footer}
    styles={{
      body: { padding: '16px' },
    }}
  >
    {children}
  </Drawer>
);

export default SidebarDrawer;
