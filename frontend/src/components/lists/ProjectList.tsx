import React, { useEffect } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select, DatePicker } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';

const { Option } = Select;
const { confirm } = Modal;

const ProjectList: React.FC = () => {
  const [projects, setProjects] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [isModalVisible, setIsModalVisible] = React.useState(false);
  const [editingProject, setEditingProject] = React.useState<any>(null);
  const [form] = Form.useForm();

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8001/projects', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setProjects(data);
      }
    } catch (error) {
      console.error('Failed to fetch projects:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

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

  const handleDelete = (projectId: number) => {
    confirm({
      title: '确定删除该项目吗？',
      content: '此操作不可恢复',
      onOk: async () => {
        try {
          const token = localStorage.getItem('token');
          await fetch(`http://localhost:8001/projects/${projectId}`, {
            method: 'DELETE',
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          fetchProjects();
        } catch (error) {
          console.error('Failed to delete project:', error);
        }
      }
    });
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      const token = localStorage.getItem('token');
      
      if (editingProject) {
        // Update existing project
        await fetch(`http://localhost:8001/projects/${editingProject.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(values)
        });
      } else {
        // Create new project
        await fetch('http://localhost:8001/projects', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(values)
        });
      }
      
      setIsModalVisible(false);
      fetchProjects();
    } catch (error) {
      console.error('Failed to save project:', error);
    }
  };

  const columns = [
    {
      title: '项目编号',
      dataIndex: 'project_code',
      key: 'project_code',
    },
    {
      title: '项目名称',
      dataIndex: 'project_name',
      key: 'project_name',
    },
    {
      title: '终端客户',
      dataIndex: 'terminal_customer_id',
      key: 'terminal_customer_id',
      render: (customerId: number) => `客户 ID: ${customerId}`,
    },
    {
      title: '销售负责人',
      dataIndex: 'sales_owner_id',
      key: 'sales_owner_id',
      render: (ownerId: number) => `销售 ID: ${ownerId}`,
    },
    {
      title: '业务类型',
      dataIndex: 'business_type',
      key: 'business_type',
    },
    {
      title: '下游合同金额',
      dataIndex: 'downstream_contract_amount',
      key: 'downstream_contract_amount',
      render: (amount: number) => amount?.toLocaleString() || '-',
    },
    {
      title: '毛利率',
      dataIndex: 'gross_margin',
      key: 'gross_margin',
      render: (margin: number) => margin?.toLocaleString() || '-',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space size="middle">
          <Button icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Button icon={<DeleteOutlined />} danger onClick={() => handleDelete(record.id)}>
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2>项目管理列表</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建项目
        </Button>
      </div>
      
      <Table 
        columns={columns} 
        dataSource={projects} 
        loading={loading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />
      
      <Modal
        title={editingProject ? '编辑项目' : '新建项目'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => setIsModalVisible(false)}
        okText="保存"
        cancelText="取消"
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item 
            name="project_name" 
            label="项目名称" 
            rules={[{ required: true, message: '请输入项目名称!' }]}
          >
            <Input />
          </Form.Item>
          
          <Form.Item 
            name="terminal_customer_id" 
            label="终端客户 ID" 
            rules={[{ required: true, message: '请输入终端客户 ID!' }]}
          >
            <Input type="number" />
          </Form.Item>
          
          <Form.Item 
            name="sales_owner_id" 
            label="销售负责人 ID" 
            rules={[{ required: true, message: '请输入销售负责人 ID!' }]}
          >
            <Input type="number" />
          </Form.Item>
          
          <Form.Item 
            name="business_type" 
            label="业务类型" 
            rules={[{ required: true, message: '请选择业务类型!' }]}
          >
            <Select>
              <Option value="New Project">新项目</Option>
              <Option value="Renewal/Maintenance">续费项目-SVC</Option>
              <Option value="Expansion">增购项目</Option>
              <Option value="Additional Purchase">其他</Option>
            </Select>
          </Form.Item>
          
          <Form.Item name="downstream_contract_amount" label="下游合同金额">
            <Input type="number" />
          </Form.Item>
          
          <Form.Item name="upstream_procurement_amount" label="上游采购金额">
            <Input type="number" />
          </Form.Item>
          
          <Form.Item name="description" label="项目描述">
            <Input.TextArea rows={4} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ProjectList;