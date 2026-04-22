import React, { useEffect } from 'react';
import { App, Card, Form, Input, Select, Button, Space, DatePicker, Alert } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useCreateFollowUp, FollowUpCreate } from '../../hooks/useFollowUps';
import { useDictItems } from '../../hooks/useDictItems';
import { useLeads } from '../../hooks/useLeads';
import { useOpportunities } from '../../hooks/useOpportunities';
import { useProjects } from '../../hooks/useProjects';

const { Option } = Select;
const { TextArea } = Input;

const FollowUpForm: React.FC = () => {
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const { data: methodItems = [] } = useDictItems('跟进方式');
  const { data: conclusionItems = [] } = useDictItems('跟进结论');
  const { data: leads = [] } = useLeads();
  const { data: opportunities = [] } = useOpportunities();
  const { data: projects = [] } = useProjects();

  const methodOptions = methodItems.map(item => ({ value: item.name, label: item.name }));
  const conclusionOptions = conclusionItems.map(item => ({ value: item.name, label: item.name }));
  const leadOptions = leads.map(l => ({ value: l.id, label: `${l.lead_code} - ${l.lead_name}` }));
  const opportunityOptions = opportunities.map(o => ({ value: o.id, label: `${o.opportunity_code} - ${o.opportunity_name}` }));
  const projectOptions = projects.map(p => ({ value: p.id, label: `${p.project_code} - ${p.project_name}` }));

  const createMutation = useCreateFollowUp();

  useEffect(() => {
    // 不预设任何关联，用户需手动选择
  }, [form]);

  const onFinish = async (values: any) => {
    try {
      // 验证至少有一个关联
      if (!values.lead_id && !values.opportunity_id && !values.project_id) {
        message.error('关联线索、关联商机、关联项目至少需要选择一个');
        return;
      }

      const payload: FollowUpCreate = {
        lead_id: values.lead_id,
        opportunity_id: values.opportunity_id,
        project_id: values.project_id,
        follow_up_date: values.follow_up_date?.format?.('YYYY-MM-DD'),
        follow_up_method: values.follow_up_method,
        follow_up_content: values.follow_up_content,
        follow_up_conclusion: values.follow_up_conclusion,
        next_action: values.next_action,
        next_follow_up_date: values.next_follow_up_date?.format?.('YYYY-MM-DD'),
      };

      await createMutation.mutateAsync(payload);
      message.success('跟进记录创建成功');
      navigate('/business-follow-ups');
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  return (
    <Card title="添加跟进记录" style={{ maxWidth: 800 }}>
      <Alert
        message="请至少选择一个关联对象（线索/商机/项目），关联客户将自动获取"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        disabled={createMutation.isPending}
      >
        <Space style={{ width: '100%' }} size="large">
          <Form.Item
            name="follow_up_date"
            label="跟进日期"
            rules={[{ required: true, message: '请选择跟进日期' }]}
            style={{ width: 150 }}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="follow_up_method"
            label="跟进方式"
            rules={[{ required: true, message: '请选择跟进方式' }]}
            style={{ width: 150 }}
          >
            <Select placeholder="选择方式">
              {methodOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="follow_up_conclusion"
            label="跟进结论"
            rules={[{ required: true, message: '请选择跟进结论' }]}
            style={{ width: 150 }}
          >
            <Select placeholder="选择结论">
              {conclusionOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>
        </Space>

        <Form.Item
          name="follow_up_content"
          label="跟进内容"
          rules={[{ required: true, message: '请输入跟进内容' }]}
        >
          <TextArea rows={4} placeholder="记录跟进详情..." />
        </Form.Item>

        <Space style={{ width: '100%' }} size="large">
          <Form.Item name="next_action" label="下次行动" style={{ width: 300 }}>
            <Input placeholder="计划下一步行动" />
          </Form.Item>
          <Form.Item name="next_follow_up_date" label="下次跟进日期" style={{ width: 150 }}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
        </Space>

        <Form.Item label="关联对象（至少选一个）" required>
          <Space style={{ width: '100%' }} size="middle">
            <Form.Item name="lead_id" noStyle>
              <Select
                style={{ width: 220 }}
                placeholder="选择线索"
                showSearch
                optionFilterProp="children"
                allowClear
              >
                {leadOptions.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>
            <Form.Item name="opportunity_id" noStyle>
              <Select
                style={{ width: 220 }}
                placeholder="选择商机"
                showSearch
                optionFilterProp="children"
                allowClear
              >
                {opportunityOptions.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>
            <Form.Item name="project_id" noStyle>
              <Select
                style={{ width: 220 }}
                placeholder="选择项目"
                showSearch
                optionFilterProp="children"
                allowClear
              >
                {projectOptions.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>
          </Space>
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={createMutation.isPending}>
              创建跟进记录
            </Button>
            <Button onClick={() => navigate('/business-follow-ups')}>
              取消
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default FollowUpForm;
