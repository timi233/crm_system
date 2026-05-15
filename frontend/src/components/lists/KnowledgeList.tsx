import React, { useState } from 'react';
import { App, Table, Button, Space, Modal, Form, Input, Select, Card, Tag, Row, Col } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, BookOutlined } from '@ant-design/icons';
import { useKnowledgeList, useCreateKnowledge, useUpdateKnowledge, useDeleteKnowledge } from '../../hooks/useKnowledge';
import { Knowledge } from '../../types/knowledge';
import PageScaffold from '../../components/common/PageScaffold';
import PageModal from '../../components/common/PageModal';

const { Option } = Select;

const KnowledgeList: React.FC = () => {
  const { message, modal } = App.useApp();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingKnowledge, setEditingKnowledge] = useState<Knowledge | null>(null);
  const [searchText, setSearchText] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null);
  const [form] = Form.useForm();

  const { data: knowledgeList = [], isLoading } = useKnowledgeList();
  const createMutation = useCreateKnowledge();
  const updateMutation = useUpdateKnowledge();
  const deleteMutation = useDeleteKnowledge();

  const categories = Array.from(new Set(knowledgeList.map(k => k.problem_type).filter(Boolean)));

  const filteredKnowledge = knowledgeList.filter(k => {
    const matchesSearch = !searchText ||
      k.title.toLowerCase().includes(searchText.toLowerCase()) ||
      k.problem.toLowerCase().includes(searchText.toLowerCase()) ||
      k.solution.toLowerCase().includes(searchText.toLowerCase());
    const matchesCategory = !categoryFilter || k.problem_type === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const handleCreate = () => {
    setEditingKnowledge(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (knowledge: Knowledge) => {
    setEditingKnowledge(knowledge);
    form.setFieldsValue(knowledge);
    setIsModalVisible(true);
  };

  const handleDelete = (id: number) => {
    modal.confirm({
      title: '确定删除该知识库条目吗？',
      content: '此操作不可恢复',
      okType: 'danger',
      onOk: async () => {
        try {
          await deleteMutation.mutateAsync(id);
          message.success('条目已删除');
        } catch (error) {}
      }
    });
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      if (editingKnowledge) {
        await updateMutation.mutateAsync({ id: editingKnowledge.id, knowledge: values });
        message.success('条目信息已更新');
      } else {
        await createMutation.mutateAsync(values);
        message.success('新条目已创建');
      }
      setIsModalVisible(false);
      form.resetFields();
    } catch (error) {}
  };

  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      render: (text: string) => <span style={{ fontWeight: 600 }}>{text}</span>,
    },
    {
      title: '分类',
      dataIndex: 'problem_type',
      key: 'problem_type',
      width: 150,
      render: (cat: string) => <Tag style={{ border: 'none', background: '#e0e7ff', color: '#4338ca' }}>{cat || '未分类'}</Tag>,
    },
    {
      title: '最后更新',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 180,
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: Knowledge) => (
        <Space size="middle">
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)}>删除</Button>
        </Space>
      ),
    },
  ];

  return (
    <PageScaffold
      title="知识库管理"
      breadcrumbItems={[{ title: '首页' }, { title: '知识库' }]}
      extra={
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleCreate}
          size="large"
          className="btn--gradient"
          style={{ height: '40px', padding: '0 20px' }}
        >
          发布新知识
        </Button>
      }
      filters={
        <Space size={16} wrap>
          <Input.Search
            placeholder="搜索标题或内容"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 280 }}
            size="middle"
          />
          <Select
            placeholder="筛选分类"
            value={categoryFilter}
            onChange={setCategoryFilter}
            style={{ width: 180 }}
            allowClear
          >
            {categories.map(cat => (
              <Option key={cat} value={cat}>{cat}</Option>
            ))}
          </Select>
        </Space>
      }
    >
      <Table
        columns={columns}
        dataSource={filteredKnowledge}
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
        title={editingKnowledge ? '编辑知识条目' : '发布新知识文档'}
        open={isModalVisible}
        onClose={() => setIsModalVisible(false)}
        width={800}
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
            发布并保存
          </Button>
        ]}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="title"
            label="文档标题"
            rules={[{ required: true, message: '请输入标题!' }]}
          >
            <Input placeholder="输入清晰明确的文档标题" />
          </Form.Item>

          <Form.Item
            name="problem_type"
            label="所属分类"
            rules={[{ required: true, message: '请选择或输入分类!' }]}
          >
            <Select placeholder="选择现有分类或输入新分类" mode="tags">
              {categories.map(cat => (
                <Option key={cat} value={cat}>{cat}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="problem"
            label="问题描述"
            rules={[{ required: true, message: '请输入问题描述!' }]}
          >
            <Input.TextArea rows={6} placeholder="详细描述遇到的问题..." />
          </Form.Item>

          <Form.Item
            name="solution"
            label="解决方案"
            rules={[{ required: true, message: '请输入解决方案!' }]}
          >
            <Input.TextArea rows={10} placeholder="输入解决该问题的具体步骤和方法..." />
          </Form.Item>
        </Form>
      </PageModal>
    </PageScaffold>
  );
};

export default KnowledgeList;
