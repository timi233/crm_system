import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Descriptions,
  Tag,
  Button,
  Space,
  Table,
  Spin,
  Modal,
  Select,
  message,
  Input,
  Divider,
} from 'antd';
import {
  ArrowLeftOutlined,
  CheckCircleOutlined,
  StopOutlined,
  UserSwitchOutlined,
} from '@ant-design/icons';
import {
  useHandoverRequest,
  useAssetsPreview,
  useAssignHandover,
  useExecuteHandover,
  useCancelHandover,
} from '../hooks/useHandovers';
import { useUsers } from '../hooks/useUsers';

const { TextArea } = Input;
const { confirm } = Modal;

const STATUS_LABELS: Record<string, string> = {
  pending_assignment: '待分配',
  pending_execution: '待执行',
  executing: '执行中',
  completed: '已完成',
  canceled: '已取消',
  failed: '失败',
};

const STATUS_COLORS: Record<string, string> = {
  pending_assignment: 'orange',
  pending_execution: 'blue',
  executing: 'processing',
  completed: 'success',
  canceled: 'default',
  failed: 'error',
};

const ENTITY_LABELS: Record<string, string> = {
  TerminalCustomer: '终端客户',
  Lead: '线索',
  Opportunity: '商机',
  Project: '项目',
  FollowUp: '跟进记录',
  WorkOrder: '工单',
  WorkOrderTechnician: '工单技术员',
  ChannelAssignment: '渠道分配',
  ExecutionPlan: '执行计划',
};

const HandoverDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const handoverId = Number(id);
  const hasValidId = Number.isInteger(handoverId) && handoverId > 0;

  const { data: handover, isLoading, error } = useHandoverRequest(handoverId, hasValidId);
  const { data: assets, isLoading: assetsLoading } = useAssetsPreview(handoverId, hasValidId && !!handover);
  const { data: users = [], isLoading: usersLoading } = useUsers();

  const assignMutation = useAssignHandover();
  const executeMutation = useExecuteHandover();
  const cancelMutation = useCancelHandover();

  const [assignModalVisible, setAssignModalVisible] = useState(false);
  const [selectedToUserId, setSelectedToUserId] = useState<number | undefined>(undefined);
  const [cancelReason, setCancelReason] = useState('');
  const [scopeEntities, setScopeEntities] = useState<string[]>(
    Object.keys(ENTITY_LABELS)
  );

  const userMap = new Map<number, string>(users.map((u: any) => [u.id, u.name]));

  if (isLoading || usersLoading) {
    return (
      <Card>
        <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />
      </Card>
    );
  }

  if (!hasValidId || error || !handover) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          加载失败或交接请求不存在
          <Button onClick={() => navigate('/handovers')} style={{ marginLeft: 16 }}>
            返回列表
          </Button>
        </div>
      </Card>
    );
  }

  const isPendingAssignment = handover.status === 'pending_assignment';
  const isPendingExecution = handover.status === 'pending_execution';
  const isCompleted = handover.status === 'completed';
  const isCanceled = handover.status === 'canceled';
  const isFailed = handover.status === 'failed';
  const canAssign = isPendingAssignment;
  const canExecute = isPendingExecution || isFailed;
  const canCancel = !isCompleted && !isCanceled;

  const userName = (userId: number | null | undefined) => {
    if (userId == null) return '-';
    return userMap.get(userId) || `用户 #${userId}`;
  };

  const handleAssign = () => {
    if (!selectedToUserId) {
      message.warning('请选择接收人');
      return;
    }
    assignMutation.mutate(
      { id: handoverId, data: { to_user_id: selectedToUserId, scope_config: { entities: scopeEntities } } },
      {
        onSuccess: () => {
          message.success('分配成功');
          setAssignModalVisible(false);
          setSelectedToUserId(undefined);
        },
        onError: () => {
          message.error('分配失败');
        },
      }
    );
  };

  const handleExecute = () => {
    confirm({
      title: '确认执行交接',
      content: '执行后将自动转移所有资产归属，此操作不可逆。确定继续吗？',
      okText: '确认执行',
      okButtonProps: { danger: true },
      onOk: () => {
        executeMutation.mutate(handoverId, {
          onSuccess: (res: any) => {
            if (res.success) {
              message.success('交接执行成功');
            } else {
              message.error(res.message || '交接执行失败');
            }
          },
        });
      },
    });
  };

  const handleCancel = () => {
    Modal.confirm({
      title: '取消交接请求',
      content: (
        <div>
          <p>确定要取消此交接请求吗？</p>
          <TextArea
            placeholder="请输入取消原因（可选）"
            value={cancelReason}
            onChange={(e) => setCancelReason(e.target.value)}
            rows={3}
          />
        </div>
      ),
      okText: '确认取消',
      okButtonProps: { danger: true },
      onOk: () => {
        cancelMutation.mutate(
          { id: handoverId, reason: cancelReason || undefined },
          {
            onSuccess: () => {
              message.success('取消成功');
              setCancelReason('');
            },
          }
        );
      },
    });
  };

  const assetColumns = [
    {
      title: '资产类型',
      dataIndex: 'entity',
      key: 'entity',
      render: (key: string) => ENTITY_LABELS[key] || key,
    },
    {
      title: '数量',
      dataIndex: 'count',
      key: 'count',
      width: 100,
    },
    {
      title: '归属字段',
      dataIndex: 'field',
      key: 'field',
    },
  ];

  const assetRows = assets
    ? Object.entries(assets)
        .filter(([, v]: [string, any]) => v.count > 0)
        .map(([key, value]: [string, any]) => ({
          entity: key,
          count: value.count,
          field: value.field,
        }))
    : [];

  const executionSummary = handover.execution_summary;

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Card>
        <div style={{ marginBottom: 16 }}>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/handovers')}>
            返回列表
          </Button>
        </div>

        <Descriptions bordered column={2}>
          <Descriptions.Item label="交接 ID">{handover.id}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={STATUS_COLORS[handover.status] || 'default'}>
              {STATUS_LABELS[handover.status] || handover.status}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="离职人员">
            {userName(handover.from_user_id)}
          </Descriptions.Item>
          <Descriptions.Item label="接收人">
            {handover.to_user_id ? userName(handover.to_user_id) : '未分配'}
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {handover.created_at ? new Date(handover.created_at).toLocaleString('zh-CN') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="分配时间">
            {handover.decided_at ? new Date(handover.decided_at).toLocaleString('zh-CN') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="执行时间">
            {handover.executed_at ? new Date(handover.executed_at).toLocaleString('zh-CN') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="错误信息">
            {handover.error_message || '-'}
          </Descriptions.Item>
        </Descriptions>

        <div style={{ marginTop: 16 }}>
          <Space>
            {canAssign && (
              <Button
                type="primary"
                icon={<UserSwitchOutlined />}
                onClick={() => setAssignModalVisible(true)}
              >
                分配接收人
              </Button>
            )}
            {canExecute && (
              <Button
                danger
                icon={<CheckCircleOutlined />}
                onClick={handleExecute}
                loading={executeMutation.isPending}
              >
                执行交接
              </Button>
            )}
            {canCancel && (
              <Button
                icon={<StopOutlined />}
                onClick={handleCancel}
                loading={cancelMutation.isPending}
              >
                取消交接
              </Button>
            )}
          </Space>
        </div>
      </Card>

      <Card title="资产预览">
        {assetsLoading ? (
          <Spin />
        ) : assetRows.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '20px 0', color: '#999' }}>
            {isPendingAssignment
              ? '请先分配接收人以查看资产预览'
              : '暂无待交接资产'}
          </div>
        ) : (
          <Table
            columns={assetColumns}
            dataSource={assetRows}
            rowKey="entity"
            pagination={false}
            size="small"
          />
        )}
      </Card>

      {isCompleted && executionSummary && executionSummary.transferred && (
        <Card title="执行结果">
          <Descriptions bordered column={2} size="small">
            {Object.entries(executionSummary.transferred).map(([entity, count]) => (
              <Descriptions.Item key={entity} label={ENTITY_LABELS[entity] || entity}>
                已转移 {count as number} 条
              </Descriptions.Item>
            ))}
          </Descriptions>
          {executionSummary.errors && executionSummary.errors.length > 0 && (
            <>
              <Divider orientation="left">错误信息</Divider>
              {executionSummary.errors.map((err: string, i: number) => (
                <Tag key={i} color="error" style={{ marginBottom: 4 }}>
                  {err}
                </Tag>
              ))}
            </>
          )}
        </Card>
      )}

      <Modal
        title="分配交接接收人"
        open={assignModalVisible}
        onOk={handleAssign}
        onCancel={() => {
          setAssignModalVisible(false);
          setSelectedToUserId(undefined);
        }}
        confirmLoading={assignMutation.isPending}
        okText="确认分配"
        cancelText="取消"
      >
        <div style={{ marginBottom: 16 }}>
          <div style={{ marginBottom: 8 }}>选择接收人：</div>
          <Select
            value={selectedToUserId}
            onChange={setSelectedToUserId}
            placeholder="请选择接收人"
            style={{ width: '100%' }}
            showSearch
            optionFilterProp="children"
          >
            {users
              .filter((u: any) => u.is_active !== false)
              .map((u: any) => (
                <Select.Option key={u.id} value={u.id}>
                  {u.name} ({u.email})
                </Select.Option>
              ))}
          </Select>
        </div>
        <div>
          <div style={{ marginBottom: 8 }}>交接范围：</div>
          <Select
            mode="multiple"
            value={scopeEntities}
            onChange={setScopeEntities}
            placeholder="选择交接资产类型"
            style={{ width: '100%' }}
          >
            {Object.entries(ENTITY_LABELS).map(([key, label]) => (
              <Select.Option key={key} value={key}>
                {label}
              </Select.Option>
            ))}
          </Select>
        </div>
      </Modal>
    </Space>
  );
};

export default HandoverDetailPage;
