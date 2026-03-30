import React, { useEffect } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';

const { Option } = Select;
const { confirm } = Modal;

const ContractList: React.FC = () => {
  const [contracts, setContracts] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [isModalVisible, setIsModalVisible] = React.useState(false);
  const [editingContract, setEditingContract] = React.useState<any>(null);
  const [form] = Form.useForm();

  const fetchContracts = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8001/contracts', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setContracts(data);
      }
    } catch (error) {
      console.error('Failed to fetch contracts:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContracts();
  }, []);

  const handleCreate = () => {
    setEditingContract(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (contract: any) => {
    setEditingContract(contract);
    form.setFieldsValue(contract);
    setIsModalVisible(true);
  };

  const handleDelete = (contractId: number) => {
    confirm({
      title: '确定删除该合同吗？',
      content: '此操作不可恢复',
      onOk: async () => {
        try {
          const token = localStorage.getItem('token');
          await fetch(`http://localhost:8001/contracts/${contractId}`, {
            method: 'DELETE',
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          fetchContracts();
        } catch (error) {
          console.error('Failed to delete contract:', error);
        }
      }
    });
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      const token = localStorage.getItem('token');
      
      if (editingContract) {
        // Update existing contract
        await fetch(`http://localhost:8001/contracts/${editingContract.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(values)
        });
      } else {
        // Create new contract
        await fetch('http://localhost:8001/contracts', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(values)
        });
      }
      
      setIsModalVisible(false);
      fetchContracts();
    } catch (error) {
      console.error('Failed to save contract:', error);
    }
  };

  const columns = [
    {
      title: '合同编号',
      dataIndex: 'contract_code',
      key: 'contract_code',
    },
    {
      title: '项目ID',
      dataIndex: 'project_id',
      key: 'project_id',
      render: (projectId: number) => `项目 ID: ${projectId}`,
    },
    {
      title: '合同方向',
      dataIndex: 'contract_direction',
      key: 'contract_direction',
    },
    {
      title: '合同金额',
      dataIndex: 'contract_amount',
      key: 'contract_amount',
      render: (amount: number) => amount?.toLocaleString() || '-',
    },
    {
      title: '签约日期',
      dataIndex: 'signed_date',
      key: 'signed_date',
      render: (date: string) => date ? new Date(date).toLocaleDateString() : '-',
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
        <h2>合同管理列表</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建合同
        </Button>
      </div>
      
      <Table 
        columns={columns} 
        dataSource={contracts} 
        loading={loading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />
      
      <Modal
        title={editingContract ? '编辑合同' : '新建合同'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => setIsModalVisible(false)}
        okText="保存"
        cancelText="取消"
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item 
            name="project_id" 
            label="项目ID" 
            rules={[{ required: true, message: '请输入项目ID!' }]}
          >
            <Input type="number" />
          </Form.Item>
          
          <Form.Item 
            name="contract_direction" 
            label="合同方向" 
            rules={[{ required: true, message: '请选择合同方向!' }]}
          >
            <Select>
              <Option value="Downstream">下游合同</Option>
              <Option value="Upstream">上游合同</Option>
            </Select>
          </Form.Item>
          
          <Form.Item name="counterparty_id" label="交易对手ID">
            <Input type="number" />
          </Form.Item>
          
          <Form.Item name="contract_amount" label="合同金额">
            <Input type="number" />
          </Form.Item>
          
          <Form.Item name="signed_date" label="签约日期">
            <Input type="date" />
          </Form.Item>
          
          <Form.Item name="description" label="合同描述">
            <Input.TextArea rows={4} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ContractList;