import React, { useState, useMemo, useEffect } from 'react';
import { App, Table, Button, Space, Modal, Form, Input, Select, DatePicker, Tag, InputNumber, Dropdown, Empty, Checkbox, Descriptions, Row, Col } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, MenuOutlined, SwapOutlined, FundOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useOpportunities, useCreateOpportunity, useUpdateOpportunity, useDeleteOpportunity, Opportunity as OpportunityType } from '../../hooks/useOpportunities';
import { useDictItems } from '../../hooks/useDictItems';
import { useCustomers } from '../../hooks/useCustomers';
import { useUsers } from '../../hooks/useUsers';
import { useChannels } from '../../hooks/useChannels';
import PageScaffold from '../../components/common/PageScaffold';
import PageModal from '../../components/common/PageModal';
import NineAModal from '../modals/NineAModal';

import { formatWan, fromWan, toWan } from '../../utils/currency';

const { Option } = Select;

const OpportunityList: React.FC = () => {
  const { message, modal } = App.useApp();
  const navigate = useNavigate();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingOpportunity, setEditingOpportunity] = useState<OpportunityType | null>(null);
  const [searchText, setSearchText] = useState('');
  const [stageFilter, setStageFilter] = useState<string | null>(null);
  const [ownerFilter, setOwnerFilter] = useState<number | null>(null);
  const [showOnlyMyOpportunities, setShowOnlyMyOpportunities] = useState(false);
  const [nineAModalVisible, setNineAModalVisible] = useState(false);
  const [selectedOpportunity, setSelectedOpportunity] = useState<OpportunityType | null>(null);
  const [form] = Form.useForm();

  const { data: opportunities = [], isLoading } = useOpportunities();
  const { data: stageItems = [] } = useDictItems('商机阶段');
  const { data: sourceItems = [] } = useDictItems('商机来源');
  const { data: productItems = [] } = useDictItems('产品品牌');
  const { data: customers = [] } = useCustomers();
  const { data: users = [] } = useUsers();
  const { data: channels = [] } = useChannels();

  const stageOptions = stageItems.map(item => ({ value: item.name, label: item.name }));
  const sourceOptions = sourceItems.map(item => ({ value: item.name, label: item.name }));
  const customerOptions = customers.map(c => ({ value: c.id, label: c.customer_name }));
  const userOptions = users.map(u => ({ value: u.id, label: u.name }));
  const channelOptions = channels.map(ch => ({ value: ch.id, label: ch.company_name }));

  const createMutation = useCreateOpportunity();
  const updateMutation = useUpdateOpportunity();
  const deleteMutation = useDeleteOpportunity();

  const filteredOpportunities = useMemo(() => opportunities.filter(opp => {
    const matchesSearch = !searchText ||
      opp.opportunity_name.toLowerCase().includes(searchText.toLowerCase()) ||
      opp.opportunity_code.toLowerCase().includes(searchText.toLowerCase());
    const matchesStage = !stageFilter || opp.opportunity_stage === stageFilter;
    const matchesOwner = !ownerFilter || opp.sales_owner_id === ownerFilter;
    // TODO: implement showOnlyMyOpportunities logic if needed
    return matchesSearch && matchesStage && matchesOwner;
  }), [opportunities, searchText, stageFilter, ownerFilter]);

  const getStageColor = (stage: string) => {
    const colors: Record<string, string> = {
      '需求方案': 'blue',
      '需求确认': 'cyan',
      '报价投标': 'gold',
      '合同签订': 'purple',
      '已成交': 'green',
      '已流失': 'red',
    };
    return colors[stage] || 'default';
  };

  const handleCreate = () => {
    setEditingOpportunity(null);
    form.resetFields();
    form.setFieldsValue({ opportunity_stage: '需求方案' });
    setIsModalVisible(true);
  };

  const handleEdit = (opportunity: OpportunityType) => {
    setEditingOpportunity(opportunity);
    form.setFieldsValue({
      ...opportunity,
      expected_contract_amount: toWan(opportunity.expected_contract_amount)
    });
    setIsModalVisible(true);
  };

  const handleView = (opportunity: OpportunityType) => {
    navigate(`/opportunities/${opportunity.id}/full`);
  };

  const handleDelete = (id: number) => {
    modal.confirm({
      title: '确定删除该商机吗？',
      content: '此操作不可恢复',
      okType: 'danger',
      onOk: async () => {
        try {
          await deleteMutation.mutateAsync(id);
          message.success('商机已删除');
        } catch (error) {}
      }
    });
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      const payload = {
        ...values,
        expected_contract_amount: fromWan(values.expected_contract_amount)
      };
      if (editingOpportunity) {
        await updateMutation.mutateAsync({ id: editingOpportunity.id, opportunity: payload });
        message.success('商机已更新');
      } else {
        await createMutation.mutateAsync(payload);
        message.success('商机已创建');
      }
      setIsModalVisible(false);
      form.resetFields();
    } catch (error: any) {}
  };

  const handleNineAClick = (opportunity: OpportunityType) => {
    setSelectedOpportunity(opportunity);
    setNineAModalVisible(true);
  };

  const handleConvertClick = (opportunity: OpportunityType) => {
    // TODO: Implement convert to project logic
    message.info('转换功能开发中');
  };

  return (
    <PageScaffold
      title="商机管理"
      breadcrumbItems={[{ title: '首页' }, { title: '商机管理' }]}
      extra={
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleCreate}
          size="large"
          className="btn--gradient"
          style={{ height: '40px', padding: '0 20px' }}
        >
          新建商机
        </Button>
      }
      filters={
        <Space size={16} wrap>
          <Input.Search
            placeholder="搜索商机名称/编号"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 280 }}
            size="middle"
            allowClear
          />
          <Select
            placeholder="当前阶段"
            value={stageFilter}
            onChange={setStageFilter}
            style={{ width: 150 }}
            allowClear
          >
            {stageOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>
                {opt.label}
              </Option>
            ))}
          </Select>
          <Select
            placeholder="负责人"
            value={ownerFilter}
            onChange={setOwnerFilter}
            style={{ width: 180 }}
            allowClear
          >
            {userOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>
                {opt.label}
              </Option>
            ))}
          </Select>
          <Checkbox
            checked={showOnlyMyOpportunities}
            onChange={(e) => setShowOnlyMyOpportunities(e.target.checked)}
            style={{ marginLeft: 8 }}
          >
            只看我负责
          </Checkbox>
        </Space>
      }
    >
      <Table
        columns={[
          {
            title: '编号',
            dataIndex: 'opportunity_code',
            key: 'opportunity_code',
            width: 160,
            fixed: 'left' as const,
          },
          {
            title: '商机名称',
            dataIndex: 'opportunity_name',
            key: 'opportunity_name',
            width: 220,
            fixed: 'left' as const,
          },
          {
            title: '终端客户',
            dataIndex: 'terminal_customer_name',
            key: 'terminal_customer_name',
            width: 180,
          },
          {
            title: '商机阶段',
            dataIndex: 'opportunity_stage',
            key: 'opportunity_stage',
            width: 120,
            render: (stage: string) => <Tag color={getStageColor(stage)} style={{ border: 'none' }}>{stage}</Tag>,
          },
          {
            title: '负责人',
            dataIndex: 'sales_owner_name',
            key: 'sales_owner_name',
            width: 100,
          },
          {
            title: '操作',
            key: 'action',
            width: 80,
            fixed: 'right' as const,
            render: (_: any, record: OpportunityType) => (
              <Dropdown
                menu={{
                  items: [
                    { key: 'view', label: '查看详情', icon: <EyeOutlined /> },
                    { key: 'edit', label: '编辑商机', icon: <EditOutlined /> },
                    record.opportunity_stage === '合同签订' && !record.project_id && { key: 'convert', label: '转项目', icon: <SwapOutlined /> },
                    !record.project_id && record.opportunity_stage !== '已成交' && { key: 'delete', label: '删除商机', icon: <DeleteOutlined />, danger: true },
                  ].filter(Boolean) as any[],
                  onClick: ({ key }) => {
                    if (key === 'view') handleView(record);
                    else if (key === 'edit') handleEdit(record);
                    else if (key === 'convert') handleConvertClick(record);
                    else if (key === 'delete') handleDelete(record.id);
                  },
                }}
                trigger={['click']}
              >
                <Button size="small" icon={<MenuOutlined />}>操作</Button>
              </Dropdown>
            ),
          },
        ]}
        dataSource={filteredOpportunities}
        loading={isLoading}
        rowKey="id"
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条数据`,
        }}
        scroll={{ x: 800 }}
        className="customer-table"
        bordered={false}
        expandable={{
          expandedRowRender: (record: OpportunityType) => (
            <div style={{ padding: '8px 24px' }}>
              <Descriptions column={4} size="small">
                <Descriptions.Item label="涉及产品">
                  {record.products && record.products.length > 0
                    ? record.products.map(p => <Tag key={p} color="blue" style={{ border: 'none' }}>{p}</Tag>)
                    : '-'}
                </Descriptions.Item>
                <Descriptions.Item label="协同渠道">
                  {record.channel_name || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="预计金额(万元)">
                  {formatWan(record.expected_contract_amount)}
                </Descriptions.Item>
                <Descriptions.Item label="关闭日期">
                  {record.expected_close_date || '-'}
                </Descriptions.Item>
              </Descriptions>
              <div style={{ marginTop: 12 }}>
                <Button
                  size="small"
                  icon={<FundOutlined />}
                  onClick={() => handleNineAClick(record)}
                >
                  9A管理
                </Button>
              </div>
            </div>
          ),
          rowExpandable: (record: OpportunityType) => true,
        }}
        locale={{ emptyText: <Empty description="暂无商机数据" image={Empty.PRESENTED_IMAGE_SIMPLE}>
          <Button type="primary" onClick={handleCreate}>+ 新增第一条商机</Button>
        </Empty> }}
      />

      <PageModal
        title={editingOpportunity ? '编辑商机详情' : '录入新商机'}
        open={isModalVisible}
        onClose={() => setIsModalVisible(false)}
        width={720}
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
            保存并提交
          </Button>
        ]}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="opportunity_name"
            label="商机名称"
            rules={[{ required: true, message: '请输入商机名称!' }]}
          >
            <Input placeholder="例如：某医院信息化系统建设项目" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="terminal_customer_id"
                label="终端客户"
                rules={[{ required: true, message: '请选择终端客户!' }]}
              >
                <Select placeholder="搜索终端客户" showSearch optionFilterProp="children">
                  {customerOptions.map(opt => (
                    <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="sales_owner_id"
                label="销售负责人"
                rules={[{ required: true, message: '请选择负责人!' }]}
              >
                <Select placeholder="选择内部负责人" showSearch optionFilterProp="children">
                  {userOptions.map(opt => (
                    <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="opportunity_stage"
                label="商机阶段"
                rules={[{ required: true, message: '请选择商机阶段!' }]}
              >
                <Select placeholder="选择当前阶段">
                  {stageOptions.map(opt => (
                    <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="opportunity_source" label="商机来源">
                <Select placeholder="选择来源" allowClear>
                  {sourceOptions.map(opt => (
                    <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="channel_id" label="协同渠道">
                <Select placeholder="选择协同渠道" allowClear showSearch optionFilterProp="label">
                  {channelOptions.map(opt => (
                    <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="expected_contract_amount" label="预计合同金额(万元)">
                <InputNumber style={{ width: '100%' }} placeholder="0.0" precision={1} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="products" label="涉及产品品牌">
            <Select mode="multiple" placeholder="选择产品品牌（可多选）" allowClear>
              {productItems.map(item => (
                <Option key={item.name} value={item.name}>{item.name}</Option>
              ))}
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="expected_close_date" label="预计关闭日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="loss_reason" label="流失原因">
                <Input placeholder="仅在流失阶段录入" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={3} placeholder="如有其他补充信息请录入..." />
          </Form.Item>
        </Form>
      </PageModal>

      <NineAModal
        visible={nineAModalVisible}
        onClose={() => setNineAModalVisible(false)}
        opportunityId={selectedOpportunity?.id || 0}
        opportunityName={selectedOpportunity?.opportunity_name || ''}
      />
    </PageScaffold>
  );
};

export default OpportunityList;
