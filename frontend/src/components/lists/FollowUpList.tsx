import React, { useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select, DatePicker, Card, Tag, message, Popconfirm, Descriptions, Alert } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, PhoneOutlined, EyeOutlined } from '@ant-design/icons';
import { useFollowUps, useCreateFollowUp, useUpdateFollowUp, useDeleteFollowUp, FollowUp, FollowUpCreate } from '../../hooks/useFollowUps';
import { useDictItems } from '../../hooks/useDictItems';
import { useLeads } from '../../hooks/useLeads';
import { useOpportunities } from '../../hooks/useOpportunities';
import { useProjects } from '../../hooks/useProjects';

const { Option } = Select;
const { Search } = Input;
const { TextArea } = Input;

interface FollowUpListProps {
  lead_id?: number;
  opportunity_id?: number;
  project_id?: number;
  showQuickAdd?: boolean;
}

const FollowUpList: React.FC<FollowUpListProps> = ({
  lead_id,
  opportunity_id,
  project_id,
  showQuickAdd = false,
}) => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isViewModalVisible, setIsViewModalVisible] = useState(false);
  const [editingFollowUp, setEditingFollowUp] = useState<FollowUp | null>(null);
  const [viewingFollowUp, setViewingFollowUp] = useState<FollowUp | null>(null);
  const [searchText, setSearchText] = useState('');
  const [methodFilter, setMethodFilter] = useState<string | null>(null);
  const [conclusionFilter, setConclusionFilter] = useState<string | null>(null);
  const [form] = Form.useForm();

  const filters = { lead_id, opportunity_id, project_id };
  const { data: followUps = [], isLoading } = useFollowUps(
    showQuickAdd ? undefined : filters
  );

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
  const updateMutation = useUpdateFollowUp();
  const deleteMutation = useDeleteFollowUp();

  const filteredFollowUps = followUps.filter(f => {
    const matchesSearch = !searchText || 
      f.follow_up_content?.toLowerCase().includes(searchText.toLowerCase());
    const matchesMethod = !methodFilter || f.follow_up_method === methodFilter;
    const matchesConclusion = !conclusionFilter || f.follow_up_conclusion === conclusionFilter;
    return matchesSearch && matchesMethod && matchesConclusion;
  });

  const getConclusionColor = (conclusion: string) => {
    const colorMap: Record<string, string> = {
      '有意向': 'green',
      '待跟进': 'blue',
      '洽谈中': 'cyan',
      '已报价': 'purple',
      '已转化': 'success',
      '无意向': 'orange',
      '已流失': 'red',
    };
    return colorMap[conclusion] || 'default';
  };

  const handleCreate = () => {
    setEditingFollowUp(null);
    form.resetFields();
    form.setFieldsValue({
      lead_id,
      opportunity_id,
      project_id,
      follow_up_date: undefined,
    });
    setIsModalVisible(true);
  };

  const handleEdit = (followUp: FollowUp) => {
    setEditingFollowUp(followUp);
    form.setFieldsValue(followUp);
    setIsModalVisible(true);
  };

  const handleView = (followUp: FollowUp) => {
    setViewingFollowUp(followUp);
    setIsViewModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteMutation.mutateAsync(id);
      message.success('删除成功');
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '删除失败');
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      
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

      if (editingFollowUp) {
        await updateMutation.mutateAsync({ id: editingFollowUp.id, followUp: payload });
        message.success('更新成功');
      } else {
        await createMutation.mutateAsync(payload);
        message.success('创建成功');
      }

      setIsModalVisible(false);
      form.resetFields();
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  const columns = [
    {
      title: '跟进日期',
      dataIndex: 'follow_up_date',
      key: 'follow_up_date',
      width: 110,
      render: (date: string) => date || '-',
    },
    {
      title: '跟进方式',
      dataIndex: 'follow_up_method',
      key: 'follow_up_method',
      width: 90,
    },
    {
      title: '跟进内容',
      dataIndex: 'follow_up_content',
      key: 'follow_up_content',
      ellipsis: true,
    },
    {
      title: '跟进结论',
      dataIndex: 'follow_up_conclusion',
      key: 'follow_up_conclusion',
      width: 90,
      render: (conclusion: string) => (
        <Tag color={getConclusionColor(conclusion)}>{conclusion}</Tag>
      ),
    },
    {
      title: '关联对象',
      key: 'related',
      width: 180,
      render: (_: any, record: FollowUp) => {
        const items = [];
        if (record.lead_name) items.push(`线索: ${record.lead_name}`);
        if (record.opportunity_name) items.push(`商机: ${record.opportunity_name}`);
        if (record.project_name) items.push(`项目: ${record.project_name}`);
        return items.length > 0 ? items.join(' | ') : '-';
      },
    },
    {
      title: '关联客户',
      dataIndex: 'terminal_customer_name',
      key: 'terminal_customer_name',
      width: 120,
      render: (name: string) => name || '-',
    },
    {
      title: '下次跟进',
      dataIndex: 'next_follow_up_date',
      key: 'next_follow_up_date',
      width: 110,
      render: (date: string) => date || '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 160,
      render: (_: any, record: FollowUp) => (
        <Space size="small">
          <Button size="small" icon={<EyeOutlined />} onClick={() => handleView(record)}>
            查看
          </Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Popconfirm
            title="确定删除该跟进记录吗？"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Card
      title={
        <Space>
          <PhoneOutlined />
          跟进记录
        </Space>
      }
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          添加跟进
        </Button>
      }
    >
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Search
            placeholder="搜索跟进内容"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 200 }}
          />
          <Select
            placeholder="跟进方式"
            value={methodFilter}
            onChange={setMethodFilter}
            style={{ width: 120 }}
            allowClear
          >
            {methodOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>{opt.label}</Option>
            ))}
          </Select>
          <Select
            placeholder="跟进结论"
            value={conclusionFilter}
            onChange={setConclusionFilter}
            style={{ width: 120 }}
            allowClear
          >
            {conclusionOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>{opt.label}</Option>
            ))}
          </Select>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={filteredFollowUps}
        loading={isLoading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        size="small"
        scroll={{ x: 1100 }}
      />

      <Modal
        title={editingFollowUp ? '编辑跟进记录' : '添加跟进记录'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => setIsModalVisible(false)}
        okText="保存"
        cancelText="取消"
        width={700}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
      >
        <Alert
          message="请至少选择一个关联对象（线索/商机/项目），关联客户将自动获取"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <Form form={form} layout="vertical">
          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="follow_up_date" label="跟进日期" rules={[{ required: true }]}>
              <DatePicker style={{ width: 150 }} />
            </Form.Item>
            <Form.Item name="follow_up_method" label="跟进方式" rules={[{ required: true }]}>
              <Select style={{ width: 150 }} placeholder="选择方式">
                {methodOptions.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>
            <Form.Item name="follow_up_conclusion" label="跟进结论" rules={[{ required: true }]}>
              <Select style={{ width: 150 }} placeholder="选择结论">
                {conclusionOptions.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>
          </Space>

          <Form.Item name="follow_up_content" label="跟进内容" rules={[{ required: true }]}>
            <TextArea rows={3} placeholder="记录跟进详情..." />
          </Form.Item>

          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="next_action" label="下次行动" style={{ width: 280 }}>
              <Input placeholder="计划下一步行动" />
            </Form.Item>
            <Form.Item name="next_follow_up_date" label="下次跟进日期">
              <DatePicker style={{ width: 150 }} />
            </Form.Item>
          </Space>

          <Form.Item label="关联对象（至少选一个）" required>
            <Space style={{ width: '100%' }} size="middle">
              <Form.Item name="lead_id" noStyle>
                <Select
                  style={{ width: 200 }}
                  placeholder="选择线索"
                  showSearch
                  optionFilterProp="children"
                  allowClear
                  disabled={!!lead_id}
                >
                  {leadOptions.map(opt => (
                    <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                  ))}
                </Select>
              </Form.Item>
              <Form.Item name="opportunity_id" noStyle>
                <Select
                  style={{ width: 200 }}
                  placeholder="选择商机"
                  showSearch
                  optionFilterProp="children"
                  allowClear
                  disabled={!!opportunity_id}
                >
                  {opportunityOptions.map(opt => (
                    <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                  ))}
                </Select>
              </Form.Item>
              <Form.Item name="project_id" noStyle>
                <Select
                  style={{ width: 200 }}
                  placeholder="选择项目"
                  showSearch
                  optionFilterProp="children"
                  allowClear
                  disabled={!!project_id}
                >
                  {projectOptions.map(opt => (
                    <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="跟进记录详情"
        open={isViewModalVisible}
        onCancel={() => setIsViewModalVisible(false)}
        footer={<Button onClick={() => setIsViewModalVisible(false)}>关闭</Button>}
        width={700}
      >
        {viewingFollowUp && (
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="跟进日期">{viewingFollowUp.follow_up_date || '无'}</Descriptions.Item>
            <Descriptions.Item label="跟进方式">{viewingFollowUp.follow_up_method}</Descriptions.Item>
            <Descriptions.Item label="跟进结论">
              <Tag color={getConclusionColor(viewingFollowUp.follow_up_conclusion)}>
                {viewingFollowUp.follow_up_conclusion}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="跟进人">{viewingFollowUp.follower_name || `ID: ${viewingFollowUp.follower_id}`}</Descriptions.Item>
            <Descriptions.Item label="跟进内容" span={2}>{viewingFollowUp.follow_up_content}</Descriptions.Item>
            <Descriptions.Item label="下次行动">{viewingFollowUp.next_action || '无'}</Descriptions.Item>
            <Descriptions.Item label="下次跟进日期">{viewingFollowUp.next_follow_up_date || '无'}</Descriptions.Item>
            <Descriptions.Item label="关联客户">{viewingFollowUp.terminal_customer_name || '无'}</Descriptions.Item>
            <Descriptions.Item label="关联线索">{viewingFollowUp.lead_name || '无'}</Descriptions.Item>
            <Descriptions.Item label="关联商机">{viewingFollowUp.opportunity_name || '无'}</Descriptions.Item>
            <Descriptions.Item label="关联项目">{viewingFollowUp.project_name || '无'}</Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </Card>
  );
};

export default FollowUpList;