import React from 'react';
import { Modal, Button, Descriptions, Spin } from 'antd';
import { UserOutlined, PhoneOutlined } from '@ant-design/icons';

interface DispatchInfo {
  customer_name?: string;
  contact?: string;
  phone?: string;
  entity_name?: string;
  entity_type?: string;
}

interface DispatchModalProps {
  visible: boolean;
  onClose: () => void;
  onSubmit: () => Promise<void>;
  loading: boolean;
  dispatchInfo?: DispatchInfo;
}

const DispatchModal: React.FC<DispatchModalProps> = ({
  visible,
  onClose,
  onSubmit,
  loading,
  dispatchInfo,
}) => {
  const handleOk = async () => {
    try {
      await onSubmit();
      onClose();
    } catch (error) {
      console.error('Dispatch creation failed:', error);
    }
  };

  return (
    <Modal
      title="创建派工申请"
      open={visible}
      onCancel={onClose}
      footer={[
        <Button key="cancel" onClick={onClose}>
          取消
        </Button>,
        <Button key="submit" type="primary" loading={loading} onClick={handleOk}>
          确认创建派工
        </Button>,
      ]}
      width={600}
    >
      <div style={{ marginBottom: 16 }}>
        <p style={{ color: '#666', marginBottom: 16 }}>
          系统将自动使用预设的派工系统配置创建工单，无需手动填写参数。
        </p>
        
        {dispatchInfo ? (
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="客户名称">
              {dispatchInfo.customer_name || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="联系人">
              {dispatchInfo.contact ? (
                <span>
                  <UserOutlined style={{ marginRight: 4 }} />
                  {dispatchInfo.contact}
                </span>
              ) : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="联系电话">
              {dispatchInfo.phone ? (
                <span>
                  <PhoneOutlined style={{ marginRight: 4 }} />
                  {dispatchInfo.phone}
                </span>
              ) : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="关联{dispatchInfo.entity_type || '记录'}">
              {dispatchInfo.entity_name || '-'}
            </Descriptions.Item>
          </Descriptions>
        ) : (
          <Spin tip="正在加载派工信息..." />
        )}
      </div>

      <div style={{ 
        padding: 12, 
        background: '#f0f2f5', 
        borderRadius: 4,
        marginTop: 16 
      }}>
        <p style={{ margin: 0, fontSize: 12, color: '#999' }}>
          <strong>提示：</strong>派工申请将发送到IT派工系统，技术人员将尽快响应。
          您可以在"派工历史"中查看工单状态和进度。
        </p>
      </div>
    </Modal>
  );
};

export default DispatchModal;