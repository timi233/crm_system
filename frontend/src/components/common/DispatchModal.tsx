import React, { useState } from 'react';
import { Modal, Form, Input, Button, message } from 'antd';
import { DispatchApplicationRequest } from '../../types/dispatch';

interface DispatchModalProps {
  visible: boolean;
  onClose: () => void;
  onSubmit: (values: DispatchApplicationRequest) => Promise<void>;
  loading: boolean;
}

const DispatchModal: React.FC<DispatchModalProps> = ({
  visible,
  onClose,
  onSubmit,
  loading,
}) => {
  const [form] = Form.useForm<DispatchApplicationRequest>();

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      await onSubmit(values);
      form.resetFields();
      onClose();
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  return (
    <Modal
      title="创建派工申请"
      open={visible}
      onOk={handleOk}
      onCancel={onClose}
      footer={[
        <Button key="cancel" onClick={onClose}>
          取消
        </Button>,
        <Button key="submit" type="primary" loading={loading} onClick={handleOk}>
          创建派工
        </Button>,
      ]}
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="dispatch_api_url"
          label="派工系统API地址"
          rules={[{ required: true, message: '请输入派工系统API地址' }]}
          initialValue="http://localhost:3001"
        >
          <Input placeholder="例如: http://localhost:3001" />
        </Form.Item>
        <Form.Item
          name="dispatch_token"
          label="派工系统认证Token"
          rules={[{ required: true, message: '请输入派工系统认证Token' }]}
        >
          <Input.Password placeholder="JWT Token" />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default DispatchModal;