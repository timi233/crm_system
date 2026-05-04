import React, { useState } from 'react';
import { App, Button, Table, Space, Tag, Input, Select, Dropdown, Empty } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, MenuOutlined } from '@ant-design/icons';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useSelector } from 'react-redux';
import type { RootState } from '../store/store';
import { useProjects, useDeleteProject, Project } from '../hooks/useProjects';
import PageScaffold from '../components/common/PageScaffold';
import ProjectForm from '../components/forms/ProjectForm';

const { Option } = Select;

const ProjectListPage: React.FC = () => {
  const { message, modal } = App.useApp();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { capabilities } = useSelector((state: RootState) => state.auth);
  
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(searchParams.get('new') === 'true');

  const canCreateProject = Boolean(capabilities['project:create']);

  const { data: projects = [], isLoading } = useProjects();
  const deleteMutation = useDeleteProject();

  const filteredProjects = projects.filter(project => {
    const matchesSearch = !searchText || 
      project.project_name.toLowerCase().includes(searchText.toLowerCase()) ||
      project.project_code.toLowerCase().includes(searchText.toLowerCase());
    const matchesStatus = !statusFilter || project.project_status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case '执行中': return 'blue';
      case '已完成': return 'green';
      case '已终止': return 'red';
      default: return 'default';
    }
  };

  const handleCreate = () => {
    setIsDrawerOpen(true);
  };

  const handleView = (project: Project) => {
    navigate(`/projects/${project.id}/full`);
  };

  const handleEdit = (project: Project) => {
    navigate(`/projects/${project.id}/edit`);
  };

  const handleDelete = (projectId: number) => {
    modal.confirm({
      title: '确定删除该项目吗？',
      content: '此操作不可恢复',
      onOk: async () => {
        try {
          await deleteMutation.mutateAsync(projectId);
          message.success('项目删除成功');
        } catch (error: any) {
          if (error?.response?.data?.detail) {
            message.error(error.response.data.detail);
          }
        }
      }
    });
  };

  const columns = [
    {
      title: '项目编号',
      dataIndex: 'project_code',
      key: 'project_code',
      width: 140,
    },
    {
      title: '项目名称',
      dataIndex: 'project_name',
      key: 'project_name',
      width: 200,
      render: (text: string, record: Project) => (
        <a onClick={() => navigate(`/projects/${record.id}/full`)}>{text}</a>
      ),
    },
    {
      title: '业务类型',
      dataIndex: 'business_type',
      key: 'business_type',
      width: 120,
    },
    {
      title: '状态',
      dataIndex: 'project_status',
      key: 'project_status',
      width: 100,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>{status}</Tag>
      ),
    },
    {
      title: '负责人',
      dataIndex: 'sales_owner_name',
      key: 'sales_owner_name',
      width: 100,
    },
    {
      title: '下游合同金额',
      dataIndex: 'downstream_contract_amount',
      key: 'downstream_contract_amount',
      width: 150,
      render: (amount: number) => amount ? `¥${amount.toLocaleString()}` : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: any, record: Project) => (
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

  return (
    <PageScaffold
      title="项目管理"
      breadcrumbItems={[{ title: '首页', href: '/dashboard' }, { title: '项目管理' }]}
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate} disabled={!canCreateProject}>
          新建项目
        </Button>
      }
    >
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Input.Search
            placeholder="搜索项目名称或编号"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 200 }}
            allowClear
          />
          <Select
            placeholder="筛选状态"
            value={statusFilter}
            onChange={setStatusFilter}
            style={{ width: 150 }}
            allowClear
          >
            <Option value="执行中">执行中</Option>
            <Option value="已完成">已完成</Option>
            <Option value="已终止">已终止</Option>
          </Select>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={filteredProjects}
        rowKey="id"
        loading={isLoading}
        pagination={{ pageSize: 20 }}
        scroll={{ x: 800 }}
        locale={{
          emptyText: (
            <Empty description="暂无项目数据" image={Empty.PRESENTED_IMAGE_SIMPLE}>
              <Button type="primary" onClick={handleCreate} disabled={!canCreateProject}>+ 新增第一条项目</Button>
            </Empty>
          )
        }}
      />
      <ProjectForm open={isDrawerOpen} onCancel={() => setIsDrawerOpen(false)} />
    </PageScaffold>
  );
};

export default ProjectListPage;