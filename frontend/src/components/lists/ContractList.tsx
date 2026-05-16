import React, { useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select, DatePicker, Tag, InputNumber, App, Dropdown, Descriptions, Empty, Row, Col } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, MenuOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useContracts, useCreateContract, useUpdateContract, useDeleteContract } from '../../hooks/useContracts';
import PageScaffold from '../../components/common/PageScaffold';
import PageModal from '../../components/common/PageModal';

import { formatWan, fromWan, toWan } from '../../utils/currency';

const { Option } = Select;

const CONTRACT_DIRECTIONS = [
  { value: 'Downstream', label: '下游合同 (销售)' },
  { value: 'Upstream', label: '上游合同 (采购)' },
];

const ContractList: React.FC = () => {
  const { message, modal } = App.useApp();
  const navigate = useNavigate();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingContract, setEditingOpportunity] = useState<any>(null);
  const [searchText, setSearchText] = useState('');
  const [directionFilter, setDirectionFilter] = useState<string | null>(null);
  const [form] = Form.useForm();

  const { data: contracts = [], isLoading } = useContracts();
  const createMutation = useCreateContract();
  const updateMutation = useUpdateContract();
  const deleteMutation = useDeleteContract();

  const filteredContracts = contracts.filter(c => {
    const matchesSearch = !searchText ||
      c.contract_name.toLowerCase().includes(searchText.toLowerCase()) ||
      c.contract_code.toLowerCase().includes(searchText.toLowerCase());
    const matchesDirection = !directionFilter || c.contract_direction === directionFilter;
    return matchesSearch && matchesDirection;
  });

  const handleCreate = () => {
    setEditingOpportunity(null);
    form.resetFields();
    form.setFieldsValue({ contract_status: 'draft' });
    setIsModalOpen(true);
  };

  const handleEdit = (contract: any) => {
    setEditingOpportunity(contract);
    form.setFieldsValue({
      ...contract,
      contract_amount: toWan(contract.contract_amount)
    });
    setIsModalOpen(true);
  };

  const handleView = (contract: any) => {
    navigate(`/contracts/${contract.id}/full`);
  };

  const handleDelete = (id: number) => {
    modal.confirm({
      title: '确定删除该合同吗？',
      content: '此操作不可恢复',
      okType: 'danger',
      onOk: async () => {
        try {
          await deleteMutation.mutateAsync(id);
          message.success('合同已删除');
        } catch (error) {}
      }
    });
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      const payload = {
        ...values,
        contract_amount: fromWan(values.contract_amount)
      };
      if (editingContract) {
        await updateMutation.mutateAsync({ id: editingContract.id, contract: payload });
        message.success('合同信息已更新');
      } else {
        await createMutation.mutateAsync(payload);
        message.success('合同已创建');
      }
      setIsModalOpen(false);
      form.resetFields();
    } catch (error) {}
  };

  const baseColumns = [
    {
      title: '合同编号',
      dataIndex: 'contract_code',
      key: 'contract_code',
      width: 160,
    },
    {
      title: '合同名称',
      dataIndex: 'contract_name',
      key: 'contract_name',
      width: 220,
    },
    {
      title: '合同类型',
      dataIndex: 'contract_direction',
      key: 'contract_direction',
      width: 100,
      render: (dir: string) => (
        <Tag color={dir === 'Downstream' ? 'blue' : 'orange'} style={{ border: 'none' }}>
          {dir === 'Downstream' ? '下游合同' : '上游合同'}
        </Tag>
      ),
    },
    {
      title: '金额(万元)',
      dataIndex: 'contract_amount',
      key: 'contract_amount',
      width: 120,
      render: (v: number) => <span style={{ fontWeight: 600 }}>{formatWan(v)}</span>,
    },
    {
      title: '状态',
      dataIndex: 'contract_status',
      key: 'contract_status',
      width: 100,
      render: (status: string) => {
        const labels: Record<string, string> = { 'draft': '草稿', 'pending': '审批中', 'signed': '已签署', 'archived': '已归档' };
        return <Tag style={{ border: 'none' }}>{labels[status] || status}</Tag>;
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: any, record: any) => (
        <Dropdown
          menu={{
            items: [
              { key: 'view', label: '查看详情', icon: <EyeOutlined /> },
              { key: 'edit', label: '编辑合同', icon: <EditOutlined /> },
              { key: 'delete', label: '删除合同', icon: <DeleteOutlined />, danger: true },
            ],
            onClick: ({ key }) => {
              if (key === 'view') handleView(record);
              else if (key === 'edit') handleEdit(record);
              else if (key === 'delete') handleDelete(record.id);
            },
          }}
          trigger={['click']}
        >
          <Button size="small" icon={<MenuOutlined />}>操作</Button>
        </Dropdown>
      ),
    },
  ];

  const expandedRowRender = (record: any) => (
    <Descriptions column={3} size="small" style={{ padding: '8px 24px' }}>
      <Descriptions.Item label="签订日期">{record.signing_date || '-'}</Descriptions.Item>
      <Descriptions.Item label="生效日期">{record.effective_date || '-'}</Descriptions.Item>
      <Descriptions.Item label="到期日期">{record.expiry_date || '-'}</Descriptions.Item>
      <Descriptions.Item label="关联项目ID">{record.project_id || '-'}</Descriptions.Item>
      <Descriptions.Item label="备注" span={2}>{record.notes || '-'}</Descriptions.Item>
    </Descriptions>
  );

  return (
    <PageScaffold
      title="合同归档管理"
      breadcrumbItems={[{ title: '首页' }, { title: '合同归档管理' }]}
      extra={
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleCreate}
          size="large"
          className="btn--gradient"
          style={{ height: '40px', padding: '0 20px' }}
        >
          新建合同
        </Button>
      }
      filters={
        <Space size={16} wrap>
          <Input.Search
            placeholder="搜索合同名称或编号"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 280 }}
            size="middle"
          />
          <Select
            placeholder="筛选合同类型"
            value={directionFilter}
            onChange={setDirectionFilter}
            style={{ width: 180 }}
            allowClear
          >
            {CONTRACT_DIRECTIONS.map(opt => (
              <Option key={opt.value} value={opt.value}>{opt.label}</Option>
            ))}
          </Select>
        </Space>
      }
    >
      <Table
        columns={baseColumns}
        dataSource={filteredContracts}
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
          expandedRowRender,
          rowExpandable: () => true,
        }}
        locale={{ emptyText: <Empty description="暂无合同数据" image={Empty.PRESENTED_IMAGE_SIMPLE}>
          <Button type="primary" onClick={handleCreate}>+ 新增第一条合同</Button>
        </Empty> }}
      />

      <PageModal
        title={editingContract ? '编辑合同详情' : '录入新合同'}
        open={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        width={720}
        footer={[
          <Button key="cancel" onClick={() => setIsModalOpen(false)}>
            取消
          </Button>,
          <Button
            key="submit"
            type="primary"
            className="btn--gradient"
            onClick={handleSave}
            loading={createMutation.isPending || updateMutation.isPending}
          >
            保存并归档
          </Button>
        ]}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="contract_name"
            label="合同名称"
            rules={[{ required: true, message: '请输入合同名称!' }]}
          >
            <Input placeholder="例如：某项目设备采购合同" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="contract_direction"
                label="合同方向"
                rules={[{ required: true, message: '请选择合同方向!' }]}
              >
                <Select placeholder="选择类型">
                  {CONTRACT_DIRECTIONS.map(opt => (
                    <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="contract_amount"
                label="合同金额(万元)"
                rules={[{ required: true, message: '请输入合同总金额!' }]}
              >
                <InputNumber style={{ width: '100%' }} placeholder="0.0" precision={1} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="signing_date" label="签订日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="effective_date" label="生效日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="expiry_date" label="到期日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="contract_status" label="合同状态">
                <Select placeholder="选择状态">
                  <Option value="draft">草稿</Option>
                  <Option value="pending">审批中</Option>
                  <Option value="signed">已签署</Option>
                  <Option value="archived">已归档</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="notes" label="补充备注">
            <Input.TextArea rows={3} placeholder="输入合同相关的其他补充条款或说明..." />
          </Form.Item>
        </Form>
      </PageModal>
    </PageScaffold>
  );
};

export default ContractList;
