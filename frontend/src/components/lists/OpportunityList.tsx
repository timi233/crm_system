import React, { useEffect } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select, DatePicker } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import type { Dayjs } from 'dayjs';

const { Option } = Select;
const { RangePicker } = DatePicker;
const { confirm } = Modal;

const OpportunityList: React.FC = () => {
  const [opportunities, setOpportunities] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [isModalVisible, setIsModalVisible] = React.useState(false);
  const [editingOpportunity, setEditingOpportunity] = React.useState<any>(null);
  const [form] = Form.useForm();

  const fetchOpportunities = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8001/opportunities', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setOpportunities(data);
      }
    } catch (error) {
      console.error('Failed to fetch opportunities:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOpportunities();
  }, []);

  const handleCreate = () => {
    setEditingOpportunity(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (opportunity: any) => {
    setEditingOpportunity(opportunity);
    form.setFieldsValue({
      ...opportunity,
      created_at: opportunity.created_at ? new Date(opportunity.created_at) : null,
      estimated_close_date: opportunity.estimated_close_date ? new Date(opportunity.estimated_close_date) : null,
    });
    setIsModalVisible(true);
  };

  const handleDelete = (opportunityId: number) => {
    confirm({
      title: '确定删除该商机吗？',
      content: '此操作不可恢复',
      onOk: async () => {
        try {
          const token = localStorage.getItem('token');
          await fetch(`http://localhost:8001/opportunities/${opportunityId}`, {
            method: 'DELETE',
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          fetchOpportunities();
        } catch (error) {
          console.error('Failed to delete opportunity:', error);
        }
      }
    });
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      const token = localStorage.getItem('token');
      
      // Convert dates to ISO strings
      const payload = {
        ...values,
        created_at: values.created_at?.toISOString(),
        estimated_close_date: values.estimated_close_date?.toISOString(),
      };
      
      if (editingOpportunity) {
        // Update existing opportunity
        await fetch(`http://localhost:8001/opportunities/${editingOpportunity.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(payload)
        });
      } else {
        // Create new opportunity
        await fetch('http://localhost:8001/opportunities', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(payload)
        });
      }
      
      setIsModalVisible(false);
      fetchOpportunities();
    } catch (error) {
      console.error('Failed to save opportunity:', error);
    }
  };

  const columns = [
    {
      title: '商机编号',
      dataIndex: 'opportunity_code',
      key: 'opportunity_code',
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
      title: '商机阶段',
      dataIndex: 'stage',
      key: 'stage',
    },
    {
      title: '预计金额',
      dataIndex: 'estimated_value',
      key: 'estimated_value',
      render: (value: number) => value?.toLocaleString() || '-',
    },
    {
      title: '预计关闭日期',
      dataIndex: 'estimated_close_date',
      key: 'estimated_close_date',
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
        <h2>商机管理列表</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建商机
        </Button>
      </div>
      
      <Table 
        columns={columns} 
        dataSource={opportunities} 
        loading={loading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />
      
      <Modal
        title={editingOpportunity ? '编辑商机' : '新建商机'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => setIsModalVisible(false)}
        okText="保存"
        cancelText="取消"
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item 
            name="title" 
            label="商机标题" 
            rules={[{ required: true, message: '请输入商机标题!' }]}
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
            name="stage" 
            label="商机阶段" 
            rules={[{ required: true, message: '请选择商机阶段!' }]}
          >
            <Select>
              <Option value="初步接触">初步接触</Option>
              <Option value="需求分析">需求分析</Option>
              <Option value="方案设计">方案设计</Option>
              <Option value="报价谈判">报价谈判</Option>
              <Option value="合同签署">合同签署</Option>
              <Option value="已关闭-赢">已关闭-赢</Option>
              <Option value="已关闭-输">已关闭-输</Option>
            </Select>
          </Form.Item>
          
          <Form.Item name="estimated_value" label="预计金额">
            <Input type="number" />
          </Form.Item>
          
          <Form.Item name="estimated_close_date" label="预计关闭日期">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          
          <Form.Item name="description" label="商机描述">
            <Input.TextArea rows={4} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default OpportunityList;