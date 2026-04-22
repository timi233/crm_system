import React, { useMemo, useState } from 'react';
import {
  Alert,
  App,
  Button,
  Card,
  DatePicker,
  Descriptions,
  Drawer,
  Form,
  Input,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
} from 'antd';
import {
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  PhoneOutlined,
  PlusOutlined,
} from '@ant-design/icons';

import {
  FollowUp,
  FollowUpCreate,
  useCreateFollowUp,
  useDeleteFollowUp,
  useFollowUps,
  useUpdateFollowUp,
} from '../../hooks/useFollowUps';
import { useDictItems } from '../../hooks/useDictItems';
import { useLeads } from '../../hooks/useLeads';
import { useOpportunities } from '../../hooks/useOpportunities';
import { useProjects } from '../../hooks/useProjects';
import { useChannels } from '../../hooks/useChannels';

const { Option } = Select;
const { Search } = Input;
const { TextArea } = Input;

type FollowUpMode = 'business' | 'channel';

interface FollowUpListProps {
  lead_id?: number;
  opportunity_id?: number;
  project_id?: number;
  channel_id?: number;
  showQuickAdd?: boolean;
  mode?: FollowUpMode;
}

const FollowUpList: React.FC<FollowUpListProps> = ({
  lead_id,
  opportunity_id,
  project_id,
  channel_id,
  showQuickAdd = false,
  mode,
}) => {
  const { message } = App.useApp();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isViewModalVisible, setIsViewModalVisible] = useState(false);
  const [editingFollowUp, setEditingFollowUp] = useState<FollowUp | null>(null);
  const [viewingFollowUp, setViewingFollowUp] = useState<FollowUp | null>(null);
  const [searchText, setSearchText] = useState('');
  const [methodFilter, setMethodFilter] = useState<string | null>(null);
  const [conclusionFilter, setConclusionFilter] = useState<string | null>(null);
  const [form] = Form.useForm();

  const effectiveMode: FollowUpMode =
    mode || (channel_id && !lead_id && !opportunity_id && !project_id ? 'channel' : 'business');
  const isChannelMode = effectiveMode === 'channel';
  const pageLabels = isChannelMode
    ? {
        cardTitle: '渠道跟进',
        createButton: '新增渠道跟进',
        editTitle: '编辑渠道跟进',
        createTitle: '新增渠道跟进',
        detailTitle: '渠道跟进详情',
        date: '拜访日期',
        method: '拜访方式',
        content: '拜访内容',
        actor: '拜访人',
        customer: '关联终端客户',
        methodFilter: '拜访方式',
        searchPlaceholder: '搜索拜访内容',
        guidance: '请关联渠道，并按拜访场景填写拜访目的、地点、参与人员',
      }
    : {
        cardTitle: '业务跟进',
        createButton: '新增业务跟进',
        editTitle: '编辑业务跟进',
        createTitle: '新增业务跟进',
        detailTitle: '业务跟进详情',
        date: '跟进日期',
        method: '跟进方式',
        content: '跟进内容',
        actor: '跟进人',
        customer: '关联终端客户',
        methodFilter: '跟进方式',
        searchPlaceholder: '搜索跟进内容',
        guidance: '请至少关联一个业务对象（线索/商机/项目）',
      };

  const filters = {
    lead_id,
    opportunity_id,
    project_id,
    channel_id,
    follow_up_type: effectiveMode,
  };

  const { data: followUps = [], isLoading } = useFollowUps(showQuickAdd ? { follow_up_type: effectiveMode } : filters);

  const { data: businessMethodItems = [] } = useDictItems('跟进方式');
  const { data: visitMethodItems = [] } = useDictItems('拜访方式');
  const { data: conclusionItems = [] } = useDictItems('跟进结论');
  const { data: visitPurposeItems = [] } = useDictItems('拜访目的');
  const { data: leads = [] } = useLeads();
  const { data: opportunities = [] } = useOpportunities();
  const { data: projects = [] } = useProjects();
  const { data: channels = [] } = useChannels(undefined, isChannelMode);

  const methodItems = isChannelMode && visitMethodItems.length > 0 ? visitMethodItems : businessMethodItems;
  const methodOptions = methodItems.map((item) => ({ value: item.name, label: item.name }));
  const conclusionOptions = conclusionItems.map((item) => ({ value: item.name, label: item.name }));
  const purposeOptions = visitPurposeItems.map((item) => ({ value: item.name, label: item.name }));
  const leadOptions = leads.map((l) => ({ value: l.id, label: `${l.lead_code} - ${l.lead_name}` }));
  const opportunityOptions = opportunities.map((o) => ({
    value: o.id,
    label: `${o.opportunity_code} - ${o.opportunity_name}`,
  }));
  const projectOptions = projects.map((p) => ({ value: p.id, label: `${p.project_code} - ${p.project_name}` }));
  const channelOptions = channels.map((c) => ({ value: c.id, label: `${c.channel_code} - ${c.company_name}` }));

  const createMutation = useCreateFollowUp();
  const updateMutation = useUpdateFollowUp();
  const deleteMutation = useDeleteFollowUp();

  const filteredFollowUps = useMemo(() => {
    return followUps.filter((f) => {
      const matchesSearch = !searchText || f.follow_up_content?.toLowerCase().includes(searchText.toLowerCase());
      const matchesMethod = !methodFilter || f.follow_up_method === methodFilter;
      const matchesConclusion = isChannelMode || !conclusionFilter || f.follow_up_conclusion === conclusionFilter;
      return matchesSearch && matchesMethod && matchesConclusion;
    });
  }, [conclusionFilter, followUps, isChannelMode, methodFilter, searchText]);

  const getConclusionColor = (conclusion?: string) => {
    if (!conclusion) return 'default';
    const colorMap: Record<string, string> = {
      有意向: 'green',
      待跟进: 'blue',
      洽谈中: 'cyan',
      已报价: 'purple',
      已转化: 'success',
      无意向: 'orange',
      已流失: 'red',
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
      channel_id,
      follow_up_type: effectiveMode,
      follow_up_date: undefined,
      next_follow_up_date: undefined,
    });
    setIsModalVisible(true);
  };

  const handleEdit = (followUp: FollowUp) => {
    setEditingFollowUp(followUp);
    form.setFieldsValue({
      ...followUp,
      follow_up_type: followUp.follow_up_type || effectiveMode,
    });
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

      if (isChannelMode && !values.channel_id) {
        message.error('渠道跟进必须选择关联渠道');
        return;
      }

      if (!isChannelMode && !values.lead_id && !values.opportunity_id && !values.project_id) {
        message.error('业务跟进至少关联线索、商机、项目中的一个');
        return;
      }

      const payload: FollowUpCreate = {
        lead_id: values.lead_id,
        opportunity_id: values.opportunity_id,
        project_id: values.project_id,
        channel_id: values.channel_id,
        follow_up_type: effectiveMode,
        follow_up_date: values.follow_up_date?.format?.('YYYY-MM-DD'),
        follow_up_method: values.follow_up_method,
        follow_up_content: values.follow_up_content,
        follow_up_conclusion: values.follow_up_conclusion,
        next_action: values.next_action,
        next_follow_up_date: values.next_follow_up_date?.format?.('YYYY-MM-DD'),
        visit_location: values.visit_location,
        visit_attendees: values.visit_attendees,
        visit_purpose: values.visit_purpose,
      };

      if (editingFollowUp) {
        await updateMutation.mutateAsync({ id: editingFollowUp.id, data: payload });
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

  const columns: any[] = [
    {
      title: pageLabels.date,
      dataIndex: 'follow_up_date',
      key: 'follow_up_date',
      width: 120,
      render: (date: string) => date || '-',
    },
    {
      title: pageLabels.method,
      dataIndex: 'follow_up_method',
      key: 'follow_up_method',
      width: 100,
    },
    {
      title: pageLabels.content,
      dataIndex: 'follow_up_content',
      key: 'follow_up_content',
      ellipsis: true,
    },
  ];

  if (!isChannelMode) {
    columns.push({
      title: '跟进结论',
      dataIndex: 'follow_up_conclusion',
      key: 'follow_up_conclusion',
      width: 110,
      render: (conclusion: string) => <Tag color={getConclusionColor(conclusion)}>{conclusion || '-'}</Tag>,
    });
    columns.push({
      title: '关联对象',
      key: 'related',
      width: 220,
      render: (_: unknown, record: FollowUp) => {
        const items: string[] = [];
        if (record.lead_name) items.push(`线索: ${record.lead_name}`);
        if (record.opportunity_name) items.push(`商机: ${record.opportunity_name}`);
        if (record.project_name) items.push(`项目: ${record.project_name}`);
        return items.length > 0 ? items.join(' | ') : '-';
      },
    });
  } else {
    columns.push({
      title: '关联渠道',
      dataIndex: 'channel_name',
      key: 'channel_name',
      width: 170,
      render: (name: string) => name || '-',
    });
    columns.push({
      title: '拜访目的',
      dataIndex: 'visit_purpose',
      key: 'visit_purpose',
      width: 120,
      render: (value: string) => value || '-',
    });
    columns.push({
      title: '拜访地点',
      dataIndex: 'visit_location',
      key: 'visit_location',
      width: 140,
      render: (value: string) => value || '-',
    });
  }

  columns.push({
    title: pageLabels.customer,
    dataIndex: 'terminal_customer_name',
    key: 'terminal_customer_name',
    width: 140,
    render: (name: string) => name || '-',
  });

  if (!isChannelMode) {
    columns.push({
      title: '下次跟进',
      dataIndex: 'next_follow_up_date',
      key: 'next_follow_up_date',
      width: 120,
      render: (date: string) => date || '-',
    });
  }

  columns.push({
    title: '操作',
    key: 'action',
    width: 165,
    render: (_: unknown, record: FollowUp) => (
      <Space size="small">
        <Button size="small" icon={<EyeOutlined />} onClick={() => handleView(record)}>
          查看
        </Button>
        <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
          编辑
        </Button>
        <Popconfirm title="确定删除该记录吗？" onConfirm={() => handleDelete(record.id)}>
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      </Space>
    ),
  });

  return (
    <Card
      title={
        <Space>
          <PhoneOutlined />
          {pageLabels.cardTitle}
        </Space>
      }
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          {pageLabels.createButton}
        </Button>
      }
    >
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Search
            placeholder={pageLabels.searchPlaceholder}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 220 }}
          />
          <Select
            placeholder={pageLabels.methodFilter}
            value={methodFilter}
            onChange={setMethodFilter}
            style={{ width: 130 }}
            allowClear
          >
            {methodOptions.map((opt) => (
              <Option key={opt.value} value={opt.value}>
                {opt.label}
              </Option>
            ))}
          </Select>
          {!isChannelMode && (
            <Select
              placeholder="跟进结论"
              value={conclusionFilter}
              onChange={setConclusionFilter}
              style={{ width: 130 }}
              allowClear
            >
              {conclusionOptions.map((opt) => (
                <Option key={opt.value} value={opt.value}>
                  {opt.label}
                </Option>
              ))}
            </Select>
          )}
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={filteredFollowUps}
        loading={isLoading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        size="small"
        scroll={{ x: 1200 }}
      />

      <Drawer
        title={editingFollowUp ? pageLabels.editTitle : pageLabels.createTitle}
        open={isModalVisible}
        onClose={() => setIsModalVisible(false)}
        width={560}
        maskClosable={false}
        destroyOnClose
      >
        <Alert
          message={pageLabels.guidance}
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <Form form={form} layout="vertical">
          <Space style={{ width: '100%' }} size="large" wrap>
            <Form.Item name="follow_up_date" label={pageLabels.date} rules={[{ required: true }]}>
              <DatePicker style={{ width: 160 }} />
            </Form.Item>
            <Form.Item name="follow_up_method" label={pageLabels.method} rules={[{ required: true }]}>
              <Select style={{ width: 160 }} placeholder="请选择">
                {methodOptions.map((opt) => (
                  <Option key={opt.value} value={opt.value}>
                    {opt.label}
                  </Option>
                ))}
              </Select>
            </Form.Item>
            {!isChannelMode && (
              <Form.Item name="follow_up_conclusion" label="跟进结论" rules={[{ required: true }]}>
                <Select style={{ width: 160 }} placeholder="请选择">
                  {conclusionOptions.map((opt) => (
                    <Option key={opt.value} value={opt.value}>
                      {opt.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            )}
          </Space>

          <Form.Item name="follow_up_content" label={pageLabels.content} rules={[{ required: true }]}>
            <TextArea rows={3} placeholder={isChannelMode ? '记录渠道拜访详情...' : '记录业务跟进详情...'} />
          </Form.Item>

          {isChannelMode ? (
            <Space style={{ width: '100%' }} size="large" wrap>
              <Form.Item name="visit_purpose" label="拜访目的" style={{ width: 160 }}>
                <Select placeholder="可选" allowClear>
                  {purposeOptions.map((opt) => (
                    <Option key={opt.value} value={opt.value}>
                      {opt.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
              <Form.Item name="visit_location" label="拜访地点" style={{ width: 170 }}>
                <Input placeholder="可选" />
              </Form.Item>
              <Form.Item name="visit_attendees" label="参与人员" style={{ width: 170 }}>
                <Input placeholder="可选" />
              </Form.Item>
            </Space>
          ) : (
            <Space style={{ width: '100%' }} size="large" wrap>
              <Form.Item name="next_action" label="下次行动" style={{ width: 300 }}>
                <Input placeholder="计划下一步行动" />
              </Form.Item>
              <Form.Item name="next_follow_up_date" label="下次跟进日期">
                <DatePicker style={{ width: 160 }} />
              </Form.Item>
            </Space>
          )}

          {isChannelMode ? (
            <Form.Item label="关联渠道" required>
              <Form.Item name="channel_id" noStyle>
                <Select
                  style={{ width: '100%' }}
                  placeholder="选择渠道"
                  showSearch
                  optionFilterProp="children"
                  allowClear
                  disabled={!!channel_id}
                >
                  {channelOptions.map((opt) => (
                    <Option key={opt.value} value={opt.value}>
                      {opt.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Form.Item>
          ) : (
            <Form.Item label="关联对象（至少选择一个）" required>
              <Space style={{ width: '100%' }} size="middle" wrap>
                <Form.Item name="lead_id" noStyle>
                  <Select
                    style={{ width: 160 }}
                    placeholder="选择线索"
                    showSearch
                    optionFilterProp="children"
                    allowClear
                    disabled={!!lead_id}
                  >
                    {leadOptions.map((opt) => (
                      <Option key={opt.value} value={opt.value}>
                        {opt.label}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
                <Form.Item name="opportunity_id" noStyle>
                  <Select
                    style={{ width: 170 }}
                    placeholder="选择商机"
                    showSearch
                    optionFilterProp="children"
                    allowClear
                    disabled={!!opportunity_id}
                  >
                    {opportunityOptions.map((opt) => (
                      <Option key={opt.value} value={opt.value}>
                        {opt.label}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
                <Form.Item name="project_id" noStyle>
                  <Select
                    style={{ width: 170 }}
                    placeholder="选择项目"
                    showSearch
                    optionFilterProp="children"
                    allowClear
                    disabled={!!project_id}
                  >
                    {projectOptions.map((opt) => (
                      <Option key={opt.value} value={opt.value}>
                        {opt.label}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Space>
            </Form.Item>
          )}
        </Form>
        <Button type="primary" onClick={handleModalOk} loading={createMutation.isPending || updateMutation.isPending} block>
          保存
        </Button>
      </Drawer>

      <Drawer
        title={pageLabels.detailTitle}
        open={isViewModalVisible}
        onClose={() => setIsViewModalVisible(false)}
        width={560}
        maskClosable={false}
        destroyOnClose
      >
        {viewingFollowUp && (
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label={pageLabels.date}>
              {viewingFollowUp.follow_up_date || '无'}
            </Descriptions.Item>
            <Descriptions.Item label={pageLabels.method}>
              {viewingFollowUp.follow_up_method || '无'}
            </Descriptions.Item>
            {!isChannelMode && (
              <Descriptions.Item label="跟进结论">
                <Tag color={getConclusionColor(viewingFollowUp.follow_up_conclusion)}>
                  {viewingFollowUp.follow_up_conclusion || '无'}
                </Tag>
              </Descriptions.Item>
            )}
            <Descriptions.Item label={pageLabels.actor}>
              {viewingFollowUp.follower_name || `ID: ${viewingFollowUp.follower_id}`}
            </Descriptions.Item>
            <Descriptions.Item label={pageLabels.content} span={2}>
              {viewingFollowUp.follow_up_content || '无'}
            </Descriptions.Item>
            {isChannelMode ? (
              <>
                <Descriptions.Item label="关联渠道">
                  {viewingFollowUp.channel_name || '无'}
                </Descriptions.Item>
                <Descriptions.Item label="拜访目的">
                  {viewingFollowUp.visit_purpose || '无'}
                </Descriptions.Item>
                <Descriptions.Item label="拜访地点">
                  {viewingFollowUp.visit_location || '无'}
                </Descriptions.Item>
                <Descriptions.Item label="参与人员">
                  {viewingFollowUp.visit_attendees || '无'}
                </Descriptions.Item>
              </>
            ) : (
              <>
                <Descriptions.Item label="下次行动">{viewingFollowUp.next_action || '无'}</Descriptions.Item>
                <Descriptions.Item label="下次跟进日期">{viewingFollowUp.next_follow_up_date || '无'}</Descriptions.Item>
                <Descriptions.Item label="关联线索">{viewingFollowUp.lead_name || '无'}</Descriptions.Item>
                <Descriptions.Item label="关联商机">{viewingFollowUp.opportunity_name || '无'}</Descriptions.Item>
                <Descriptions.Item label="关联项目">{viewingFollowUp.project_name || '无'}</Descriptions.Item>
                <Descriptions.Item label={pageLabels.customer}>
                  {viewingFollowUp.terminal_customer_name || '无'}
                </Descriptions.Item>
              </>
            )}
          </Descriptions>
        )}
        <Button onClick={() => setIsViewModalVisible(false)} block style={{ marginTop: 16 }}>
          关闭
        </Button>
      </Drawer>
    </Card>
  );
};

export default FollowUpList;
