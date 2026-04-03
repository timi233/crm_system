import React, { useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select, Card, Tag, Tabs, Row, Col, message, Popconfirm, Cascader } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ShopOutlined, BankOutlined, EnvironmentOutlined, GlobalOutlined, TeamOutlined, EyeOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useChannels, useCreateChannel, useUpdateChannel, useDeleteChannel, Channel, ChannelCreate } from '../../hooks/useChannels';
import { useDictItems, useRegionCascader } from '../../hooks/useDictItems';
import api from '../../services/api';

const { Option } = Select;
const { Search } = Input;
const { TabPane } = Tabs;

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
  const navigate = useNavigate();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingChannel, setEditingChannel] = useState<Channel | null>(null);
  const [searchText, setSearchText] = useState('');
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [form] = Form.useForm();

  const { data: channels = [], isLoading } = useChannels();
  const { data: typeItems = [] } = useDictItems('渠道类型');
  const { data: statusItems = [] } = useDictItems('渠道状态');
  const { data: regionOptions = [] } = useRegionCascader();

  const typeOptions = typeItems.map(item => ({ value: item.name, label: item.name }));
  const statusOptions = statusItems.map(item => ({ value: item.name, label: item.name }));

  const filteredChannels = channels.filter(channel => {
    const matchesSearch = !searchText ||
      channel.company_name?.toLowerCase().includes(searchText.toLowerCase()) ||
      channel.channel_code?.toLowerCase().includes(searchText.toLowerCase());
    const matchesType = !typeFilter || channel.channel_type === typeFilter;
    const matchesStatus = !statusFilter || channel.status === statusFilter;
    return matchesSearch && matchesType && matchesStatus;
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

  const handleCreate = () => {
    setEditingChannel(null);
    form.resetFields();
    form.setFieldsValue({ status: '合作中' });
    setIsModalVisible(true);
  };

  const handleEdit = (channel: Channel) => {
    setEditingChannel(channel);
    const regionArray = channel.province && channel.city ? [channel.province, channel.city] : [];
    form.setFieldsValue({
      ...channel,
      region: regionArray.length > 0 ? regionArray : undefined,
    });
    setIsModalVisible(true);
  };

  const handleView = (channel: Channel) => {
    navigate(`/channels/${channel.id}/full`);
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
      title: '渠道编号',
      dataIndex: 'channel_code',
      key: 'channel_code',
      width: 150,
    },
    {
      title: '公司名称',
      dataIndex: 'company_name',
      key: 'company_name',
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
      width: 120,
    },
    {
      title: '地区',
      key: 'region',
      width: 120,
      render: (_: any, record: Channel) => {
        const parts = [record.province, record.city].filter(Boolean);
        return parts.length > 0 ? parts.join(' ') : '-';
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 160,
      render: (_: any, record: Channel) => (
        <Space size="small">
          <Button size="small" icon={<EyeOutlined />} onClick={() => handleView(record)}>
            查看
          </Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Popconfirm
            title="确定删除该渠道吗？"
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
          <ShopOutlined />
          渠道档案
        </Space>
      }
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建渠道
        </Button>
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
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={filteredChannels}
        loading={isLoading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        scroll={{ x: 1200 }}
      />

      <Modal
        title={editingChannel ? '编辑渠道' : '新建渠道'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => setIsModalVisible(false)}
        okText="保存"
        cancelText="取消"
        width={800}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
      >
        <Form form={form} layout="vertical">
          <Tabs defaultActiveKey="basic">
            <TabPane tab="基本信息" key="basic">
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item 
                    name="company_name" 
                    label="公司名称" 
                    rules={[{ required: true, message: '请输入公司名称!' }]}
                  >
                    <Input placeholder="请输入公司名称" />
                  </Form.Item>
                </Col>
                <Col span={6}>
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
                <Col span={6}>
                  <Form.Item name="status" label="状态">
                    <Select placeholder="选择状态">
                      {statusOptions.map(opt => (
                        <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item name="main_contact" label="主要联系人">
                    <Input placeholder="联系人姓名" />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="phone" label="电话">
                    <Input placeholder="联系电话" />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="email" label="邮箱">
                    <Input placeholder="邮箱地址" />
                  </Form.Item>
                </Col>
              </Row>
            </TabPane>

            <TabPane tab="地址信息" key="address">
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="region" label="省份/城市">
                    <Cascader
                      options={regionOptions}
                      placeholder="请选择省份/城市"
                      showSearch
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="address" label="详细地址">
                    <Input placeholder="详细地址" />
                  </Form.Item>
                </Col>
              </Row>
            </TabPane>

            <TabPane tab="财务信息" key="finance">
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item 
                    name="credit_code" 
                    label="统一社会信用代码"
                    rules={[
                      { required: true, message: '请输入统一社会信用代码!' },
                      { len: 18, message: '统一社会信用代码应为18位!' },
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
                    <Input placeholder="18位信用代码" maxLength={18} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="bank_name" label="开户行">
                    <Input placeholder="开户银行" />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="bank_account" label="银行账号">
                    <Input placeholder="银行账号" />
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item name="billing_info" label="开票信息">
                <Input.TextArea rows={2} placeholder="开票信息详情" />
              </Form.Item>
            </TabPane>

            <TabPane tab="网络渠道" key="web">
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="website" label="官网">
                    <Input placeholder="公司官网地址" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="wechat" label="微信公众号">
                    <Input placeholder="微信公众号名称" />
                  </Form.Item>
                </Col>
              </Row>
            </TabPane>

            <TabPane tab="合作信息" key="cooperation">
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item name="cooperation_region" label="合作区域">
                    <Input placeholder="合作区域" />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="discount_rate" label="折扣率">
                    <Input type="number" placeholder="如: 0.85 表示85折" step="0.01" min="0" max="1" />
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item name="notes" label="备注">
                <Input.TextArea rows={3} placeholder="其他备注信息" />
              </Form.Item>
            </TabPane>
          </Tabs>
        </Form>
      </Modal>
    </Card>
  );
};

export default ChannelList;