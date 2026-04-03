import React, { useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select, InputNumber, Card, Tag } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useProjects, useCreateProject, useUpdateProject, useDeleteProject } from '../../hooks/useProjects';
import { useDictItems } from '../../hooks/useDictItems';
import { useCustomers } from '../../hooks/useCustomers';
import { useUsers } from '../../hooks/useUsers';

const { Option } = Select;
const { Search } = Input;
const { confirm } = Modal;

const ProjectList: React.FC = () => {
  const navigate = useNavigate();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingProject, setEditingProject] = useState<any>(null);
  const [searchText, setSearchText] = useState('');
  const [projectStatusFilter, setProjectStatusFilter] = useState<string | null>(null);
  const [form] = Form.useForm();

  const { data: projects = [], isLoading } = useProjects();
  const { data: statusItems = [] } = useDictItems('项目状态');
  const { data: customers = [] } = useCustomers();
  const { data: users = [] } = useUsers();

  const statusOptions = statusItems.map(item => ({ value: item.name, label: item.name }));
  const customerOptions = customers.map(c => ({ value: c.id, label: c.customer_name }));
  const userOptions = users.map(u => ({ value: u.id, label: u.name }));

  const filteredProjects = projects.filter(project => {
    const matchesSearch = !searchText ||
      project.project_name?.toLowerCase().includes(searchText.toLowerCase());

    const matchesStatus = !projectStatusFilter || project.project_status === projectStatusFilter;

    return matchesSearch && matchesStatus;
  });

  const createMutation = useCreateProject();
  const updateMutation = useUpdateProject();
  const deleteMutation = useDeleteProject();

  const handleCreate = () => {
    setEditingProject(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (project: any) => {
    setEditingProject(project);
    form.setFieldsValue(project);
    setIsModalVisible(true);
  };

  const handleView = (project: any) => {
    navigate(`/projects/${project.id}/full`);
  };

  const handleDelete = (projectId: number) => {
    confirm({
      title: '确定删除该项目吗？',
      content: '此操作不可恢复',
      onOk: async () => {
        try {
          await deleteMutation.mutateAsync(projectId);
        } catch (error) {
          console.error('Failed to delete project:', error);
        }
      }
    });
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();

      if (editingProject) {
        await updateMutation.mutateAsync({ id: editingProject.id, project: values });
      } else {
        await createMutation.mutateAsync(values);
      }

      setIsModalVisible(false);
      form.resetFields();
    } catch (error) {
      console.error('Failed to save project:', error);
    }
  };

  const columns = [
    {
      title: '项目编号',
      dataIndex: 'project_code',
      key: 'project_code',
      width: 150,
    },
    {
      title: '项目名称',
      dataIndex: 'project_name',
      key: 'project_name',
    },
    {
      title: '项目状态',
      dataIndex: 'project_status',
      key: 'project_status',
      width: 100,
      render: (status: string) => <Tag color="blue">{status}</Tag>,
    },
    {
      title: '终端客户',
      dataIndex: 'terminal_customer_name',
      key: 'terminal_customer_name',
      width: 150,
      render: (name: string, record: any) => name || `ID: ${record.terminal_customer_id}`,
    },
    {
      title: '销售负责人',
      dataIndex: 'sales_owner_name',
      key: 'sales_owner_name',
      width: 100,
      render: (name: string, record: any) => name || `ID: ${record.sales_owner_id}`,
    },
    {
      title: '业务类型',
      dataIndex: 'business_type',
      key: 'business_type',
      width: 120,
    },
    {
      title: '下游合同金额',
      dataIndex: 'downstream_contract_amount',
      key: 'downstream_contract_amount',
      width: 120,
      render: (amount: number) => amount ? `¥${amount.toLocaleString()}` : '-',
    },
    {
      title: '毛利率',
      dataIndex: 'gross_margin',
      key: 'gross_margin',
      width: 100,
      render: (margin: number) => margin ? `¥${margin.toLocaleString()}` : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_: any, record: any) => (
        <Space size="small">
          <Button size="small" icon={<EyeOutlined />} onClick={() => handleView(record)}>
            查看
          </Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Button size="small" icon={<DeleteOutlined />} danger onClick={() => handleDelete(record.id)}>
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <Card
      title="项目管理列表"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建项目
        </Button>
      }
    >
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Search
            placeholder="搜索项目名称"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 200 }}
          />
          <Select
            placeholder="筛选项目状态"
            value={projectStatusFilter}
            onChange={setProjectStatusFilter}
            style={{ width: 150 }}
            allowClear
          >
            {statusOptions.map(opt => (
              <Option key={opt.value} value={opt.value}>
                {opt.label}
              </Option>
            ))}
          </Select>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={filteredProjects}
        loading={isLoading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        scroll={{ x: 1200 }}
      />

      <Modal
        title={editingProject ? '编辑项目' : '新建项目'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => setIsModalVisible(false)}
        okText="保存"
        cancelText="取消"
        width={600}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="project_name"
            label="项目名称"
            rules={[{ required: true, message: '请输入项目名称!' }]}
          >
            <Input placeholder="请输入项目名称" />
          </Form.Item>

          <Form.Item
            name="project_status"
            label="项目状态"
            rules={[{ required: true, message: '请选择项目状态!' }]}
          >
            <Select placeholder="请选择项目状态" showSearch>
              {statusOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
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
            name="business_type"
            label="业务类型"
            rules={[{ required: true, message: '请选择业务类型!' }]}
          >
            <Select placeholder="请选择业务类型">
              <Option value="New Project">新项目</Option>
              <Option value="Renewal/Maintenance">续费项目-SVC</Option>
              <Option value="Expansion">增购项目</Option>
              <Option value="Additional Purchase">其他</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="downstream_contract_amount"
            label="下游合同金额"
            rules={[{ required: true, message: '请输入下游合同金额!' }]}
          >
            <InputNumber placeholder="请输入金额" style={{ width: '100%' }} min={0} />
          </Form.Item>

          <Form.Item name="upstream_procurement_amount" label="上游采购金额">
            <InputNumber placeholder="请输入金额" style={{ width: '100%' }} min={0} />
          </Form.Item>

          <Form.Item name="notes" label="项目描述">
            <Input.TextArea rows={4} placeholder="项目描述信息" />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default ProjectList;