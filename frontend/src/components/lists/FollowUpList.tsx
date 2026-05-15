import React, { useMemo, useState } from 'react';
import { Alert, App, Button, Card, DatePicker, Descriptions, Form, Input, Popconfirm, Select, Space, Table, Tag, Row, Col } from 'antd';
import { PlusOutlined, EyeOutlined, DeleteOutlined, PhoneOutlined } from '@ant-design/icons';
import { useSearchParams } from 'react-router-dom';
import { useFollowUps, useCreateFollowUp, useUpdateFollowUp, useDeleteFollowUp, FollowUp } from '../../hooks/useFollowUps';
import { useDictItems } from '../../hooks/useDictItems';
import PageScaffold from '../../components/common/PageScaffold';
import PageModal from '../../components/common/PageModal';

const { Option } = Select;

interface FollowUpListProps {
  mode?: 'business' | 'channel';
  channel_id?: number;
}

const FollowUpList: React.FC<FollowUpListProps> = ({ mode = 'business', channel_id }) => {
  const { message, modal } = App.useApp();
  const [searchParams] = useSearchParams();
  const customerId = searchParams.get('customer_id');
  const leadId = searchParams.get('lead_id');
  const opportunityId = searchParams.get('opportunity_id');
  const projectId = searchParams.get('project_id');

  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isViewModalVisible, setIsViewModalVisible] = useState(false);
  const [editingFollowUp, setEditingFollowUp] = useState<FollowUp | null>(null);
  const [viewingFollowUp, setViewingFollowUp] = useState<FollowUp | null>(null);
  const [searchText, setSearchText] = useState('');
  const [methodFilter, setMethodFilter] = useState<string | null>(null);
  const [conclusionFilter, setConclusionFilter] = useState<string | null>(null);
  const [form] = Form.useForm();

  const isChannelMode = mode === 'channel';
  const effectiveChannelId = channel_id || (searchParams.get('channel_id') ? Number(searchParams.get('channel_id')) : undefined);

  const { data: followUps = [], isLoading } = useFollowUps({
    terminal_customer_id: customerId ? Number(customerId) : undefined,
    channel_id: effectiveChannelId,
    lead_id: leadId ? Number(leadId) : undefined,
    opportunity_id: opportunityId ? Number(opportunityId) : undefined,
    project_id: projectId ? Number(projectId) : undefined,
    follow_up_type: mode,
  });

  const { data: methodItems = [] } = useDictItems('跟进方式');
  const { data: conclusionItems = [] } = useDictItems('跟进结论');

  const methodOptions = methodItems.map(item => ({ value: item.name, label: item.name }));
  const conclusionOptions = conclusionItems.map(item => ({ value: item.name, label: item.name }));

  const createMutation = useCreateFollowUp();
  const updateMutation = useUpdateFollowUp();
  const deleteMutation = useDeleteFollowUp();

  const filteredFollowUps = followUps.filter(f => {
    const matchesSearch = !searchText || f.follow_up_content.toLowerCase().includes(searchText.toLowerCase());
    const matchesMethod = !methodFilter || f.follow_up_method === methodFilter;
    const matchesConclusion = !conclusionFilter || f.follow_up_conclusion === conclusionFilter;
    return matchesSearch && matchesMethod && matchesConclusion;
  });

  const handleCreate = () => {
    setEditingFollowUp(null);
    form.resetFields();
    form.setFieldsValue({
      follow_up_date: new Date().toISOString().split('T')[0],
      follow_up_method: '电话',
      follow_up_type: mode,
      terminal_customer_id: customerId ? Number(customerId) : undefined,
      channel_id: effectiveChannelId,
      lead_id: leadId ? Number(leadId) : undefined,
      opportunity_id: opportunityId ? Number(opportunityId) : undefined,
      project_id: projectId ? Number(projectId) : undefined,
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

  const handleDelete = (id: number) => {
    modal.confirm({
      title: '确定删除该跟进记录吗？',
      content: '此操作不可恢复',
      okType: 'danger',
      onOk: async () => {
        try {
          await deleteMutation.mutateAsync(id);
          message.success('记录已删除');
        } catch (error) {}
      }
    });
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      if (editingFollowUp) {
        await updateMutation.mutateAsync({ id: editingFollowUp.id, data: values });
        message.success('记录已更新');
      } else {
        await createMutation.mutateAsync(values);
        message.success('记录已保存');
      }
      setIsModalVisible(false);
      form.resetFields();
    } catch (error) {}
  };

  const pageLabels = isChannelMode ? {
    cardTitle: '渠道跟进记录',
    searchPlaceholder: '搜索跟进内容',
    methodFilter: '跟进方式',
    createButton: '新增渠道跟进',
    editTitle: '编辑渠道跟进',
    createTitle: '记录新渠道沟通'
  } : {
    cardTitle: '业务跟进记录',
    searchPlaceholder: '搜索跟进内容',
    methodFilter: '跟进方式',
    createButton: '新增业务跟进',
    editTitle: '编辑跟进记录',
    createTitle: '记录新业务进展'
  };

  const columns = [
    { title: '日期', dataIndex: 'follow_up_date', key: 'follow_up_date', width: 110 },
    { title: '跟进方式', dataIndex: 'follow_up_method', key: 'follow_up_method', width: 100, render: (m: string) => <Tag style={{ border: 'none', background: '#f1f5f9' }}>{m}</Tag> },
    { title: '跟进内容', dataIndex: 'follow_up_content', key: 'follow_up_content', ellipsis: true },
    { title: '结论', dataIndex: 'follow_up_conclusion', key: 'follow_up_conclusion', width: 100, render: (c: string) => <Tag color="blue" style={{ border: 'none' }}>{c}</Tag> },
    { title: '跟进人', dataIndex: 'follower_name', key: 'follower_name', width: 100 },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: FollowUp) => (
        <Space size="middle">
          <Button size="small" icon={<EyeOutlined />} onClick={() => handleView(record)}>详情</Button>
          <Button size="small" icon={<DeleteOutlined />} danger onClick={() => handleDelete(record.id)}>删除</Button>
        </Space>
      ),
    },
  ];

  return (
    <PageScaffold
      title={pageLabels.cardTitle}
      breadcrumbItems={[{ title: '首页' }, { title: pageLabels.cardTitle }]}
      extra={
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleCreate}
          size="large"
          className="btn--gradient"
          style={{ height: '40px', padding: '0 20px' }}
        >
          {pageLabels.createButton}
        </Button>
      }
      filters={
        <Space size={16} wrap>
          <Input.Search
            placeholder={pageLabels.searchPlaceholder}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 280 }}
            size="middle"
          />
          <Select
            placeholder={pageLabels.methodFilter}
            value={methodFilter}
            onChange={setMethodFilter}
            style={{ width: 150 }}
            allowClear
          >
            {methodOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>{opt.label}</Option>
            ))}
          </Select>
          {!isChannelMode && (
            <Select
              placeholder="跟进结论"
              value={conclusionFilter}
              onChange={setConclusionFilter}
              style={{ width: 150 }}
              allowClear
            >
              {conclusionOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          )}
        </Space>
      }
    >
      <Table
        columns={columns}
        dataSource={filteredFollowUps}
        loading={isLoading}
        rowKey="id"
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条数据`,
        }}
        className="customer-table"
        bordered={false}
      />

      <PageModal
        title={editingFollowUp ? pageLabels.editTitle : pageLabels.createTitle}
        open={isModalVisible}
        onClose={() => setIsModalVisible(false)}
        width={640}
        footer={[
          <Button key="cancel" onClick={() => setIsModalVisible(false)}>
            取消
          </Button>,
          <Button
            key="submit"
            type="primary"
            className="btn--gradient"
            onClick={handleSave}
            loading={createMutation.isPending || updateMutation.isPending}
          >
            保存记录
          </Button>
        ]}
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="follow_up_date" label="跟进日期" rules={[{ required: true }]}>
                <Input type="date" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="follow_up_method" label="跟进方式" rules={[{ required: true }]}>
                <Select>
                  {methodOptions.map(opt => (
                    <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="follow_up_content" label="跟进详情" rules={[{ required: true, message: '请输入跟进内容' }]}>
            <Input.TextArea rows={4} placeholder="详细记录本次沟通的核心内容和达成的一致意见..." />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="follow_up_conclusion" label="跟进结论">
                <Select placeholder="选择本次沟通后的定性结论">
                  {conclusionOptions.map(opt => (
                    <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="next_action" label="下一步计划">
                <Input placeholder="例如：下周提供报价单" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </PageModal>

      <PageModal
        title="跟进详情回顾"
        open={isViewModalVisible}
        onClose={() => setIsViewModalVisible(false)}
        width={600}
        footer={[<Button key="close" onClick={() => setIsViewModalVisible(false)}>关闭</Button>]}
      >
        {viewingFollowUp && (
          <Descriptions column={2} bordered={false} layout="vertical">
            <Descriptions.Item label="日期">{viewingFollowUp.follow_up_date}</Descriptions.Item>
            <Descriptions.Item label="方式">{viewingFollowUp.follow_up_method}</Descriptions.Item>
            <Descriptions.Item label="结论" span={2}><Tag color="blue">{viewingFollowUp.follow_up_conclusion}</Tag></Descriptions.Item>
            <Descriptions.Item label="跟进内容" span={2}><div style={{ background: '#f8fafc', padding: '16px', borderRadius: '8px' }}>{viewingFollowUp.follow_up_content}</div></Descriptions.Item>
            <Descriptions.Item label="下一步行动" span={2}>{viewingFollowUp.next_action || '-'}</Descriptions.Item>
          </Descriptions>
        )}
      </PageModal>
    </PageScaffold>
  );
};

export default FollowUpList;
