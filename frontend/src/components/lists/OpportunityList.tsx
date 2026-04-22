import React, { useState, useMemo, useEffect } from 'react';
import { App, Table, Button, Space, Modal, Form, Input, Select, DatePicker, Tag, InputNumber, Dropdown, Empty, Checkbox, Descriptions, Drawer } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SwapOutlined, EyeOutlined, FundOutlined, MenuOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { useOpportunities, useCreateOpportunity, useUpdateOpportunity, useDeleteOpportunity, Opportunity as OpportunityType } from '../../hooks/useOpportunities';
import { useDictItems } from '../../hooks/useDictItems';
import { useCustomers } from '../../hooks/useCustomers';
import { useUsers } from '../../hooks/useUsers';
import { useChannels } from '../../hooks/useChannels';
import { useNineA, useCreateNineA, useUpdateNineA, NineA } from '../../hooks/useNineA';
import { useAuth } from '../../hooks/useAuth';
import PageScaffold from '../../components/common/PageScaffold';

const { Option } = Select;
const { Search } = Input;
const { TextArea } = Input;

const OPPORTUNITY_STAGE_TRANSITIONS: Record<string, string[]> = {
  "需求方案": ["需求确认", "已流失"],
  "需求确认": ["报价投标", "需求方案", "已流失"],
  "报价投标": ["合同签订", "需求确认", "已流失"],
  "合同签订": ["已成交"],
  "已成交": [],
  "已流失": [],
};

const BUSINESS_TYPES = [
  { value: 'New Project', label: '新项目' },
  { value: 'Renewal/Maintenance', label: '续费项目-SVC' },
  { value: 'Expansion', label: '增购项目' },
  { value: 'Additional Purchase', label: '其他' },
];

const OpportunityList: React.FC = () => {
  const navigate = useNavigate();
  const { message, modal } = App.useApp();
  const { user } = useAuth();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isConvertModalVisible, setIsConvertModalVisible] = useState(false);
  const [isNineAModalVisible, setIsNineAModalVisible] = useState(false);
  const [editingOpportunity, setEditingOpportunity] = useState<OpportunityType | null>(null);
  const [convertingOpportunity, setConvertingOpportunity] = useState<OpportunityType | null>(null);
  const [nineAOpportunity, setNineAOpportunity] = useState<OpportunityType | null>(null);
  const [searchText, setSearchText] = useState('');
  const [stageFilter, setStageFilter] = useState<string | null>(null);
  const [ownerFilter, setOwnerFilter] = useState<number | null>(null);
  const [showOnlyMyOpportunities, setShowOnlyMyOpportunities] = useState(false);
  const [form] = Form.useForm();
  const [convertForm] = Form.useForm();
  const [nineAForm] = Form.useForm();

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

  const currentStage = Form.useWatch('opportunity_stage', form);
  const validNextStages = useMemo(() => {
    if (!editingOpportunity || !currentStage) return stageOptions;
    return stageOptions.filter(opt =>
      OPPORTUNITY_STAGE_TRANSITIONS[editingOpportunity.opportunity_stage]?.includes(opt.value) ||
      opt.value === editingOpportunity.opportunity_stage
    );
  }, [editingOpportunity, currentStage, stageOptions]);

  const showLossReason = currentStage === '已流失';

  const filteredOpportunities = useMemo(() => opportunities.filter(opportunity => {
    const matchesSearch = !searchText ||
      opportunity.opportunity_name?.toLowerCase().includes(searchText.toLowerCase()) ||
      opportunity.opportunity_code?.toLowerCase().includes(searchText.toLowerCase());
    const matchesStage = !stageFilter || opportunity.opportunity_stage === stageFilter;
    const matchesOwner = !ownerFilter || opportunity.sales_owner_id === ownerFilter;
    const matchesMyOpportunities = !showOnlyMyOpportunities || opportunity.sales_owner_id === user?.id;
    return matchesSearch && matchesStage && matchesOwner && matchesMyOpportunities;
  }), [opportunities, searchText, stageFilter, ownerFilter, showOnlyMyOpportunities, user?.id]);

  const createMutation = useCreateOpportunity();
  const updateMutation = useUpdateOpportunity();
  const deleteMutation = useDeleteOpportunity();

  const getStageColor = (stage: string) => {
    switch (stage) {
      case '需求方案': return 'blue';
      case '需求确认': return 'cyan';
      case '报价投标': return 'gold';
      case '合同签订': return 'purple';
      case '已成交': return 'green';
      case '已流失': return 'red';
      default: return 'default';
    }
  };

  const handleCreate = () => {
    setEditingOpportunity(null);
    form.resetFields();
    form.setFieldsValue({ opportunity_stage: '需求方案', lead_grade: 'B' });
    setIsModalVisible(true);
  };

  const handleEdit = (opportunity: OpportunityType) => {
    if (opportunity.opportunity_stage === '已成交' || opportunity.opportunity_stage === '已流失') {
      message.warning('已成交或已流失的商机不能修改');
      return;
    }
    setEditingOpportunity(opportunity);
    form.setFieldsValue({
      ...opportunity,
      expected_close_date: opportunity.expected_close_date ? opportunity.expected_close_date : undefined,
    });
    setIsModalVisible(true);
  };

  const handleView = (opportunity: OpportunityType) => {
    navigate(`/opportunities/${opportunity.id}/full`);
  };

  const handleDelete = (opportunityId: number) => {
    modal.confirm({
      title: '确定删除该商机吗？',
      content: '此操作不可恢复',
      onOk: async () => {
        try {
          await deleteMutation.mutateAsync(opportunityId);
          message.success('商机删除成功');
        } catch (error) {
        }
      }
    });
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      const payload = {
        ...values,
        expected_close_date: values.expected_close_date?.format?.('YYYY-MM-DD') || values.expected_close_date,
      };

      if (editingOpportunity) {
        await updateMutation.mutateAsync({ id: editingOpportunity.id, opportunity: payload });
      } else {
        await createMutation.mutateAsync(payload);
      }

      setIsModalVisible(false);
      form.resetFields();
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  const handleConvertClick = (opportunity: OpportunityType) => {
    if (opportunity.project_id) {
      message.info('该商机已转换为项目');
      return;
    }
    if (opportunity.opportunity_stage !== '合同签订') {
      message.warning('商机需在合同签订阶段才能转项目');
      return;
    }
    setConvertingOpportunity(opportunity);
    convertForm.resetFields();
    convertForm.setFieldsValue({
      project_name: opportunity.opportunity_name,
      business_type: 'New Project'
    });
    setIsConvertModalVisible(true);
  };

  const handleConvertOk = async () => {
    if (!convertingOpportunity) return;

    try {
      const values = await convertForm.validateFields();
      await api.post(`/opportunities/${convertingOpportunity.id}/convert`, values);
      message.success('商机已成功转换为项目');
      setIsConvertModalVisible(false);
      convertForm.resetFields();
      setConvertingOpportunity(null);
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  const handleNineAClick = (opportunity: OpportunityType) => {
    setNineAOpportunity(opportunity);
    setIsNineAModalVisible(true);
  };

  return (
    <PageScaffold
      title="商机管理"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建商机
        </Button>
      }
      filters={
        <Space>
          <Search
            placeholder="搜索商机名称/编号"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 200 }}
            allowClear
          />
          <Select
            placeholder="阶段"
            value={stageFilter}
            onChange={setStageFilter}
            style={{ width: 120 }}
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
            style={{ width: 120 }}
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
            title: '名称',
            dataIndex: 'opportunity_name',
            key: 'opportunity_name',
            width: 220,
            fixed: 'left' as const,
          },
          {
            title: '客户',
            dataIndex: 'terminal_customer_name',
            key: 'terminal_customer_name',
            width: 180,
          },
          {
            title: '阶段',
            dataIndex: 'opportunity_stage',
            key: 'opportunity_stage',
            width: 100,
            render: (stage: string) => <Tag color={getStageColor(stage)}>{stage}</Tag>,
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
                    { key: 'view', label: '查看', icon: <EyeOutlined /> },
                    { key: 'edit', label: '编辑', icon: <EditOutlined /> },
                    record.opportunity_stage === '合同签订' && !record.project_id && { key: 'convert', label: '转项目', icon: <SwapOutlined /> },
                    !record.project_id && record.opportunity_stage !== '已成交' && { key: 'delete', label: '删除', icon: <DeleteOutlined />, danger: true },
                  ].filter(Boolean),
                  onClick: ({ key }) => {
                    if (key === 'view') handleView(record);
                    else if (key === 'edit') handleEdit(record);
                    else if (key === 'convert') handleConvertClick(record);
                    else if (key === 'delete') handleDelete(record.id);
                  },
                }}
                trigger={['click']}
              >
                <Button size="small" icon={<MenuOutlined />} />
              </Dropdown>
            ),
          },
        ]}
        dataSource={filteredOpportunities}
        loading={isLoading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        scroll={{ x: 800 }}
        expandable={{
          expandedRowRender: (record: OpportunityType) => (
            <div style={{ padding: '16px' }}>
              <Descriptions column={4} size="small">
                <Descriptions.Item label="产品">
                  {record.products && record.products.length > 0
                    ? record.products.map(p => <Tag key={p} color="blue">{p}</Tag>)
                    : '-'}
                </Descriptions.Item>
                <Descriptions.Item label="渠道">
                  {record.channel_name || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="预计金额">
                  {record.expected_contract_amount?.toLocaleString() || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="关闭日期">
                  {record.expected_close_date || '-'}
                </Descriptions.Item>
              </Descriptions>
              <div style={{ marginTop: 8 }}>
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
          <Button type="primary" onClick={handleCreate}>+ 新建第一条商机</Button>
        </Empty> }}
      />

      <Drawer
        title={editingOpportunity ? '编辑商机' : '新建商机'}
        open={isModalVisible}
        onClose={() => setIsModalVisible(false)}
        width={520}
        maskClosable={false}
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ flex: 1, overflow: 'auto' }}>
          <Form.Item
            name="opportunity_name"
            label="商机名称"
            rules={[{ required: true, message: '请输入商机名称!' }]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            name="terminal_customer_id"
            label="终端客户"
            rules={[{ required: true, message: '请选择终端客户!' }]}
          >
            <Select placeholder="请选择终端客户" showSearch optionFilterProp="children">
              {customerOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="sales_owner_id"
            label="销售负责人"
            rules={[{ required: true, message: '请选择销售负责人!' }]}
          >
            <Select placeholder="请选择销售负责人" showSearch optionFilterProp="children">
              {userOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="opportunity_stage"
            label="商机阶段"
            rules={[{ required: true, message: '请选择商机阶段!' }]}
          >
            <Select placeholder="请选择商机阶段">
              {validNextStages.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>

          {showLossReason && (
            <Form.Item
              name="loss_reason"
              label="流失原因"
              rules={[{ required: true, message: '请输入流失原因!' }]}
            >
              <Input.TextArea rows={2} placeholder="请输入流失原因" />
            </Form.Item>
          )}

          <Form.Item
            name="opportunity_source"
            label="商机来源"
            rules={[{ required: true, message: '请选择商机来源!' }]}
          >
            <Select placeholder="请选择商机来源">
              {sourceOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="products" label="产品">
            <Select mode="multiple" placeholder="请选择产品（可多选）" allowClear>
              {productItems.map(item => (
                <Option key={item.name} value={item.name}>{item.name}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="expected_contract_amount"
            label="预计合同金额"
            rules={[{ required: true, message: '请输入预计合同金额!' }]}
          >
            <Input type="number" />
          </Form.Item>

          <Form.Item name="expected_close_date" label="预计关闭日期">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="channel_id" label="关联渠道">
            <Select placeholder="请选择渠道 (可选)" showSearch optionFilterProp="children" allowClear>
              {channelOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item>
            <Button type="primary" onClick={handleModalOk} loading={createMutation.isPending || updateMutation.isPending} block>
              保存
            </Button>
          </Form.Item>
        </Form>
      </Drawer>

      <Drawer
        title="商机转项目"
        open={isConvertModalVisible}
        onClose={() => setIsConvertModalVisible(false)}
        width={480}
        maskClosable={false}
        destroyOnClose
      >
        <Form form={convertForm} layout="vertical" style={{ flex: 1, overflow: 'auto' }}>
          <Form.Item
            name="project_name"
            label="项目名称"
            rules={[{ required: true, message: '请输入项目名称!' }]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            name="business_type"
            label="业务类型"
            rules={[{ required: true, message: '请选择业务类型!' }]}
          >
            <Select>
              {BUSINESS_TYPES.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item>
            <Button type="primary" onClick={handleConvertOk} block>
              确认转换
            </Button>
          </Form.Item>
        </Form>
      </Drawer>

      <NineAModal
        visible={isNineAModalVisible}
        opportunity={nineAOpportunity}
        onClose={() => {
          setIsNineAModalVisible(false);
          setNineAOpportunity(null);
        }}
      />
    </PageScaffold>
  );
};

const NineAModal: React.FC<{
  visible: boolean;
  opportunity: OpportunityType | null;
  onClose: () => void;
}> = ({ visible, opportunity, onClose }) => {
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const { data: nineA, isLoading } = useNineA(opportunity?.id || 0);
  const createMutation = useCreateNineA(opportunity?.id || 0);
  const updateMutation = useUpdateNineA(opportunity?.id || 0);

  useEffect(() => {
    if (nineA) {
      form.setFieldsValue(nineA);
    } else if (opportunity) {
      form.setFieldsValue({
        budget: opportunity.expected_contract_amount,
      });
    }
  }, [nineA, opportunity, form]);

  const handleSave = async () => {
    if (!opportunity) return;

    try {
      const values = await form.validateFields();
      if (nineA) {
        await updateMutation.mutateAsync(values);
        message.success('9A分析更新成功');
      } else {
        await createMutation.mutateAsync(values);
        message.success('9A分析创建成功');
      }
      onClose();
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  return (
    <Drawer
      title={`9A 管理 - ${opportunity?.opportunity_name || ''}`}
      open={visible}
      onClose={onClose}
      width={600}
      maskClosable={false}
      destroyOnClose
    >
      {isLoading ? (
        <div style={{ textAlign: 'center', padding: 40 }}>加载中...</div>
      ) : (
        <Form form={form} layout="vertical" style={{ flex: 1, overflow: 'auto' }}>
          <Form.Item name="key_events" label="关键事件">
            <TextArea rows={3} placeholder="记录关键事件和时间节点" />
          </Form.Item>

          <Form.Item name="budget" label="预算">
            <InputNumber
              style={{ width: '100%' }}
              placeholder="预算金额（同步自商机预计金额）"
              min={0}
              formatter={value => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={value => value!.replace(/\¥\s?|(,*)/g, '') as any}
            />
          </Form.Item>

          <Form.Item name="close_date" label="关单时间">
            <DatePicker style={{ width: '100%' }} placeholder="选择预计关单日期" />
          </Form.Item>

          <Form.Item name="decision_chain_influence" label="决策链影响度">
            <TextArea rows={3} placeholder="分析决策链条中各角色的影响力" />
          </Form.Item>

          <Form.Item name="customer_challenges" label="客户的挑战和痛点">
            <TextArea rows={3} placeholder="记录客户面临的主要挑战和痛点" />
          </Form.Item>

          <Form.Item name="customer_needs" label="客户需求和价值诉求">
            <TextArea rows={3} placeholder="分析客户的真实需求和价值诉求" />
          </Form.Item>

          <Form.Item name="solution_differentiation" label="解决方案和差异化因素">
            <TextArea rows={3} placeholder="我们的解决方案及与竞争对手的差异化" />
          </Form.Item>

          <Form.Item name="competitors" label="竞争者">
            <TextArea rows={3} placeholder="竞争对手分析" />
          </Form.Item>

          <Form.Item name="buying_method" label="购买方式">
            <TextArea rows={2} placeholder="客户的购买流程和方式" />
          </Form.Item>
          
          <Form.Item>
            <Button type="primary" onClick={handleSave} loading={createMutation.isPending || updateMutation.isPending} block>
              保存
            </Button>
          </Form.Item>
        </Form>
      )}
    </Drawer>
  );
};

export default OpportunityList;
