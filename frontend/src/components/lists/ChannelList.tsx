import React, { useEffect, useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select, Tag, Cascader, App, Dropdown, Descriptions, Empty, Row, Col, InputNumber } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, MenuOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useChannels, useCreateChannel, useUpdateChannel, useDeleteChannel } from '../../hooks/useChannels';
import { useDictItems, useRegionCascader } from '../../hooks/useDictItems';
import { useSelector } from 'react-redux';
import { RootState } from '../../store/store';
import PageScaffold from '../../components/common/PageScaffold';
import PageModal from '../../components/common/PageModal';
import { formatWan } from '../../utils/currency';

const { Option } = Select;

const ChannelList: React.FC = () => {
  const { message, modal } = App.useApp();
  const navigate = useNavigate();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingChannel, setEditingChannel] = useState<any>(null);
  const [searchText, setSearchText] = useState('');
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [provinceFilter, setProvinceFilter] = useState<string | null>(null);
  const [form] = Form.useForm();

  const { data: channels = [], isLoading } = useChannels();
  const { data: typeItems = [] } = useDictItems('渠道类型');
  const { data: statusItems = [] } = useDictItems('渠道状态');
  const { data: regionCascaderData = [] } = useRegionCascader();
  const provinceOptions = regionCascaderData.map(p => p.label);

  const typeOptions = typeItems.map(item => ({ value: item.name, label: item.name }));
  const statusOptions = statusItems.map(item => ({ value: item.name, label: item.name }));

  const { capabilities } = useSelector((state: RootState) => state.auth);
  const canCreateChannel = Boolean(capabilities['channel:create']);

  const createMutation = useCreateChannel();
  const updateMutation = useUpdateChannel();
  const deleteMutation = useDeleteChannel();

  const filteredChannels = channels.filter(c => {
    const matchesSearch = !searchText ||
      c.company_name.toLowerCase().includes(searchText.toLowerCase()) ||
      c.channel_code.toLowerCase().includes(searchText.toLowerCase());
    const matchesType = !typeFilter || c.channel_type === typeFilter;
    const matchesStatus = !statusFilter || c.status === statusFilter;
    const matchesProvince = !provinceFilter || c.province === provinceFilter;
    return matchesSearch && matchesType && matchesStatus && matchesProvince;
  });

  const handleCreate = () => {
    setEditingChannel(null);
    form.resetFields();
    form.setFieldsValue({ status: '活跃' });
    setIsModalOpen(true);
  };

  const handleEdit = (channel: any, e?: React.MouseEvent) => {
    e?.stopPropagation();
    setEditingChannel(channel);
    form.setFieldsValue(channel);
    setIsModalOpen(true);
  };

  const handleDelete = (channelId: number, e?: React.MouseEvent) => {
    e?.stopPropagation();
    modal.confirm({
      title: '确定删除该渠道吗？',
      content: '此操作不可恢复',
      okType: 'danger',
      onOk: async () => {
        try {
          await deleteMutation.mutateAsync(channelId);
          message.success('渠道已删除');
        } catch (error) {}
      }
    });
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      if (editingChannel) {
        await updateMutation.mutateAsync({ id: editingChannel.id, channel: values });
        message.success('渠道信息已更新');
      } else {
        await createMutation.mutateAsync(values);
        message.success('渠道已创建');
      }
      setIsModalOpen(false);
      form.resetFields();
    } catch (error) {}
  };

  const baseColumns = [
    {
      title: '渠道编号',
      dataIndex: 'channel_code',
      key: 'channel_code',
      width: 140,
    },
    {
      title: '公司名称',
      dataIndex: 'company_name',
      key: 'company_name',
      width: 220,
    },
    {
      title: '渠道类型',
      dataIndex: 'channel_type',
      key: 'channel_type',
      width: 120,
      render: (type: string) => <Tag color="blue" style={{ border: 'none' }}>{type}</Tag>,
    },
    {
      title: '所在区域',
      key: 'region',
      width: 150,
      render: (_: any, record: any) => `${record.province || ''} ${record.city || ''}`.trim() || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => <Tag color={status === '活跃' ? 'success' : 'default'} style={{ border: 'none' }}>{status}</Tag>,
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
              { key: 'edit', label: '编辑渠道', icon: <EditOutlined /> },
              { key: 'delete', label: '删除渠道', icon: <DeleteOutlined />, danger: true },
            ],
            onClick: ({ key, domEvent }) => {
              domEvent.stopPropagation();
              if (key === 'view') navigate(`/channels/${record.id}/full`);
              else if (key === 'edit') handleEdit(record);
              else if (key === 'delete') handleDelete(record.id);
            },
          }}
          trigger={['click']}
        >
          <Button size="small" icon={<MenuOutlined />} onClick={e => e.stopPropagation()}>操作</Button>
        </Dropdown>
      ),
    },
  ];

  const expandedRowRender = (record: any) => (
    <Descriptions column={3} size="small" style={{ padding: '8px 24px' }}>
      <Descriptions.Item label="主要联系人">{record.main_contact || '-'}</Descriptions.Item>
      <Descriptions.Item label="联系电话">{record.phone || '-'}</Descriptions.Item>
      <Descriptions.Item label="联系邮箱">{record.email || '-'}</Descriptions.Item>
      <Descriptions.Item label="协同客户数">{record.customers_count || 0}</Descriptions.Item>
      <Descriptions.Item label="商机总额(万元)">{formatWan(record.opportunities_amount)}</Descriptions.Item>
      <Descriptions.Item label="折扣率">{record.discount_rate ? `${(record.discount_rate * 100).toFixed(2)}%` : '-'}</Descriptions.Item>
    </Descriptions>
  );

  return (
    <PageScaffold
      title="渠道档案"
      breadcrumbItems={[{ title: '首页' }, { title: '渠道档案' }]}
      extra={
        canCreateChannel ? (
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreate}
            size="large"
            className="btn--gradient"
            style={{ height: '40px', padding: '0 20px' }}
          >
            新建渠道
          </Button>
        ) : null
      }
      filters={
        <Space size={16} wrap>
          <Input.Search
            placeholder="搜索公司名称或编号"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 280 }}
            size="middle"
          />
          <Select
            placeholder="渠道类型"
            value={typeFilter}
            onChange={setTypeFilter}
            style={{ width: 150 }}
            allowClear
          >
            {typeOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>{opt.label}</Option>
            ))}
          </Select>
          <Select
            placeholder="合作状态"
            value={statusFilter}
            onChange={setStatusFilter}
            style={{ width: 120 }}
            allowClear
          >
            {statusOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>{opt.label}</Option>
            ))}
          </Select>
          <Select
            placeholder="省份筛选"
            value={provinceFilter}
            onChange={setProvinceFilter}
            style={{ width: 140 }}
            allowClear
          >
            {provinceOptions.map(province => (
              <Option key={province} value={province}>{province}</Option>
            ))}
          </Select>
        </Space>
      }
    >
      <Table
        columns={baseColumns}
        dataSource={filteredChannels}
        loading={isLoading}
        rowKey="id"
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条数据`,
        }}
        scroll={{ x: 750 }}
        className="customer-table"
        bordered={false}
        onRow={(record) => ({
          onClick: () => navigate(`/channels/${record.id}/full`),
          style: { cursor: 'pointer' },
        })}
        expandable={{
          expandedRowRender,
          rowExpandable: () => true,
        }}
      />

      <PageModal
        title={editingChannel ? '编辑渠道详情' : '录入新渠道资料'}
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
            保存并同步
          </Button>
        ]}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="company_name"
            label="公司全称"
            rules={[{ required: true, message: '请输入公司名称!' }]}
          >
            <Input placeholder="请录入公司完整名称" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="channel_type"
                label="渠道类型"
                rules={[{ required: true, message: '请选择渠道类型!' }]}
              >
                <Select placeholder="选择类型">
                  {typeOptions.map(opt => (
                    <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="status"
                label="状态"
                rules={[{ required: true, message: '请选择状态!' }]}
              >
                <Select placeholder="请选择当前状态">
                  {statusOptions.map(opt => (
                    <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="credit_code" label="统一社会信用代码">
                <Input placeholder="18位信用代码" maxLength={18} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="discount_rate" label="合作折扣率">
                <InputNumber
                  style={{ width: '100%' }}
                  placeholder="0.00"
                  min={0}
                  max={1}
                  step={0.01}
                  formatter={value => `${(Number(value) * 100).toFixed(0)}%`}
                  parser={value => (Number(value!.replace('%', '')) / 100) as any}
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="province" label="省份">
                <Select placeholder="选择省份" showSearch allowClear>
                  {provinceOptions.map(p => <Option key={p} value={p}>{p}</Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="city" label="城市">
                <Input placeholder="输入城市名称" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="address" label="详细地址">
            <Input placeholder="街道、门牌号等" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="main_contact" label="主要联系人">
                <Input placeholder="姓名" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="phone" label="联系电话">
                <Input placeholder="手机或座机" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="website" label="官网地址">
            <Input placeholder="https://..." />
          </Form.Item>

          <Form.Item name="notes" label="合作备注">
            <Input.TextArea rows={3} placeholder="如有其他补充信息请录入..." />
          </Form.Item>
        </Form>
      </PageModal>
    </PageScaffold>
  );
};

export default ChannelList;
