import React, { useEffect } from 'react';
import { Form, Input, Select, DatePicker, Button, App, Row, Col } from 'antd';
import { useCreateFollowUp, useUpdateFollowUp, FollowUp } from '../../hooks/useFollowUps';
import { useDictItems } from '../../hooks/useDictItems';
import PageModal from '../common/PageModal';

const { Option } = Select;
const { TextArea } = Input;

interface FollowUpModalProps {
  visible: boolean;
  onClose: () => void;
  followUp?: FollowUp | null;
  terminal_customer_id?: number;
  channel_id?: number;
  lead_id?: number;
  opportunity_id?: number;
  project_id?: number;
}

const FollowUpModal: React.FC<FollowUpModalProps> = ({
  visible,
  onClose,
  followUp,
  terminal_customer_id,
  channel_id,
  lead_id,
  opportunity_id,
  project_id,
}) => {
  const [form] = Form.useForm();
  const { message } = App.useApp();

  const { data: methodItems = [] } = useDictItems('跟进方式');
  const { data: conclusionItems = [] } = useDictItems('跟进结论');

  const methodOptions = methodItems.map(item => ({ value: item.name, label: item.name }));
  const conclusionOptions = conclusionItems.map(item => ({ value: item.name, label: item.name }));

  const createMutation = useCreateFollowUp();
  const updateMutation = useUpdateFollowUp();

  useEffect(() => {
    if (visible && followUp) {
      form.setFieldsValue(followUp);
    } else if (visible) {
      form.resetFields();
      form.setFieldsValue({
        follow_up_date: new Date().toISOString().split('T')[0],
        follow_up_method: '电话',
        terminal_customer_id,
        channel_id,
        lead_id,
        opportunity_id,
        project_id,
      });
    }
  }, [visible, followUp, form, terminal_customer_id, channel_id, lead_id, opportunity_id, project_id]);

  const onFinish = async (values: any) => {
    try {
      if (followUp) {
        await updateMutation.mutateAsync({ id: followUp.id, data: values });
        message.success('跟进记录已更新');
      } else {
        await createMutation.mutateAsync(values);
        message.success('跟进记录已保存');
      }
      onClose();
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  return (
    <PageModal
      title={followUp ? '编辑跟进记录' : '记录新业务进展'}
      width={640}
      open={visible}
      onClose={onClose}
      footer={[
        <Button key="cancel" onClick={onClose}>
          取消
        </Button>,
        <Button
          key="submit"
          type="primary"
          className="btn--gradient"
          onClick={() => form.submit()}
          loading={createMutation.isPending || updateMutation.isPending}
        >
          保存并同步
        </Button>
      ]}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="跟进日期"
              name="follow_up_date"
              rules={[{ required: true, message: '请选择日期' }]}
            >
              <Input type="date" style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              label="跟进方式"
              name="follow_up_method"
              rules={[{ required: true, message: '请选择方式' }]}
            >
              <Select placeholder="选择沟通方式">
                {methodOptions.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Form.Item
          label="跟进内容摘要"
          name="follow_up_content"
          rules={[{ required: true, message: '请输入跟进内容' }]}
        >
          <TextArea rows={4} placeholder="详细记录本次沟通的核心内容、客户反馈及达成的一致意见..." />
        </Form.Item>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="跟进定性结论" name="follow_up_conclusion">
              <Select placeholder="选择本次沟通的最终结论" allowClear>
                {conclusionOptions.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="下一步行动计划" name="next_action">
              <Input placeholder="例如：下周三前提供技术方案" />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item name="terminal_customer_id" hidden><Input /></Form.Item>
        <Form.Item name="channel_id" hidden><Input /></Form.Item>
        <Form.Item name="lead_id" hidden><Input /></Form.Item>
        <Form.Item name="opportunity_id" hidden><Input /></Form.Item>
        <Form.Item name="project_id" hidden><Input /></Form.Item>
      </Form>
    </PageModal>
  );
};

export default FollowUpModal;
