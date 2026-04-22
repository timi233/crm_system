import React, { useState } from 'react';
import { App, Table, Button, Space, Modal, Form, Input, Select, Card, Drawer } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import { useKnowledgeList, useCreateKnowledge, useUpdateKnowledge, useDeleteKnowledge } from '../../hooks/useKnowledge';
import { Knowledge, KnowledgeCreate } from '../../types/knowledge';

const { Option } = Select;
const { Search } = Input;
const { TextArea } = Input;

const KnowledgeList: React.FC = () => {
  const { message, modal } = App.useApp();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isDetailVisible, setIsDetailVisible] = useState(false);
  const [viewingKnowledge, setViewingKnowledge] = useState<Knowledge | null>(null);
  const [editingKnowledge, setEditingKnowledge] = useState<Knowledge | null>(null);
  const [searchText, setSearchText] = useState('');
  const [problemTypeFilter, setProblemTypeFilter] = useState<string | undefined>(undefined);
  const [form] = Form.useForm();

  const { data: knowledgeList = [], isLoading } = useKnowledgeList({
    keyword: searchText || undefined,
    problem_type: problemTypeFilter,
  });

  const createMutation = useCreateKnowledge();
  const updateMutation = useUpdateKnowledge();
  const deleteMutation = useDeleteKnowledge();

  const handleViewDetail = (knowledge: Knowledge) => {
    setViewingKnowledge(knowledge);
    setIsDetailVisible(true);
  };

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

  const handleDelete = (knowledgeId: number) => {
    modal.confirm({
      title: '确定删除该知识条目吗？',
      content: '此操作不可恢复',
      onOk: async () => {
        try {
          await deleteMutation.mutateAsync(knowledgeId);
          message.success('删除成功');
        } catch (error) {
          console.error('Failed to delete knowledge:', error);
        }
      }
    });
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingKnowledge) {
        await updateMutation.mutateAsync({ 
          id: editingKnowledge.id, 
          knowledge: values as KnowledgeCreate 
        });
        message.success('更新成功');
      } else {
        await createMutation.mutateAsync(values as KnowledgeCreate);
        message.success('创建成功');
      }
      
      setIsModalVisible(false);
      form.resetFields();
    } catch (error) {
      console.error('Failed to save knowledge:', error);
    }
  };

  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: '问题类型',
      dataIndex: 'problem_type',
      key: 'problem_type',
      width: 150,
      filters: Array.from(new Set(knowledgeList.map(k => k.problem_type))).map(type => ({
        text: type,
        value: type,
      })),
      onFilter: (value: any, record: Knowledge) => record.problem_type === value,
    },
    {
      title: '浏览次数',
      dataIndex: 'view_count',
      key: 'view_count',
      width: 100,
      sorter: (a: Knowledge, b: Knowledge) => a.view_count - b.view_count,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => date ? new Date(date).toLocaleString('zh-CN') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 280,
      render: (_: any, record: Knowledge) => (
        <Space size="small">
          <Button 
            icon={<EyeOutlined />} 
            size="small"
            onClick={() => handleViewDetail(record)}
          >
            详情
          </Button>
          <Button 
            icon={<EditOutlined />} 
            size="small"
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Button 
            icon={<DeleteOutlined />} 
            danger
            size="small"
            onClick={() => handleDelete(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  // 获取所有问题类型用于筛选
  const problemTypes = Array.from(new Set(knowledgeList.map(k => k.problem_type)));

  return (
    <Card
      title="知识库管理"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建知识条目
        </Button>
      }
    >
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Search
            placeholder="搜索标题、问题、解决方案"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 250 }}
            allowClear
          />
          <Select
            placeholder="筛选问题类型"
            value={problemTypeFilter}
            onChange={setProblemTypeFilter}
            style={{ width: 200 }}
            allowClear
            showSearch
          >
            {problemTypes.map(type => (
              <Option key={type} value={type}>
                {type}
              </Option>
            ))}
          </Select>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={knowledgeList}
        loading={isLoading}
        rowKey="id"
        pagination={{ 
          pageSize: 10,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
        }}
      />
      
      <Drawer
        title={editingKnowledge ? '编辑知识条目' : '新建知识条目'}
        open={isModalVisible}
        onClose={() => setIsModalVisible(false)}
        width={520}
        maskClosable={false}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item 
            name="title" 
            label="标题" 
            rules={[{ required: true, message: '请输入标题!' }]}
          >
            <Input placeholder="请输入知识条目标题" />
          </Form.Item>
          
          <Form.Item 
            name="problem" 
            label="问题描述" 
            rules={[{ required: true, message: '请输入问题描述!' }]}
          >
            <TextArea 
              rows={4} 
              placeholder="请详细描述问题场景"
            />
          </Form.Item>
          
          <Form.Item 
            name="solution" 
            label="解决方案" 
            rules={[{ required: true, message: '请输入解决方案!' }]}
          >
            <TextArea 
              rows={6} 
              placeholder="请提供详细的解决方案步骤"
            />
          </Form.Item>
          
          <Form.Item 
            name="problem_type" 
            label="问题类型" 
            rules={[{ required: true, message: '请选择问题类型!' }]}
          >
            <Select placeholder="请选择问题类型">
              <Option value="产品咨询">产品咨询</Option>
              <Option value="技术支持">技术支持</Option>
              <Option value="售后服务">售后服务</Option>
              <Option value="商务问题">商务问题</Option>
              <Option value="其他">其他</Option>
            </Select>
          </Form.Item>
          
          <Form.Item 
            name="source_type" 
            label="来源类型" 
          >
            <Select placeholder="请选择来源类型" allowClear>
              <Option value="manual">手动录入</Option>
              <Option value="work_order">工单生成</Option>
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
        title={viewingKnowledge?.title}
        open={isDetailVisible}
        onClose={() => setIsDetailVisible(false)}
        width={520}
        maskClosable={false}
        destroyOnClose
      >
        {viewingKnowledge && (
          <div style={{ lineHeight: 1.8 }}>
            <div style={{ marginBottom: 16 }}>
              <strong>问题类型：</strong>
              <span style={{ marginLeft: 8 }}>{viewingKnowledge.problem_type}</span>
            </div>
            {viewingKnowledge.source_type_name && (
              <div style={{ marginBottom: 16 }}>
                <strong>来源类型：</strong>
                <span style={{ marginLeft: 8 }}>{viewingKnowledge.source_type_name}</span>
              </div>
            )}
            <div style={{ marginBottom: 16 }}>
              <strong>浏览次数：</strong>
              <span style={{ marginLeft: 8 }}>{viewingKnowledge.view_count}</span>
            </div>
            <div style={{ marginBottom: 16 }}>
              <strong>创建时间：</strong>
              <span style={{ marginLeft: 8 }}>
                {viewingKnowledge.created_at ? new Date(viewingKnowledge.created_at).toLocaleString('zh-CN') : '-'}
              </span>
            </div>
            {viewingKnowledge.created_by_name && (
              <div style={{ marginBottom: 16 }}>
                <strong>创建人：</strong>
                <span style={{ marginLeft: 8 }}>{viewingKnowledge.created_by_name}</span>
              </div>
            )}
            
            <div style={{ marginTop: 24, paddingTop: 16, borderTop: '1px solid #f0f0f0' }}>
              <div style={{ fontWeight: 600, marginBottom: 8, fontSize: 16 }}>问题描述</div>
              <div style={{ whiteSpace: 'pre-wrap', color: '#666' }}>
                {viewingKnowledge.problem}
              </div>
            </div>
            
            <div style={{ marginTop: 24, paddingTop: 16, borderTop: '1px solid #f0f0f0' }}>
              <div style={{ fontWeight: 600, marginBottom: 8, fontSize: 16 }}>解决方案</div>
              <div style={{ whiteSpace: 'pre-wrap', color: '#333' }}>
                {viewingKnowledge.solution}
              </div>
            </div>
            
            <div style={{ marginTop: 24 }}>
              <Button onClick={() => setIsDetailVisible(false)} block>
                关闭
              </Button>
            </div>
          </div>
        )}
      </Drawer>
    </Card>
  );
};

export default KnowledgeList;
