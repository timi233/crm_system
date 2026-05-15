import React, { ReactNode } from 'react';
import { Modal, Spin } from 'antd';

export interface PageModalProps {
  title: string;
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  width?: number;
  loading?: boolean;
  footer?: ReactNode;
}

const PageModal: React.FC<PageModalProps> = ({
  title,
  open,
  onClose,
  children,
  width = 640,
  loading = false,
  footer,
}) => (
  <Modal
    title={title}
    open={open}
    onCancel={onClose}
    width={width}
    maskClosable={false}
    destroyOnClose
    footer={footer}
    centered
  >
    <div className="fade-in">
      {loading ? (
        <div style={{ textAlign: 'center', padding: '80px 0' }}>
          <Spin tip="正在努力加载中..." size="large" />
        </div>
      ) : (
        children
      )}
    </div>
  </Modal>
);

export default PageModal;
