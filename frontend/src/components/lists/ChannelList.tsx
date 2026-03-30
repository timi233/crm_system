import React, { useEffect } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Option } = Select;
const { confirm } = Modal;

const ChannelList: React.FC = () => {
  const [channels, setChannels] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [isModalVisible, setIsModalVisible] = React.useState(false);
  const [editingChannel, setEditingChannel] = React.useState<any>(null);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const fetchChannels = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8001/channels', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setChannels(data);
      }
    } catch (error) {
      console.error('Failed to fetch channels:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChannels();
  }, []);

  const handleCreate = () => {
    setEditingChannel(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (channel: any) => {
    setEditingChannel(channel);
    form.setFieldsValue(channel);
    setIsModalVisible(true);
  };

  const handleDelete = (channelId: number) => {
    confirm({
      title: '确定删除该渠道吗？',
      content: '此操作不可恢复',
      onOk: async () => {
        try {
          const token = localStorage.getItem('token');
          await fetch(`http://localhost:8001/channels/${channelId}`, {
            method: 'DELETE',
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          fetchChannels();
        } catch (error) {
          console.error('Failed to delete channel:', error);
        }
      }
    });
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      const token = localStorage.getItem('token');
      
      if (editingChannel) {
        // Update existing channel
        await fetch(`http://localhost:8001/channels/${editingChannel.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(values)
        });
      } else {
        // Create new channel
        await fetch('http://localhost:8001/channels', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(values)
        });
      }
      
      setIsModalVisible(false);
      fetchChannels();
    } catch (error) {
      console.error('Failed to save channel:', error);
    }
  };

  const columns = [
    {
      title: '渠道编号',
      dataIndex: 'channel_code',
      key: 'channel_code',
    },
    {
      title: '渠道名称',
      dataIndex: 'channel_name',
      key: 'channel_name',
    },
    {
      title: '渠道类型',
      dataIndex: 'channel_type',
      key: 'channel_type',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
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
        <h2>渠道档案列表</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建渠道
        </Button>
      </div>
      
      <Table 
        columns={columns} 
        dataSource={channels} 
        loading={loading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />
      
      <Modal
        title={editingChannel ? '编辑渠道' : '新建渠道'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => setIsModalVisible(false)}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item 
            name="channel_name" 
            label="渠道名称" 
            rules={[{ required: true, message: '请输入渠道名称!' }]}
          >
            <Input />
          </Form.Item>
          
          <Form.Item 
            name="channel_type" 
            label="渠道类型" 
            rules={[{ required: true, message: '请选择渠道类型!' }]}
          >
            <Select>
              <Option value="经销商">经销商</Option>
              <Option value="代理商">代理商</Option>
              <Option value="直销">直销</Option>
              <Option value="电商">电商</Option>
              <Option value="其他">其他</Option>
            </Select>
          </Form.Item>
          
          <Form.Item name="status" label="状态">
            <Select>
              <Option value="active">活跃</Option>
              <Option value="inactive">停用</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ChannelList;