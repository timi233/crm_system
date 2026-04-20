import React, { useEffect } from 'react';
import { Drawer, Form, Input, Select, DatePicker, message, Button } from 'antd';
import { useSelector } from 'react-redux';
import { RootState } from '../../store/store';
import { useCreateFollowUp, useUpdateFollowUp, FollowUp, FollowUpCreate } from '../../hooks/useFollowUps';
import { useDictItems } from '../../hooks/useDictItems';

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
  const createMutation = useCreateFollowUp();
  const updateMutation = useUpdateFollowUp();
  const { user } = useSelector((state: RootState) => state.auth);

  const { data: methodItems = [] } = useDictItems('跟进方式');
  const { data: conclusionItems = [] } = useDictItems('跟进结论');

  const methodOptions = methodItems.map(item => ({ value: item.name, label: item.name }));
  const conclusionOptions = conclusionItems.map(item => ({ value: item.name, label: item.name }));

  useEffect(() => {
    if (visible) {
      if (followUp) {
        form.setFieldsValue(followUp);
      } else {
        form.resetFields();
        form.setFieldsValue({
          terminal_customer_id,
          channel_id,
          lead_id,
          opportunity_id,
          project_id,
          follower_id: user?.id,
        });
      }
    }
  }, [visible, followUp, terminal_customer_id, channel_id, lead_id, opportunity_id, project_id, user?.id]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      const payload: FollowUpCreate = {
        ...values,
        follow_up_date: values.follow_up_date?.format?.('YYYY-MM-DD'),
        next_follow_up_date: values.next_follow_up_date?.format?.('YYYY-MM-DD'),
      };

      if (followUp) {
        await updateMutation.mutateAsync({ id: followUp.id, data: payload });
        message.success('更新成功');
      } else {
        await createMutation.mutateAsync(payload);
        message.success('添加成功');
      }

      form.resetFields();
      onClose();
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  return (
    <Drawer
      title={followUp ? '编辑跟进记录' : '添加跟进记录'}
      open={visible}
      onClose={onClose}
      maskClosable={false}
      destroyOnClose
      width={520}
    >
      <Form form={form} layout="vertical">
        <Form.Item name="follow_up_date" label="跟进日期" rules={[{ required: true, message: '请选择日期' }]}>
          <DatePicker style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item name="follow_up_method" label="跟进方式" rules={[{ required: true, message: '请选择方式' }]}>
          <Select placeholder="选择跟进方式">
            {methodOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>{opt.label}</Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item name="follow_up_content" label="跟进内容" rules={[{ required: true, message: '请输入内容' }]}>
          <TextArea rows={3} placeholder="记录跟进详情..." />
        </Form.Item>

        <Form.Item name="follow_up_conclusion" label="跟进结论" rules={[{ required: true, message: '请选择结论' }]}>
          <Select placeholder="选择跟进结论">
            {conclusionOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>{opt.label}</Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item name="next_action" label="下次行动">
          <Input placeholder="计划下一步行动" />
        </Form.Item>

        <Form.Item name="next_follow_up_date" label="下次跟进日期">
          <DatePicker style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item name="follower_id" hidden>
          <Input type="number" />
        </Form.Item>

        <Form.Item name="terminal_customer_id" hidden>
          <Input type="number" />
        </Form.Item>
        <Form.Item name="channel_id" hidden>
          <Input type="number" />
        </Form.Item>
        <Form.Item name="lead_id" hidden>
          <Input type="number" />
        </Form.Item>
        <Form.Item name="opportunity_id" hidden>
          <Input type="number" />
        </Form.Item>
        <Form.Item name="project_id" hidden>
          <Input type="number" />
        </Form.Item>

        <Form.Item>
          <Button type="primary" onClick={handleOk} loading={createMutation.isPending || updateMutation.isPending} block>
            保存
          </Button>
        </Form.Item>
      </Form>
    </Drawer>
  );
};

export default FollowUpModal;
