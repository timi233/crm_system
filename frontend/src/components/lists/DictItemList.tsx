import React, { useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select, Card, Tag, InputNumber, Switch, Cascader, Row, Col, App } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, MenuOutlined } from '@ant-design/icons';
import { useDictItems, useCreateDictItem, useUpdateDictItem, useDeleteDictItem, DictItem } from '../../hooks/useDictItems';
import PageScaffold from '../../components/common/PageScaffold';
import PageModal from '../../components/common/PageModal';

const { Option } = Select;

const DICT_CATEGORIES = [
  '客户行业', '客户状态', '商机来源', '商机阶段', '项目状态', '产品品牌', '渠道类型', '渠道状态', '跟进方式', '跟进结论'
];

const DictItemList: React.FC = () => {
  const { message, modal } = App.useApp();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingItem, setEditingItem] = useState<DictItem | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string | undefined>(undefined);
  const [form] = Form.useForm();

  const { data: items = [], isLoading } = useDictItems(categoryFilter);
  const createMutation = useCreateDictItem();
  const updateMutation = useUpdateDictItem();
  const deleteMutation = useDeleteDictItem();

  const handleCreate = () => {
    setEditingItem(null);
    form.resetFields();
    form.setFieldsValue({ is_active: true, sort_order: 0, category: categoryFilter });
    setIsModalVisible(true);
  };

  const handleEdit = (item: DictItem) => {
    setEditingItem(item);
    form.setFieldsValue(item);
    setIsModalVisible(true);
  };

  const handleDelete = (id: number) => {
    modal.confirm({
      title: '确定删除该数据字典项吗？',
      content: '删除后可能会影响关联业务数据的展示。',
      okType: 'danger',
      onOk: async () => {
        try {
          await deleteMutation.mutateAsync(id);
          message.success('配置项已删除');
        } catch (error) {}
      }
    });
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      if (editingItem) {
        await updateMutation.mutateAsync({ id: editingItem.id, item: values });
        message.success('配置项已更新');
      } else {
        await createMutation.mutateAsync(values);
        message.success('配置项已创建');
      }
      setIsModalVisible(false);
      form.resetFields();
    } catch (error) {}
  };

  const columns = [
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 150,
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '排序',
      dataIndex: 'sort_order',
      key: 'sort_order',
      width: 80,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => <Tag color={active ? 'success' : 'default'} style={{ border: 'none' }}>{active ? '激活' : '停用'}</Tag>,
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: DictItem) => (
        <Space size="middle">
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)}>删除</Button>
        </Space>
      ),
    },
  ];

  return (
    <PageScaffold
      title="数据字典管理"
      breadcrumbItems={[{ title: '首页' }, { title: '系统配置' }, { title: '数据字典' }]}
      extra={
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleCreate}
          size="large"
          className="btn--gradient"
          style={{ height: '40px', padding: '0 20px' }}
        >
          新建字典项
        </Button>
      }
      filters={
        <Space size={16} wrap>
          <Select
            placeholder="筛选字典分类"
            value={categoryFilter}
            onChange={setCategoryFilter}
            style={{ width: 220 }}
            allowClear
          >
            {DICT_CATEGORIES.map(cat => (
              <Option key={cat} value={cat}>{cat}</Option>
            ))}
          </Select>
        </Space>
      }
    >
      <Table
        columns={columns}
        dataSource={items}
        loading={isLoading}
        rowKey="id"
        pagination={{
          pageSize: 20,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条数据`,
        }}
        className="customer-table"
        bordered={false}
      />

      <PageModal
        title={editingItem ? '编辑字典项' : '新增字典配置'}
        open={isModalVisible}
        onClose={() => setIsModalVisible(false)}
        width={560}
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
            保存配置
          </Button>
        ]}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="category"
            label="字典分类"
            rules={[{ required: true, message: '请选择分类!' }]}
          >
            <Select placeholder="选择所属业务分类">
              {DICT_CATEGORIES.map(cat => (
                <Option key={cat} value={cat}>{cat}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="name"
            label="选项名称"
            rules={[{ required: true, message: '请输入名称!' }]}
          >
            <Input placeholder="输入显示的文本" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="sort_order" label="排序权重">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="is_active" label="是否激活" valuePropName="checked">
                <Switch checkedChildren="开启" unCheckedChildren="停用" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="description" label="描述说明">
            <Input.TextArea rows={3} placeholder="配置项的详细说明..." />
          </Form.Item>
        </Form>
      </PageModal>
    </PageScaffold>
  );
};

export default DictItemList;
