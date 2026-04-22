import React, { useEffect } from 'react';
import { Drawer, Form, Input, Select, DatePicker, Button, App } from 'antd';
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
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const createMutation = useCreateFollowUp();
  const updateMutation = useUpdateFollowUp();
  const { user } = useSelector((state: RootState) => state.auth);

  const { data: methodItems = [] } = useDictItems('跟进方式');
  const { data: conclusionItems = [] } = useDictItems('跟进结论');
  // 新增：渠道拜访目的字典
  const { data: visitPurposeItems = [] } = useDictItems('拜访目的');

  const methodOptions = methodItems.map(item => ({ value: item.name, label: item.name }));
  const conclusionOptions = conclusionItems.map(item => ({ value: item.name, label: item.name }));
  const visitPurposeOptions = visitPurposeItems.map(item => ({ value: item.name, label: item.name }));

  // 判断是否为渠道跟进
  const isChannelFollowUp = !!channel_id && !lead_id && !opportunity_id && !project_id;
  
  // 设置表单标题
  const modalTitle = followUp 
    ? (isChannelFollowUp ? '编辑渠道拜访记录' : '编辑跟进记录')
    : (isChannelFollowUp ? '添加渠道拜访记录' : '添加跟进记录');

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
          // 设置默认跟进类型
          follow_up_type: isChannelFollowUp ? 'channel' : 'business',
        });
      }
    }
  }, [visible, followUp, terminal_customer_id, channel_id, lead_id, opportunity_id, project_id, user?.id, isChannelFollowUp, form]);

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
      title={modalTitle}
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

        {/* 业务跟进字段 - 仅在非渠道场景显示 */}
        {!isChannelFollowUp && (
          <>
            <Form.Item name="follow_up_conclusion" label="跟进结论" rules={[{ required: true, message: '请选择结论' }]}>
              <Select placeholder="选择跟进结论">
                {conclusionOptions.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item name="next_action" label="下一步行动">
              <Input placeholder="计划下一步行动" />
            </Form.Item>

            <Form.Item name="next_follow_up_date" label="下次跟进日期">
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
          </>
        )}

        {/* 渠道拜访字段 - 仅在渠道场景显示 */}
        {isChannelFollowUp && (
          <>
            <Form.Item name="visit_location" label="拜访地点">
              <Input placeholder="输入拜访地点" />
            </Form.Item>

            <Form.Item name="visit_attendees" label="参与人员">
              <Input placeholder="输入参与人员姓名，多个用逗号分隔" />
            </Form.Item>

            <Form.Item name="visit_purpose" label="拜访目的">
              <Select placeholder="选择拜访目的">
                {visitPurposeOptions.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>
          </>
        )}

        {/* 隐藏字段 */}
        <Form.Item name="follow_up_type" initialValue={isChannelFollowUp ? 'channel' : 'business'} hidden>
          <Input />
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
