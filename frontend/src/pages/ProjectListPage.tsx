import React, { useState } from 'react';
import { App, Button, Card, Table, Space, Input, Select, Tag, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import type { RootState } from '../store/store';
import { useProjects, useDeleteProject, Project } from '../hooks/useProjects';
import ProjectDrawer from '../components/modals/ProjectDrawer';

const { Search } = Input;
const { Option } = Select;

const ProjectListPage: React.FC = () => {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const { capabilities } = useSelector((state: RootState) => state.auth);
  
  const [searchText, setSearchText] = useState('');
  const [filters, setFilters] = useState({ status: 'all' });
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);

  const { data: projects = [], isLoading, refetch } = useProjects();
  const deleteMutation = useDeleteProject();

  const canManage = Boolean(capabilities['project:manage']);

  const filteredProjects = projects.filter(project => {
    const matchesSearch = !searchText || 
      project.project_name.toLowerCase().includes(searchText.toLowerCase()) ||
      project.project_code.toLowerCase().includes(searchText.toLowerCase());
    const matchesStatus = filters.status === 'all' || project.project_status === filters.status;
    return matchesSearch && matchesStatus;
  });

  const handleCreate = () => {
    setEditingProject(null);
    setDrawerVisible(true);
  };

  const handleEdit = (project: Project) => {
    setEditingProject(project);
    setDrawerVisible(true);
  };

  const handleDelete = async (projectId: number, projectName: string) => {
    try {
      await deleteMutation.mutateAsync(projectId);
      message.success(`项目 ${projectName} 已删除`);
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  const handleSave = async (projectData: any) => {
    setDrawerVisible(false);
    refetch();
    message.success(editingProject ? '项目更新成功' : '项目创建成功');
  };

  const columns = [
    {
      title: '项目编号',
      dataIndex: 'project_code',
      key: 'project_code',
      width: 120,
    },
    {
      title: '项目名称',
      dataIndex: 'project_name',
      key: 'project_name',
      render: (text: string, record: Project) => (
        <a onClick={() => navigate(`/projects/${record.id}`)}>{text}</a>
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
        <Tag color={status === '执行中' ? 'blue' : status === '已完成' ? 'green' : 'default'}>
          {status}
        </Tag>
      ),
    },
    {
      title: '负责人',
      dataIndex: 'sales_owner_name',
      key: 'sales_owner_name',
      width: 120,
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
      key: 'actions',
      width: 180,
      render: (_: any, record: Project) => (
        <Space size="middle">
          <Button 
            icon={<EyeOutlined />} 
            size="small" 
            onClick={() => navigate(`/projects/${record.id}`)}
          >
            查看
          </Button>
          {canManage && (
            <>
              <Button 
                icon={<EditOutlined />} 
                size="small" 
                onClick={() => handleEdit(record)}
              >
                编辑
              </Button>
              <Popconfirm
                title={`确定要删除项目 "${record.project_name}" 吗？`}
                onConfirm={() => handleDelete(record.id, record.project_name)}
                okText="确定"
                cancelText="取消"
              >
                <Button icon={<DeleteOutlined />} size="small" danger>
                  删除
                </Button>
              </Popconfirm>
            </>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title="项目管理"
        extra={
          canManage && (
            <Button 
              type="primary" 
              icon={<PlusOutlined />} 
              onClick={handleCreate}
            >
              新建项目
            </Button>
          )
        }
      >
        <div style={{ marginBottom: 16, display: 'flex', gap: 16 }}>
          <Search
            placeholder="搜索项目名称或编号"
            allowClear
            onSearch={setSearchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 300 }}
          />
          <Select
            value={filters.status}
            onChange={(value) => setFilters({ ...filters, status: value })}
            style={{ width: 150 }}
          >
            <Option value="all">全部状态</Option>
            <Option value="执行中">执行中</Option>
            <Option value="已完成">已完成</Option>
            <Option value="已终止">已终止</Option>
          </Select>
        </div>
        
        <Table
          columns={columns}
          dataSource={filteredProjects}
          loading={isLoading}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1000 }}
        />
      </Card>

      <ProjectDrawer
        visible={drawerVisible}
        project={editingProject}
        onSave={handleSave}
        onCancel={() => setDrawerVisible(false)}
      />
    </div>
  );
};

export default ProjectListPage;