import React, { useState, useMemo } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select, Card, Tag, InputNumber, Switch, Cascader, Drawer } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useDictItems, useDictTypes, useCreateDictItem, useUpdateDictItem, useDeleteDictItem, DictItem, DictItemCreate } from '../../hooks/useDictItems';

const { Option } = Select;
const { Search } = Input;
const { confirm } = Modal;

interface TreeNode {
  key: string;
  id?: number;
  dict_type?: string;
  code?: string;
  name: string;
  parent_id?: number | null;
  sort_order?: number;
  is_active?: boolean;
  children?: TreeNode[];
  isTypeNode?: boolean;
}

const DictItemList: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingItem, setEditingItem] = useState<DictItem | null>(null);
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [searchText, setSearchText] = useState('');
  const [form] = Form.useForm();

  const { data: dictTypes = [] } = useDictTypes();
  const { data: items = [], isLoading } = useDictItems(selectedType || undefined);
  
  const createMutation = useCreateDictItem();
  const updateMutation = useUpdateDictItem();
  const deleteMutation = useDeleteDictItem();

  const buildTreeByType = (items: DictItem[], types: string[]): TreeNode[] => {
    const result: TreeNode[] = [];
    
    types.forEach(type => {
      const typeItems = items.filter(i => i.dict_type === type);
      if (typeItems.length === 0) return;
      
      const typeNode: TreeNode = {
        key: `type-${type}`,
        name: type,
        isTypeNode: true,
        children: [],
      };
      
      const itemMap = new Map<number, TreeNode>();
      const roots: TreeNode[] = [];

      typeItems.forEach(item => {
        itemMap.set(item.id, { 
          key: `item-${item.id}`,
          id: item.id,
          dict_type: item.dict_type,
          code: item.code,
          name: item.name,
          parent_id: item.parent_id,
          sort_order: item.sort_order,
          is_active: item.is_active,
          children: [],
        });
      });

      typeItems.forEach(item => {
        const node = itemMap.get(item.id)!;
        if (item.parent_id === null) {
          roots.push(node);
        } else {
          const parent = itemMap.get(item.parent_id);
          if (parent) {
            parent.children = parent.children || [];
            parent.children.push(node);
          }
        }
      });

      const sortChildren = (nodes: TreeNode[]) => {
        nodes.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
        nodes.forEach(node => {
          if (node.children && node.children.length > 0) {
            sortChildren(node.children);
          }
        });
      };
      sortChildren(roots);

      typeNode.children = roots;
      result.push(typeNode);
    });
    
    return result;
  };

  const treeData = useMemo(() => buildTreeByType(items, dictTypes), [items, dictTypes]);

  const filteredTreeData = useMemo(() => {
    if (!searchText) return treeData;
    
    const filterTree = (nodes: TreeNode[]): TreeNode[] => {
      return nodes.reduce((acc: TreeNode[], node) => {
        if (node.isTypeNode) {
          const filteredChildren = node.children ? filterTree(node.children) : [];
          if (filteredChildren.length > 0) {
            acc.push({
              ...node,
              children: filteredChildren,
            });
          }
        } else {
          const matchesSearch = 
            node.name?.toLowerCase().includes(searchText.toLowerCase()) ||
            node.code?.toLowerCase().includes(searchText.toLowerCase());
          
          const filteredChildren = node.children ? filterTree(node.children) : [];
          
          if (matchesSearch || filteredChildren.length > 0) {
            acc.push({
              ...node,
              children: filteredChildren.length > 0 ? filteredChildren : node.children,
            });
          }
        }
        
        return acc;
      }, []);
    };
    
    return filterTree(treeData);
  }, [treeData, searchText]);

  const parentOptions = useMemo(() => {
    const buildOptions = (items: DictItem[], level = 0): { value: number; label: string }[] => {
      return items.flatMap(item => {
        const prefix = '　'.repeat(level);
        const options: { value: number; label: string }[] = [
          { value: item.id, label: `${prefix}${item.name}` }
        ];
        const children = items.filter(i => i.parent_id === item.id);
        if (children.length > 0) {
          options.push(...buildOptions(children, level + 1));
        }
        return options;
      });
    };
    
    const rootItems = items.filter(i => i.parent_id === null);
    return buildOptions(rootItems);
  }, [items]);

  const handleCreate = () => {
    setEditingItem(null);
    form.resetFields();
    form.setFieldsValue({ 
      dict_type: selectedType,
      is_active: true,
      sort_order: 0,
    });
    setIsModalVisible(true);
  };

  const handleEdit = (item: DictItem) => {
    setEditingItem(item);
    form.setFieldsValue(item);
    setIsModalVisible(true);
  };

  const handleDelete = (itemId: number) => {
    const hasChildren = items.some(i => i.parent_id === itemId);
    if (hasChildren) {
      Modal.warning({
        title: '无法删除',
        content: '该字典项下有子项，请先删除子项',
      });
      return;
    }
    
    confirm({
      title: '确定删除该字典项吗？',
      content: '此操作不可恢复',
      onOk: async () => {
        await deleteMutation.mutateAsync(itemId);
      }
    });
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingItem) {
        await updateMutation.mutateAsync({ id: editingItem.id, item: values });
      } else {
        await createMutation.mutateAsync(values as DictItemCreate);
      }
      
      setIsModalVisible(false);
      form.resetFields();
    } catch (error) {
      console.error('Failed to save dict item:', error);
    }
  };

  const getLevelTag = (level: number) => {
    const colors = ['gold', 'green', 'blue', 'purple', 'cyan'];
    const labels = ['一级', '二级', '三级', '四级', '五级'];
    return <Tag color={colors[level] || 'default'}>{labels[level] || `${level+1}级`}</Tag>;
  };

  const columns = [
    {
      title: '编码',
      dataIndex: 'code',
      key: 'code',
      width: 150,
      render: (code: string, record: TreeNode) => {
        if (record.isTypeNode) return '-';
        return code || '-';
      },
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (name: string, record: TreeNode) => {
        if (record.isTypeNode) {
          return <strong style={{ fontSize: 15 }}>{name}</strong>;
        }
        return name;
      },
    },
    {
      title: '层级',
      key: 'level',
      width: 80,
      render: (_: any, record: TreeNode) => {
        if (record.isTypeNode) return <Tag color="magenta">字典类型</Tag>;
        let level = 0;
        let currentId: number | undefined = record.parent_id;
        while (currentId) {
          level++;
          const parent = items.find(i => i.id === currentId);
          currentId = parent?.parent_id;
        }
        return getLevelTag(level);
      },
    },
    {
      title: '排序',
      dataIndex: 'sort_order',
      key: 'sort_order',
      width: 60,
      render: (order: number, record: TreeNode) => {
        if (record.isTypeNode) return '-';
        return order;
      },
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (active: boolean, record: TreeNode) => {
        if (record.isTypeNode) return '-';
        return <Tag color={active ? 'green' : 'red'}>{active ? '启用' : '禁用'}</Tag>;
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: TreeNode) => {
        if (record.isTypeNode) return '-';
        return (
          <Space size="small">
            <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record as unknown as DictItem)}>
              编辑
            </Button>
            <Button size="small" icon={<DeleteOutlined />} danger onClick={() => handleDelete(record.id!)}>
              删除
            </Button>
          </Space>
        );
      },
    },
  ];

  return (
    <Card
      title="数据字典管理"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建字典项
        </Button>
      }
    >
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Select
            placeholder="选择字典类型"
            value={selectedType}
            onChange={setSelectedType}
            style={{ width: 150 }}
            allowClear
          >
            {dictTypes.map(type => (
              <Option key={type} value={type}>{type}</Option>
            ))}
          </Select>
          <Search
            placeholder="搜索编码或名称"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 200 }}
            allowClear
          />
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={filteredTreeData}
        rowKey="key"
        loading={isLoading}
        pagination={false}
        defaultExpandAllRows
        indentSize={20}
        scroll={{ x: 750 }}
      />

      <Drawer
        title={editingItem ? '编辑字典项' : '新建字典项'}
        open={isModalVisible}
        onClose={() => setIsModalVisible(false)}
        width={520}
        maskClosable={false}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="dict_type"
            label="字典类型"
            rules={[{ required: true, message: '请输入字典类型!' }]}
          >
            {editingItem ? (
              <Input disabled />
            ) : (
              <Select placeholder="选择或输入字典类型" allowClear showSearch>
                {dictTypes.map(type => (
                  <Option key={type} value={type}>{type}</Option>
                ))}
              </Select>
            )}
          </Form.Item>
          
          <Form.Item
            name="code"
            label="编码"
            rules={[{ required: true, message: '请输入编码!' }]}
          >
            <Input placeholder="唯一标识编码" />
          </Form.Item>
          
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入名称!' }]}
          >
            <Input placeholder="显示名称" />
          </Form.Item>
          
          <Form.Item name="parent_id" label="父级">
            <Select placeholder="选择父级（留空表示顶级）" allowClear showSearch>
              {parentOptions.map(opt => (
                <Option key={opt.value} value={opt.value} disabled={editingItem?.id === opt.value}>
                  {opt.label}
                </Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item name="sort_order" label="排序">
            <InputNumber placeholder="数字越小越靠前" style={{ width: '100%' }} />
          </Form.Item>
          
          <Form.Item name="is_active" label="是否启用" valuePropName="checked">
            <Switch />
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

export default DictItemList;