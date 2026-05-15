import React, { useState } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select, Card, Tag, Row, Col, App } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useSelector } from 'react-redux';
import { RootState } from '../../store/store';
import { useUsers, useCreateUser, useUpdateUser, useDeleteUser, User } from '../../hooks/useUsers';
import PageScaffold from '../../components/common/PageScaffold';
import PageModal from '../../components/common/PageModal';

const { Option } = Select;

const UserList: React.FC = () => {
  const { message, modal } = App.useApp();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [searchText, setSearchText] = useState('');
  const [roleFilter, setRoleFilter] = useState<string | null>(null);
  const [form] = Form.useForm();

  const { data: users = [], isLoading } = useUsers();
  const { capabilities } = useSelector((state: RootState) => state.auth);
  const canManageUsers = Boolean(capabilities['user:manage']);

  const createMutation = useCreateUser();
  const updateMutation = useUpdateUser();
  const deleteMutation = useDeleteUser();

  const roleOptions = ['admin', 'sales', 'sales_manager', 'finance', 'delivery'];

  const filteredUsers = users.filter(user => {
    const matchesSearch = !searchText ||
      user.name.toLowerCase().includes(searchText.toLowerCase()) ||
      user.email.toLowerCase().includes(searchText.toLowerCase());
    const matchesRole = !roleFilter || user.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  const handleCreate = () => {
    setEditingUser(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (user: User) => {
    setEditingUser(user);
    form.setFieldsValue(user);
    setIsModalVisible(true);
  };

  const handleDelete = (id: number) => {
    modal.confirm({
      title: '确定删除该用户吗？',
      content: '此操作不可恢复',
      okType: 'danger',
      onOk: async () => {
        try {
          await deleteMutation.mutateAsync(id);
          message.success('用户已删除');
        } catch (error) {}
      }
    });
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      if (editingUser) {
        await updateMutation.mutateAsync({ id: editingUser.id, user: values });
        message.success('用户信息已更新');
      } else {
        await createMutation.mutateAsync(values);
        message.success('用户已创建');
      }
      setIsModalVisible(false);
      form.resetFields();
    } catch (error) {}
  };

  const columns = [
    {
      title: '姓名',
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
      render: (role: string) => <Tag color="blue" style={{ border: 'none' }}>{role}</Tag>,
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: User) => (
        <Space size="middle">
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)}>删除</Button>
        </Space>
      ),
    },
  ];

  return (
    <PageScaffold
      title="用户管理"
      breadcrumbItems={[{ title: '首页' }, { title: '用户管理' }]}
      extra={
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleCreate}
          disabled={!canManageUsers}
          size="large"
          className="btn--gradient"
          style={{ height: '40px', padding: '0 20px' }}
        >
          新建用户
        </Button>
      }
      filters={
        <Space size={16} wrap>
          <Input.Search
            placeholder="搜索用户名或邮箱"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 280 }}
            size="middle"
          />
          <Select
            placeholder="筛选角色"
            value={roleFilter}
            onChange={setRoleFilter}
            style={{ width: 180 }}
            allowClear
          >
            {roleOptions.map(role => (
              <Option key={role} value={role}>{role}</Option>
            ))}
          </Select>
        </Space>
      }
    >
      <Table
        columns={columns}
        dataSource={filteredUsers}
        loading={isLoading}
        rowKey="id"
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条数据`,
        }}
        className="customer-table"
        bordered={false}
      />

      <PageModal
        title={editingUser ? '编辑用户信息' : '建立新用户账号'}
        open={isModalVisible}
        onClose={() => setIsModalVisible(false)}
        width={560}
        footer={[
          <Button key="cancel" onClick={() => setIsModalVisible(false)}>
            取消
          </Button>,
          <Button
            key="submit"
            type="primary"
            className="btn--gradient"
            onClick={handleSave}
            loading={createMutation.isPending || updateMutation.isPending}
          >
            确认并保存
          </Button>
        ]}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="真实姓名"
            rules={[{ required: true, message: '请输入姓名!' }]}
          >
            <Input placeholder="输入员工真实姓名" />
          </Form.Item>

          <Form.Item
            name="email"
            label="电子邮箱"
            rules={[{ required: true, message: '请输入邮箱!' }, { type: 'email', message: '格式不正确' }]}
          >
            <Input placeholder="员工企业邮箱地址" />
          </Form.Item>

          {!editingUser && (
            <Form.Item
              name="password"
              label="登录密码"
              rules={[{ required: true, message: '请输入初始密码!' }]}
            >
              <Input.Password placeholder="设置初始登录密码" />
            </Form.Item>
          )}

          <Form.Item
            name="role"
            label="系统角色"
            rules={[{ required: true, message: '请选择角色!' }]}
          >
            <Select placeholder="分配系统访问权限">
              {roleOptions.map(role => (
                <Option key={role} value={role}>{role}</Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </PageModal>
    </PageScaffold>
  );
};

export default UserList;
