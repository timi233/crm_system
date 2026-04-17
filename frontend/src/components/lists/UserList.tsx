import React, { useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select, Card, Tag, Drawer } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useUsers, useCreateUser, useUpdateUser, useDeleteUser } from '../../hooks/useUsers';
import { useDictItems } from '../../hooks/useDictItems';

const { Option } = Select;
const { Search } = Input;
const { confirm } = Modal;

const UserList: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<any>(null);
  const [searchText, setSearchText] = useState('');
  const [roleFilter, setRoleFilter] = useState<string | null>(null);
  const [form] = Form.useForm();

  const { data: users = [], isLoading } = useUsers();
  const { data: regionItems = [] } = useDictItems('地区');
  const { data: brandItems = [] } = useDictItems('产品品牌');
  
  // 获取地区市级选项（地区是二级树，只取市级）
  const regionOptions = regionItems
    .filter(item => item.parent_id !== null) // 只取市级（有parent_id的）
    .map(item => ({ value: item.name, label: item.name }));
  
  // 获取产品品牌选项
  const brandOptions = brandItems.map(item => ({ value: item.name, label: item.name }));
  
  // Filter users based on search and filters
  const filteredUsers = users.filter(user => {
    const matchesSearch = !searchText ||
      user.name?.toLowerCase().includes(searchText.toLowerCase()) ||
      user.email?.toLowerCase().includes(searchText.toLowerCase());

    const matchesRole = !roleFilter || user.role === roleFilter;

    return matchesSearch && matchesRole;
  });
  
  const roleOptions: string[] = Array.from(
    new Set(users.map((u: any) => u.role))
  ).sort() as string[];
  
  const createMutation = useCreateUser();
  const updateMutation = useUpdateUser();
  const deleteMutation = useDeleteUser();

  const handleCreate = () => {
    setEditingUser(null);
    form.resetFields();
    form.setFieldsValue({ sales_region: [], sales_product_line: [] });
    setIsModalVisible(true);
  };

  const handleEdit = (user: any) => {
    setEditingUser(user);
    form.setFieldsValue({
      ...user,
      sales_region: user.sales_region ? user.sales_region.split(',').map(r => r.trim()) : [],
      sales_product_line: user.sales_product_line ? user.sales_product_line.split(',').map(p => p.trim()) : [],
    });
    setIsModalVisible(true);
  };

  const handleDelete = (userId: number) => {
    confirm({
      title: '确定删除该用户吗？',
      content: '此操作不可恢复',
      onOk: async () => {
        try {
          await deleteMutation.mutateAsync(userId);
        } catch (error) {
          console.error('Failed to delete user:', error);
        }
      }
    });
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      const submitData = {
        ...values,
        sales_region: values.sales_region?.join(',') || null,
        sales_product_line: values.sales_product_line?.join(',') || null,
      };
      
      if (editingUser) {
        await updateMutation.mutateAsync({ id: editingUser.id, user: submitData });
      } else {
        await createMutation.mutateAsync(submitData);
      }
      
      setIsModalVisible(false);
      form.resetFields();
    } catch (error) {
      console.error('Failed to save user:', error);
    }
  };

  const columns = [
    {
      title: '用户名',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
    },
    {
      title: '销售主管',
      dataIndex: 'sales_leader_id',
      key: 'sales_leader_id',
      render: (leaderId: number) => leaderId ? `用户 ID: ${leaderId}` : '-',
    },
    {
      title: '销售区域',
      dataIndex: 'sales_region',
      key: 'sales_region',
      render: (regions: string) => {
        if (!regions) return '-';
        const regionList = regions.split(',').map(r => r.trim());
        return (
          <Space size={[0, 4]} wrap>
            {regionList.map(region => (
              <Tag key={region} color="blue">{region}</Tag>
            ))}
          </Space>
        );
      },
    },
    {
      title: '销售产品线',
      dataIndex: 'sales_product_line',
      key: 'sales_product_line',
      render: (productLines: string) => {
        if (!productLines) return '-';
        const productList = productLines.split(',').map(p => p.trim());
        return (
          <Space size={[0, 4]} wrap>
            {productList.map(product => (
              <Tag key={product} color="green">{product}</Tag>
            ))}
          </Space>
        );
      },
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
    <Card
      title="用户管理列表"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建用户
        </Button>
      }
    >
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Search
            placeholder="搜索用户名或邮箱"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 200 }}
          />
          <Select
            placeholder="筛选角色"
            value={roleFilter}
            onChange={setRoleFilter}
            style={{ width: 150 }}
            allowClear
          >
            {roleOptions.map(role => (
              <Option key={role} value={role}>
                {role}
              </Option>
            ))}
          </Select>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={filteredUsers}
        loading={isLoading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />
      
      <Drawer
        title={editingUser ? '编辑用户' : '新建用户'}
        open={isModalVisible}
        onClose={() => setIsModalVisible(false)}
        width={520}
        maskClosable={false}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item 
            name="name" 
            label="用户名" 
            rules={[{ required: true, message: '请输入用户名!' }]}
          >
            <Input />
          </Form.Item>
          
          <Form.Item 
            name="email" 
            label="邮箱" 
            rules={[
              { required: true, message: '请输入邮箱!' },
              { type: 'email', message: '请输入有效的邮箱地址!' }
            ]}
          >
            <Input />
          </Form.Item>
          
          {!editingUser && (
            <Form.Item 
              name="password" 
              label="密码" 
              rules={[{ required: true, message: '请输入密码!' }]}
            >
              <Input.Password />
            </Form.Item>
          )}
          
          <Form.Item 
            name="role" 
            label="角色" 
            rules={[{ required: true, message: '请选择角色!' }]}
          >
            <Select>
              <Option value="admin">管理员</Option>
              <Option value="sales">销售</Option>
              <Option value="business">商务</Option>
              <Option value="finance">财务</Option>
            </Select>
          </Form.Item>
          
          <Form.Item name="sales_leader_id" label="销售主管 ID">
            <Input type="number" placeholder="仅销售角色需要填写" />
          </Form.Item>
          
          <Form.Item name="sales_region" label="销售区域">
            <Select
              mode="multiple"
              placeholder="选择负责的销售区域"
              allowClear
            >
              {regionOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item name="sales_product_line" label="销售产品线">
            <Select
              mode="multiple"
              placeholder="选择负责的产品线"
              allowClear
            >
              {brandOptions.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item>
            <Button type="primary" onClick={handleModalOk} loading={createMutation.isPending || updateMutation.isPending} block>
              保存
            </Button>
          </Form.Item>
        </Form>
      </Drawer>
    </Card>
  );
};

export default UserList;
