import React, { useEffect } from 'react';
import { Form, Input, Button, DatePicker, InputNumber, App } from 'antd';
import { useNineA, useCreateNineA, useUpdateNineA } from '../../hooks/useNineA';
import PageModal from '../common/PageModal';

const { TextArea } = Input;

interface NineAModalProps {
  visible: boolean;
  onClose: () => void;
  opportunityId: number;
  opportunityName: string;
}

const NineAModal: React.FC<NineAModalProps> = ({ visible, onClose, opportunityId, opportunityName }) => {
  const [form] = Form.useForm();
  const { message } = App.useApp();

  const { data: nineA, isLoading } = useNineA(opportunityId);
  const createMutation = useCreateNineA(opportunityId);
  const updateMutation = useUpdateNineA(opportunityId);

  useEffect(() => {
    if (visible) {
      if (nineA) {
        form.setFieldsValue(nineA);
      } else {
        form.resetFields();
      }
    }
  }, [visible, nineA, form]);

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      const payload = {
        ...values,
        close_date: values.close_date?.format?.('YYYY-MM-DD') || values.close_date,
      };

      if (nineA) {
        await updateMutation.mutateAsync(payload);
        message.success('9A分析更新成功');
      } else {
        await createMutation.mutateAsync(payload);
        message.success('9A分析已初始化');
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
      title={`9A 竞争性分析 - ${opportunityName}`}
      open={visible}
      onClose={onClose}
      width={720}
      loading={isLoading}
      footer={[
        <Button key="cancel" onClick={onClose}>
          取消
        </Button>,
        <Button
          key="submit"
          type="primary"
          className="btn--gradient"
          onClick={handleSave}
          loading={createMutation.isPending || updateMutation.isPending}
        >
          保存分析
        </Button>
      ]}
    >
      <Form form={form} layout="vertical">
        <Form.Item name="key_events" label="关键事件">
          <TextArea rows={3} placeholder="记录商机推进过程中的关键事件和时间节点" />
        </Form.Item>

        <Form.Item name="budget" label="项目预算">
          <InputNumber
            style={{ width: '100%' }}
            placeholder="预算金额"
            min={0}
            formatter={value => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
            parser={value => value!.replace(/\¥\s?|(,*)/g, '') as any}
          />
        </Form.Item>

        <Form.Item name="close_date" label="预计关单时间">
          <DatePicker style={{ width: '100%' }} placeholder="选择预计关单日期" />
        </Form.Item>

        <Form.Item name="decision_chain_influence" label="决策链影响度">
          <TextArea rows={3} placeholder="详细分析决策链条中各角色的影响力及我方覆盖情况" />
        </Form.Item>

        <Form.Item name="customer_challenges" label="客户挑战与痛点">
          <TextArea rows={3} placeholder="记录客户目前面临的主要业务挑战和痛点" />
        </Form.Item>

        <Form.Item name="customer_needs" label="客户需求与价值诉求">
          <TextArea rows={3} placeholder="分析客户对本次采购的真实需求和背后的价值诉求" />
        </Form.Item>

        <Form.Item name="solution_differentiation" label="解决方案差异化">
          <TextArea rows={3} placeholder="我方提供的解决方案及与竞争对手相比的差异化优势" />
        </Form.Item>

        <Form.Item name="competitors" label="竞争对手分析">
          <TextArea rows={3} placeholder="主要竞争对手的情况及其优劣势分析" />
        </Form.Item>

        <Form.Item name="buying_method" label="购买流程/方式">
          <TextArea rows={2} placeholder="客户内部的正式购买流程和具体的采购方式" />
        </Form.Item>
      </Form>
    </PageModal>
  );
};

export default NineAModal;
