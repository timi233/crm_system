import React, { useState } from 'react';
import { Table, Button, Space, Tag, Input, Select, Form, Dropdown, Descriptions, Empty, message, Modal } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, MenuOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useProjects, useCreateProject, useUpdateProject, useDeleteProject } from '../../hooks/useProjects';
import { useDictItems } from '../../hooks/useDictItems';
import { useCustomers } from '../../hooks/useCustomers';
import { useUsers } from '../../hooks/useUsers';
import PageScaffold from '../../components/common/PageScaffold';
import PageDrawer from '../../components/common/PageDrawer';

const { Option } = Select;
const { Search } = Input;

const ProjectList: React.FC = () => {
  const navigate = useNavigate();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<any>(null);
  const [searchText, setSearchText] = useState('');
  const [projectStatusFilter, setProjectStatusFilter] = useState<string | null>(null);
  const [form] = Form.useForm();

  const { data: projects = [], isLoading } = useProjects();
  const { data: statusItems = [] } = useDictItems('项目状态');
  const { data: productItems = [] } = useDictItems('产品品牌');
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
    setIsDrawerOpen(true);
  };

  const handleEdit = (project: any) => {
    setEditingProject(project);
    form.setFieldsValue(project);
    setIsDrawerOpen(true);
  };

  const handleView = (project: any) => {
    navigate(`/projects/${project.id}/full`);
  };

  const handleDelete = (projectId: number) => {
    Modal.confirm({
      title: '确定删除该项目吗？',
      content: '此操作不可恢复',
      onOk: async () => {
        try {
          await deleteMutation.mutateAsync(projectId);
          message.success('项目删除成功');
        } catch (error) {
        }
      }
    });
  };

  const handleDrawerOk = async () => {
    try {
      const values = await form.validateFields();

      if (editingProject) {
        await updateMutation.mutateAsync({ id: editingProject.id, project: values });
      } else {
        await createMutation.mutateAsync(values);
      }

      setIsDrawerOpen(false);
      form.resetFields();
    } catch (error) {
      console.error('Failed to save project:', error);
    }
  };

  const baseColumns = [
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
      width: 200,
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
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: any, record: any) => (
        <Dropdown
          menu={{
            items: [
              { key: 'view', label: '查看', icon: <EyeOutlined /> },
              { key: 'edit', label: '编辑', icon: <EditOutlined /> },
              { key: 'delete', label: '删除', icon: <DeleteOutlined />, danger: true },
            ],
            onClick: ({ key }) => {
              if (key === 'view') handleView(record);
              else if (key === 'edit') handleEdit(record);
              else if (key === 'delete') handleDelete(record.id);
            },
          }}
          trigger={['click']}
        >
          <Button size="small" icon={<MenuOutlined />} />
        </Dropdown>
      ),
    },
  ];

  const expandedRowRender = (record: any) => (
    <Descriptions column={3} size="small">
      <Descriptions.Item label="产品">
        {record.products && record.products.length > 0 
          ? record.products.map(p => <Tag key={p} color="blue">{p}</Tag>) 
          : '-'}
      </Descriptions.Item>
      <Descriptions.Item label="业务类型">{record.business_type || '-'}</Descriptions.Item>
      <Descriptions.Item label="下游合同金额">{record.downstream_contract_amount ? `¥${record.downstream_contract_amount.toLocaleString()}` : '-'}</Descriptions.Item>
      <Descriptions.Item label="上游采购金额">{record.upstream_procurement_amount ? `¥${record.upstream_procurement_amount.toLocaleString()}` : '-'}</Descriptions.Item>
      <Descriptions.Item label="毛利率">{record.gross_margin ? `¥${record.gross_margin.toLocaleString()}` : '-'}</Descriptions.Item>
      <Descriptions.Item label="备注">{record.notes || '-'}</Descriptions.Item>
    </Descriptions>
  );

  return (
    <PageScaffold
      title="项目管理"
      breadcrumbItems={[{ title: '首页' }, { title: '项目管理' }]}
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
        columns={baseColumns}
        dataSource={filteredProjects}
        loading={isLoading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        scroll={{ x: 800 }}
        expandable={{
          expandedRowRender,
          rowExpandable: () => true,
        }}
        locale={{ emptyText: <Empty description="暂无项目数据" image={Empty.PRESENTED_IMAGE_SIMPLE}>
          <Button type="primary" onClick={handleCreate}>+ 新建第一条项目</Button>
        </Empty> }}
      />

      <PageDrawer
        title={editingProject ? '编辑项目' : '新建项目'}
        open={isDrawerOpen}
        onClose={() => {
          setIsDrawerOpen(false);
          form.resetFields();
          setEditingProject(null);
        }}
        width={680}
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
            name="terminal_customer_id" 
            label="终端客户" 
            rules={[{ required: true, message: '请选择终端客户!' }]}
          >
            <Select placeholder="选择终端客户" showSearch optionFilterProp="label">
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
            <Select placeholder="选择销售负责人" showSearch optionFilterProp="label">
              {userOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>

          <Space style={{ width: '100%' }} size="large">
            <Form.Item 
              name="business_type" 
              label="业务类型" 
              rules={[{ required: true, message: '请输入业务类型!' }]}
              style={{ width: 200 }}
            >
              <Input placeholder="如：直销、渠道" />
            </Form.Item>

            <Form.Item 
              name="project_status" 
              label="项目状态" 
              rules={[{ required: true, message: '请选择项目状态!' }]}
              style={{ width: 150 }}
            >
              <Select placeholder="选择状态">
                {statusOptions.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>
          </Space>

          <Form.Item 
            name="downstream_contract_amount" 
            label="下游合同金额" 
            rules={[{ required: true, message: '请输入下游合同金额!' }]}
          >
            <Input type="number" placeholder="金额" />
          </Form.Item>

          <Form.Item name="upstream_procurement_amount" label="上游采购金额">
            <Input type="number" placeholder="金额" />
          </Form.Item>

          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={3} placeholder="备注信息" />
          </Form.Item>

          <Button type="primary" onClick={handleDrawerOk} loading={createMutation.isPending || updateMutation.isPending} block>
            保存
          </Button>
        </Form>
      </PageDrawer>
    </PageScaffold>
  );
};

export default ProjectList;
