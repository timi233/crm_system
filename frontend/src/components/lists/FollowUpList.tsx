import React, { useEffect } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select, DatePicker } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';

const { Option } = Select;
const { confirm } = Modal;

const FollowUpList: React.FC = () => {
  const [followUps, setFollowUps] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [isModalVisible, setIsModalVisible] = React.useState(false);
  const [editingFollowUp, setEditingFollowUp] = React.useState<any>(null);
  const [form] = Form.useForm();

  const fetchFollowUps = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8001/follow-ups', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setFollowUps(data);
      }
    } catch (error) {
      console.error('Failed to fetch follow-ups:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFollowUps();
  }, []);

  const handleCreate = () => {
    setEditingFollowUp(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (followUp: any) => {
    setEditingFollowUp(followUp);
    form.setFieldsValue({
      ...followUp,
      follow_up_date: followUp.follow_up_date ? new Date(followUp.follow_up_date) : null,
    });
    setIsModalVisible(true);
  };

  const handleDelete = (followUpId: number) => {
    confirm({
      title: '确定删除该跟进记录吗？',
      content: '此操作不可恢复',
      onOk: async () => {
        try {
          const token = localStorage.getItem('token');
          await fetch(`http://localhost:8001/follow-ups/${followUpId}`, {
            method: 'DELETE',
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          fetchFollowUps();
        } catch (error) {
          console.error('Failed to delete follow-up:', error);
        }
      }
    });
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      const token = localStorage.getItem('token');
      
      // Convert date to ISO string
      const payload = {
        ...values,
        follow_up_date: values.follow_up_date?.toISOString(),
      };
      
      if (editingFollowUp) {
        // Update existing follow-up
        await fetch(`http://localhost:8001/follow-ups/${editingFollowUp.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(payload)
        });
      } else {
        // Create new follow-up
        await fetch('http://localhost:8001/follow-ups', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(payload)
        });
      }
      
      setIsModalVisible(false);
      fetchFollowUps();
    } catch (error) {
      console.error('Failed to save follow-up:', error);
    }
  };

  const columns = [
    {
      title: '终端客户',
      dataIndex: 'terminal_customer_id',
      key: 'terminal_customer_id',
      render: (customerId: number) => `客户 ID: ${customerId}`,
    },
    {
      title: '跟进人',
      dataIndex: 'follower_id',
      key: 'follower_id',
      render: (followerId: number) => `用户 ID: ${followerId}`,
    },
    {
      title: '跟进日期',
      dataIndex: 'follow_up_date',
      key: 'follow_up_date',
      render: (date: string) => date ? new Date(date).toLocaleDateString() : '-',
    },
    {
      title: '跟进方式',
      dataIndex: 'follow_up_method',
      key: 'follow_up_method',
    },
    {
      title: '跟进内容',
      dataIndex: 'follow_up_content',
      key: 'follow_up_content',
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
        <h2>跟进记录列表</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建跟进
        </Button>
      </div>
      
      <Table 
        columns={columns} 
        dataSource={followUps} 
        loading={loading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />
      
      <Modal
        title={editingFollowUp ? '编辑跟进记录' : '新建跟进记录'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => setIsModalVisible(false)}
        okText="保存"
        cancelText="取消"
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item 
            name="terminal_customer_id" 
            label="终端客户ID" 
            rules={[{ required: true, message: '请输入终端客户ID!' }]}
          >
            <Input type="number" />
          </Form.Item>
          
          <Form.Item 
            name="follower_id" 
            label="跟进人ID" 
            rules={[{ required: true, message: '请输入跟进人ID!' }]}
          >
            <Input type="number" />
          </Form.Item>
          
          <Form.Item 
            name="follow_up_method" 
            label="跟进方式" 
            rules={[{ required: true, message: '请选择跟进方式!' }]}
          >
            <Select>
              <Option value="电话">电话</Option>
              <Option value="邮件">邮件</Option>
              <Option value="面对面">面对面</Option>
              <Option value="微信">微信</Option>
              <Option value="其他">其他</Option>
            </Select>
          </Form.Item>
          
          <Form.Item name="follow_up_date" label="跟进日期">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          
          <Form.Item name="follow_up_content" label="跟进内容">
            <Input.TextArea rows={4} />
          </Form.Item>
          
          <Form.Item name="next_follow_up_date" label="下次跟进日期">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default FollowUpList;