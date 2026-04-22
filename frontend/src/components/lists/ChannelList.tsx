import React, { useEffect, useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select, Tag, Cascader, App, Dropdown, Descriptions, Empty } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, MenuOutlined, ShopOutlined, BankOutlined, EnvironmentOutlined, GlobalOutlined, TeamOutlined } from '@ant-design/icons';
import { useLocation, useNavigate } from 'react-router-dom';
import { useChannels, useCreateChannel, useUpdateChannel, useDeleteChannel, Channel, ChannelCreate } from '../../hooks/useChannels';
import { useDictItems, useRegionCascader } from '../../hooks/useDictItems';
import api from '../../services/api';
import PageScaffold from '../../components/common/PageScaffold';
import PageDrawer from '../../components/common/PageDrawer';
import { useSelector } from 'react-redux';
import { RootState } from '../../store/store';

const { Option } = Select;
const { Search } = Input;

const checkChannelCreditCodeExists = async (creditCode: string, excludeId?: number): Promise<boolean> => {
  try {
    const params = new URLSearchParams({ credit_code: creditCode });
    if (excludeId) params.append('exclude_id', String(excludeId));
    const response = await api.get(`/channels/check-credit-code?${params.toString()}`);
    return response.data.exists;
  } catch (error) {
    return false;
  }
};

const ChannelList: React.FC = () => {
  const { message, modal } = App.useApp();
  const navigate = useNavigate();
  const location = useLocation();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [editingChannel, setEditingChannel] = useState<Channel | null>(null);
  const [searchText, setSearchText] = useState('');
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [provinceFilter, setProvinceFilter] = useState<string | null>(null);
  const [form] = Form.useForm();
  const { capabilities } = useSelector((state: RootState) => state.auth);

  const { data: channels = [], isLoading } = useChannels();
  const { data: typeItems = [] } = useDictItems('渠道类型');
  const { data: statusItems = [] } = useDictItems('渠道状态');
  const { data: regionOptions = [] } = useRegionCascader();

  const typeOptions = typeItems.map(item => ({ value: item.name, label: item.name }));
  const statusOptions = statusItems.map(item => ({ value: item.name, label: item.name }));

  const provinceOptions = Array.from(
    new Set(channels.map(channel => channel.province).filter(Boolean))
  ) as string[];

  const filteredChannels = channels.filter(channel => {
    const matchesSearch = !searchText ||
      channel.company_name?.toLowerCase().includes(searchText.toLowerCase()) ||
      channel.channel_code?.toLowerCase().includes(searchText.toLowerCase());
    const matchesType = !typeFilter || channel.channel_type === typeFilter;
    const matchesStatus = !statusFilter || channel.status === statusFilter;
    const matchesProvince = !provinceFilter || channel.province === provinceFilter;
    return matchesSearch && matchesType && matchesStatus && matchesProvince;
  });

  const getStatusColor = (status: string) => {
    const colorMap: Record<string, string> = {
      '合作中': 'green',
      '暂停合作': 'orange',
      '终止合作': 'red',
      '待审核': 'blue',
    };
    return colorMap[status] || 'default';
  };

  const createMutation = useCreateChannel();
  const updateMutation = useUpdateChannel();
  const deleteMutation = useDeleteChannel();
  const isCreateRoute = location.pathname === '/channels/new';
  const canCreateChannel = Boolean(capabilities['channel:create']);

  useEffect(() => {
    if (isCreateRoute && !canCreateChannel) {
      navigate('/channels', { replace: true });
      message.warning('当前账号没有创建渠道权限');
      return;
    }

    if (isCreateRoute) {
      setEditingChannel(null);
      form.resetFields();
      setIsDrawerOpen(true);
    } else if (!editingChannel) {
      setIsDrawerOpen(false);
    }
  }, [isCreateRoute, editingChannel, form, canCreateChannel, navigate]);

  const handleCreate = () => {
    if (!canCreateChannel) {
      message.warning('当前账号没有创建渠道权限');
      return;
    }
    setEditingChannel(null);
    form.resetFields();
    setIsDrawerOpen(true);
    navigate('/channels/new');
  };

  const handleEdit = (channel: Channel) => {
    if (!channel.can_edit) {
      message.warning('当前账号没有编辑该渠道的权限');
      return;
    }
    setEditingChannel(channel);
    const regionArray = channel.province && channel.city ? [channel.province, channel.city] : [];
    form.setFieldsValue({
      ...channel,
      region: regionArray.length > 0 ? regionArray : undefined,
    });
    setIsDrawerOpen(true);
  };

  const handleView = (channel: Channel) => {
    navigate(`/channels/${channel.id}/full`);
  };

  const handleViewFollowUps = (channel: Channel) => {
    navigate(`/channel-follow-ups?channel_id=${channel.id}`);
  };

  const handleDelete = async (id: number) => {
    const channel = channels.find(item => item.id === id);
    if (!channel?.can_delete) {
      message.warning('当前账号没有删除该渠道的权限');
      return;
    }
    modal.confirm({
      title: '确认删除',
      content: '确定要删除该渠道吗？此操作不可恢复。',
      okText: '删除',
      cancelText: '取消',
      onOk: async () => {
        try {
          await deleteMutation.mutateAsync(id);
          message.success('删除成功');
        } catch (error: any) {
          message.error(error?.response?.data?.detail || '删除失败');
        }
      },
    });
  };

  const handleDrawerOk = async () => {
    try {
      const values = await form.validateFields();
      const payload: ChannelCreate = {
        ...values,
        province: values.region?.[0] || null,
        city: values.region?.[1] || null,
        cooperation_products: values.cooperation_products?.join(','),
      };
      delete (payload as any).region;

      if (editingChannel) {
        await updateMutation.mutateAsync({ id: editingChannel.id, channel: payload });
        message.success('更新成功');
      } else {
        await createMutation.mutateAsync(payload);
        message.success('创建成功');
        navigate('/channels');
      }

      setIsDrawerOpen(false);
      form.resetFields();
      setEditingChannel(null);
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  const baseColumns = [
    {
      title: '渠道编号',
      dataIndex: 'channel_code',
      key: 'channel_code',
      width: 150,
    },
    {
      title: '公司名称',
      dataIndex: 'company_name',
      key: 'company_name',
      width: 200,
    },
    {
      title: '渠道类型',
      dataIndex: 'channel_type',
      key: 'channel_type',
      width: 100,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => <Tag color={getStatusColor(status)}>{status}</Tag>,
    },
    {
      title: '联系人',
      dataIndex: 'main_contact',
      key: 'main_contact',
      width: 100,
    },
    {
      title: '电话',
      dataIndex: 'phone',
      key: 'phone',
      width: 140,
      render: (value: string) => value || '-',
    },
    {
      title: '省市',
      key: 'region',
      width: 160,
      render: (_: any, record: Channel) =>
        record.province || record.city ? `${record.province || ''} ${record.city || ''}`.trim() : '-',
    },
    {
      title: '合作区域',
      dataIndex: 'cooperation_region',
      key: 'cooperation_region',
      width: 180,
      render: (value: string) => value || '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: any, record: Channel) => (
        <div onClick={(event) => event.stopPropagation()}>
          <Dropdown
            menu={{
              items: [
                { key: 'view', label: '查看', icon: <EyeOutlined /> },
                { key: 'follow_ups', label: '渠道跟进', icon: <TeamOutlined /> },
                ...(record.can_edit ? [{ key: 'edit', label: '编辑', icon: <EditOutlined /> }] : []),
                ...(record.can_delete ? [{ key: 'delete', label: '删除', icon: <DeleteOutlined />, danger: true }] : []),
              ],
              onClick: ({ key }) => {
                if (key === 'view') handleView(record);
                else if (key === 'follow_ups') handleViewFollowUps(record);
                else if (key === 'edit') handleEdit(record);
                else if (key === 'delete') handleDelete(record.id);
              },
            }}
            trigger={['click']}
          >
            <Button size="small" icon={<MenuOutlined />} />
          </Dropdown>
        </div>
      ),
    },
  ];

  const expandedRowRender = (record: Channel) => (
    <Descriptions column={2} size="small">
      <Descriptions.Item label="邮箱">{record.email || '-'}</Descriptions.Item>
      <Descriptions.Item label="官网">{record.website || '-'}</Descriptions.Item>
      <Descriptions.Item label="详细地址" span={2}>{record.address || '-'}</Descriptions.Item>
      <Descriptions.Item label="微信公众号">{record.wechat || '-'}</Descriptions.Item>
      <Descriptions.Item label="统一社会信用代码">{record.credit_code || '-'}</Descriptions.Item>
      <Descriptions.Item label="开户行">{record.bank_name || '-'}</Descriptions.Item>
      <Descriptions.Item label="银行账号">{record.bank_account || '-'}</Descriptions.Item>
      <Descriptions.Item label="折扣率">{record.discount_rate ? `${(record.discount_rate * 100).toFixed(0)}折` : '-'}</Descriptions.Item>
      <Descriptions.Item label="备注" span={2}>{record.notes || '-'}</Descriptions.Item>
    </Descriptions>
  );

  return (
    <PageScaffold
      title="渠道档案"
      breadcrumbItems={[{ title: '首页' }, { title: '渠道档案' }]}
      extra={
        canCreateChannel ? (
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新建渠道
          </Button>
        ) : null
      }
    >
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Search
            placeholder="搜索公司名称或编号"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 250 }}
          />
          <Select
            placeholder="渠道类型"
            value={typeFilter}
            onChange={setTypeFilter}
            style={{ width: 120 }}
            allowClear
          >
            {typeOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>{opt.label}</Option>
            ))}
          </Select>
          <Select
            placeholder="状态"
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
            placeholder="省份"
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
      </div>

      <Table
        columns={baseColumns}
        dataSource={filteredChannels}
        loading={isLoading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        scroll={{ x: 750 }}
        onRow={(record) => ({
          onClick: () => navigate(`/channels/${record.id}/full`),
          style: { cursor: 'pointer' },
        })}
        expandable={{
          expandedRowRender,
          rowExpandable: () => true,
        }}
      />

      <PageDrawer
        title={editingChannel ? '编辑渠道' : '新建渠道'}
        open={isDrawerOpen}
        onClose={() => {
          setIsDrawerOpen(false);
          form.resetFields();
          setEditingChannel(null);
          if (isCreateRoute) {
            navigate('/channels');
          }
        }}
        width={680}
      >
        <Form form={form} layout="vertical">
          <Form.Item 
            name="company_name" 
            label="公司名称" 
            rules={[{ required: true, message: '请输入公司名称!' }]}
          >
            <Input placeholder="请输入公司名称" />
          </Form.Item>

          <Space style={{ width: '100%' }} size="large">
            <Form.Item 
              name="channel_type" 
              label="渠道类型" 
              rules={[{ required: true, message: '请选择渠道类型!' }]}
              style={{ width: 200 }}
            >
              <Select placeholder="选择类型">
                {typeOptions.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item name="status" label="状态" style={{ width: 150 }}>
              <Select placeholder="选择状态">
                {statusOptions.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>
          </Space>

          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="main_contact" label="主要联系人" style={{ width: 200 }}>
              <Input placeholder="联系人姓名" />
            </Form.Item>
            <Form.Item name="phone" label="电话" style={{ width: 150 }}>
              <Input placeholder="联系电话" />
            </Form.Item>
            <Form.Item name="email" label="邮箱" style={{ width: 200 }}>
              <Input placeholder="邮箱地址" />
            </Form.Item>
          </Space>

          <Form.Item name="region" label="省份/城市">
            <Cascader
              options={regionOptions}
              placeholder="请选择省份/城市"
              showSearch
            />
          </Form.Item>

          <Form.Item name="address" label="详细地址">
            <Input placeholder="详细地址" />
          </Form.Item>

          <Form.Item 
            name="credit_code" 
            label="统一社会信用代码"
            rules={[
              { required: true, message: '请输入统一社会信用代码!' },
              { len: 18, message: '统一社会信用代码应为 18 位!' },
              {
                validator: async (_, value) => {
                  if (!value || value.length !== 18) return Promise.resolve();
                  const exists = await checkChannelCreditCodeExists(value, editingChannel?.id);
                  if (exists) {
                    return Promise.reject(new Error('该统一社会信用代码已存在!'));
                  }
                  return Promise.resolve();
                }
              }
            ]}
          >
            <Input placeholder="18 位信用代码" maxLength={18} />
          </Form.Item>

          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="bank_name" label="开户行" style={{ width: 200 }}>
              <Input placeholder="开户银行" />
            </Form.Item>
            <Form.Item name="bank_account" label="银行账号" style={{ width: 200 }}>
              <Input placeholder="银行账号" />
            </Form.Item>
          </Space>

          <Form.Item name="billing_info" label="开票信息">
            <Input.TextArea rows={2} placeholder="开票信息详情" />
          </Form.Item>

          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="website" label="官网" style={{ width: 200 }}>
              <Input placeholder="公司官网地址" />
            </Form.Item>
            <Form.Item name="wechat" label="微信公众号" style={{ width: 200 }}>
              <Input placeholder="微信公众号名称" />
            </Form.Item>
          </Space>

          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="cooperation_region" label="合作区域" style={{ width: 200 }}>
              <Input placeholder="合作区域" />
            </Form.Item>
            <Form.Item name="discount_rate" label="折扣率" style={{ width: 150 }}>
              <Input type="number" placeholder="如：0.85 表示 85 折" step="0.01" min="0" max="1" />
            </Form.Item>
          </Space>

          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={3} placeholder="其他备注信息" />
          </Form.Item>

          <Button type="primary" onClick={handleDrawerOk} loading={createMutation.isPending || updateMutation.isPending} block>
            保存
          </Button>
        </Form>
      </PageDrawer>
    </PageScaffold>
  );
};

export default ChannelList;
