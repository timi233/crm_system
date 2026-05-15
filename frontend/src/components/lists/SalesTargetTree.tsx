import React, { useCallback, useMemo, useState } from 'react';
import {
  App,
  Button,
  Form,
  InputNumber,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  Alert,
  Progress,
  SelectProps,
  Row,
  Col,
} from 'antd';
import {
  PlusOutlined,
  TrophyOutlined,
  SplitCellsOutlined,
  EditOutlined,
  DeleteOutlined,
  WarningOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import ActualEntryModal from '../modals/ActualEntryModal';
import QuarterSplitModal from '../modals/QuarterSplitModal';
import YearSplitModal from '../modals/YearSplitModal';
import PageModal from '../common/PageModal';
import {
  useSalesTargetTree,
  useCreateYearTarget,
  useUpdateSalesTarget,
  useDeleteSalesTarget,
  useUsers,
  useActualRecords,
  type YearNode,
  type MonthNode,
  type ActualPerformance,
} from '../../hooks/useSalesTargets';
import { useAuth } from '../../hooks/useAuth';
import { Popconfirm } from 'antd';

const { Text, Title } = Typography;
const { Option } = Select;

/* ─── Helpers ─── */

const formatWan = (v: number | null | undefined) => {
  if (v === null || v === undefined) return '-';
  return (Number(v) / 10000).toLocaleString('zh-CN', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
};

const toWan = (v: number | null | undefined) => {
  if (v === null || v === undefined) return undefined;
  return Number((Number(v) / 10000).toFixed(1));
};

const fromWan = (v: number | null | undefined) => {
  if (v === null || v === undefined) return 0;
  return Math.round(Number(v) * 10000);
};

const progressColor = (pct: number) => {
  if (pct >= 100) return '#10B981';
  if (pct >= 80) return '#F59E0B';
  if (pct > 0) return '#EF4444';
  return '#cbd5e1';
};

const progressLabel = (pct: number) => {
  if (pct >= 100) return '🚀超额';
  if (pct >= 80) return '✅接近';
  if (pct <= 0) return '';
  return '🔴落后';
};

/* ─── Row Type ─── */

type RowLevel = 'year' | 'quarter' | 'month';

interface TreeRow {
  key: string;
  level: RowLevel;
  id: number;
  userId?: number;
  year: number;
  period: number;
  periodDisplay: string;
  target_amount: number;
  gross_profit_target: number;
  remaining_rev: number;
  remaining_gp: number;
  actual_amount: number;
  actual_gross_profit: number;
  has_actual?: boolean;
  progress_pct: number;
  children?: TreeRow[];
}

/* ─── Build Tree ─── */

const buildTreeRows = (
  data: YearNode[],
  actualMap: Map<string, ActualPerformance>,
): TreeRow[] => {
  const getActualForMonth = (userId: number, year: number, month: number) => {
    return actualMap.get(`${userId}-${year}-${month}`);
  };

  return data.map((yr) => {
    const monthsFromQuarters = (yr.quarters ?? []).flatMap((q) => q.months ?? []);

    const yrActuals = monthsFromQuarters.map((m) =>
      getActualForMonth(yr.user_id, yr.target_year, m.period),
    );
    const yrTotalActualRev = yrActuals.reduce(
      (s, a) => s + (a?.amount_actual ?? 0),
      0,
    );
    const yrTotalActualGp = yrActuals.reduce(
      (s, a) => s + (a?.gross_profit_actual ?? 0),
      0,
    );
    const yrProgress =
      yr.target_amount > 0
        ? (yrTotalActualRev / yr.target_amount) * 100
        : 0;

    const quarterRows = (yr.quarters ?? []).map((q) => {
      const qActuals = (q.months ?? []).map((m) =>
        getActualForMonth(yr.user_id, yr.target_year, m.period),
      );
      const qTotalActualRev = qActuals.reduce(
        (s, a) => s + (a?.amount_actual ?? 0),
        0,
      );
      const qTotalActualGp = qActuals.reduce(
        (s, a) => s + (a?.gross_profit_actual ?? 0),
        0,
      );
      const qProgress =
        q.target_amount > 0
          ? (qTotalActualRev / q.target_amount) * 100
          : 0;

      const monthRows: TreeRow[] = (q.months ?? []).map((m) => {
        const mA = getActualForMonth(yr.user_id, yr.target_year, m.period);
        const mRev = mA?.amount_actual ?? 0;
        const mGp = mA?.gross_profit_actual ?? 0;
        const mProgress =
          m.target_amount > 0 ? (mRev / m.target_amount) * 100 : 0;

        return {
          key: `m-${m.id}`,
          level: 'month' as RowLevel,
          id: m.id,
          userId: yr.user_id,
          year: yr.target_year,
          period: m.period,
          periodDisplay: `${m.period}月`,
          target_amount: m.target_amount,
          gross_profit_target: m.gross_profit_target,
          remaining_rev: m.remaining_rev,
          remaining_gp: m.remaining_gp,
          actual_amount: mRev,
          actual_gross_profit: mGp,
          has_actual: Boolean(mA),
          progress_pct: mProgress,
        };
      });

      return {
        key: `q-${q.id}`,
        level: 'quarter' as RowLevel,
        id: q.id,
        userId: yr.user_id,
        year: yr.target_year,
        period: q.period,
        periodDisplay: `Q${q.period}`,
        target_amount: q.target_amount,
        gross_profit_target: q.gross_profit_target,
        remaining_rev: q.remaining_rev,
        remaining_gp: q.remaining_gp,
        actual_amount: qTotalActualRev,
        actual_gross_profit: qTotalActualGp,
        progress_pct: qProgress,
        _quarterData: q,
        _yearTargetId: yr.id,
        children: monthRows.length > 0 ? monthRows : undefined,
      };
    });

    const row: TreeRow = {
      key: `y-${yr.id}`,
      level: 'year' as RowLevel,
      id: yr.id,
      userId: yr.user_id,
      year: yr.target_year,
      period: yr.target_year,
      periodDisplay: `${yr.target_year}年`,
      target_amount: yr.target_amount,
      gross_profit_target: yr.gross_profit_target,
      remaining_rev: yr.remaining_rev,
      remaining_gp: yr.remaining_gp,
      actual_amount: yrTotalActualRev,
      actual_gross_profit: yrTotalActualGp,
      progress_pct: yrProgress,
      children: quarterRows.length > 0 ? quarterRows : undefined,
    };

    return row;
  });
};

/* ─── Main Component ─── */

const SalesTargetTree: React.FC = () => {
  const { message } = App.useApp();
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear());
  const [form] = Form.useForm();
  const [editForm] = Form.useForm();
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<TreeRow | null>(null);

  const [entryModal, setEntryModal] = useState<{
    open: boolean;
    year: number;
    month: number;
    userId: number;
    targetId?: number | null;
    revTarget?: number;
    gpTarget?: number;
    existingActual?: {
        id: number;
        amount_actual: number;
        gross_profit_actual: number;
    } | null;
  }>({ open: false, year: 0, month: 0, userId: 0 });

  const [splitModal, setSplitModal] = useState<{
    open: boolean;
    yearTargetId: number;
    targetYear: number;
    quarter: number;
    quarterRevTarget: number;
    quarterGpTarget: number;
  }>({ open: false, yearTargetId: 0, targetYear: 0, quarter: 0, quarterRevTarget: 0, quarterGpTarget: 0 });

  const [yearSplitModal, setYearSplitModal] = useState<{
    open: boolean;
    yearTargetId: number;
    targetYear: number;
    yearRevTarget: number;
    yearGpTarget: number;
    existingQuarters?: any[];
  }>({ open: false, yearTargetId: 0, targetYear: 0, yearRevTarget: 0, yearGpTarget: 0 });

  const { data: treeData = [], isLoading: treeLoading, refetch: refetchTree } = useSalesTargetTree(selectedYear);
  const { data: users = [], isLoading: usersLoading } = useUsers();
  const { data: actuals = [] } = useActualRecords({ year: selectedYear });

  const createMutation = useCreateYearTarget();
  const updateMutation = useUpdateSalesTarget();
  const deleteMutation = useDeleteSalesTarget();

  const actualMap = useMemo(() => {
    const m = new Map<string, ActualPerformance>();
    actuals.forEach((a) => m.set(`${a.user_id}-${a.year}-${a.month}`, a));
    return m;
  }, [actuals]);

  const userMap = useMemo(() => {
    const m = new Map<number, string>();
    users.forEach((u) => m.set(u.id, u.name));
    return m;
  }, [users]);

  const getUserName = useCallback(
    (uid: number) => userMap.get(uid) || `ID:${uid}`,
    [userMap],
  );

  const nestedData = useMemo(
    () => buildTreeRows(treeData, actualMap),
    [treeData, actualMap],
  );

  const openEntryDrawer = useCallback(
    (row: TreeRow) => {
      const existing = actuals.find(
        (a) => a.user_id === row.userId && a.year === row.year && a.month === row.period,
      );
      setEntryModal({
        open: true,
        year: row.year,
        month: row.period,
        userId: row.userId ?? 0,
        targetId: row.id,
        revTarget: row.target_amount,
        gpTarget: row.gross_profit_target,
        existingActual: existing ? {
            id: existing.id,
            amount_actual: existing.amount_actual,
            gross_profit_actual: existing.gross_profit_actual
        } : null,
      });
    },
    [actuals],
  );

  const openSplitDrawer = useCallback((row: TreeRow) => {
    setSplitModal({
      open: true,
      yearTargetId: (row as any)._yearTargetId ?? 0,
      targetYear: row.year,
      quarter: row.period,
      quarterRevTarget: row.target_amount,
      quarterGpTarget: row.gross_profit_target,
    });
  }, []);

  const openYearSplitModal = useCallback((row: TreeRow) => {
    setYearSplitModal({
      open: true,
      yearTargetId: row.id,
      targetYear: row.year,
      yearRevTarget: row.target_amount,
      yearGpTarget: row.gross_profit_target,
      existingQuarters: row.children?.map(c => ({
        quarter: c.period,
        target_amount: c.target_amount,
        gross_profit_target: c.gross_profit_target
      }))
    });
  }, []);

  const openEditDrawer = useCallback((row: TreeRow) => {
    setEditTarget(row);
    editForm.setFieldsValue({
      target_amount: toWan(row.target_amount),
      gross_profit_target: toWan(row.gross_profit_target),
    });
    setEditModalOpen(true);
  }, [editForm]);

  const handleEditTarget = async () => {
    if (!editTarget) return;
    const values = await editForm.validateFields();
    await updateMutation.mutateAsync({
      id: editTarget.id,
      data: {
        target_amount: fromWan(values.target_amount),
        gross_profit_target: fromWan(values.gross_profit_target) || 0,
      },
    });
    editForm.resetFields();
    setEditModalOpen(false);
    setEditTarget(null);
    message.success('目标更新成功');
    refetchTree();
  };

  const handleDeleteTarget = async (row: TreeRow) => {
    await deleteMutation.mutateAsync(row.id);
    message.success('目标删除成功');
    refetchTree();
  };

  const handleCreateYear = async () => {
    const values = await form.validateFields();
    await createMutation.mutateAsync({
      user_id: values.user_id,
      target_year: values.target_year,
      target_amount: fromWan(values.target_amount),
      gross_profit_target: fromWan(values.gross_profit_target) || 0,
    });
    form.resetFields();
    setCreateModalOpen(false);
    message.success('年目标创建成功');
    refetchTree();
  };

  const yearOptions: SelectProps['options'] = useMemo(() => {
    const cy = new Date().getFullYear();
    return [cy - 1, cy, cy + 1].map((y) => ({
      value: y,
      label: `${y}年`,
    }));
  }, []);

  const columns = [
    {
      title: '考核期间',
      dataIndex: 'periodDisplay',
      key: 'periodDisplay',
      width: 140,
      render: (text: string, record: TreeRow) => (
        <Space>
          {record.level === 'year' && <TrophyOutlined style={{ color: '#F59E0B' }} />}
          {record.level === 'quarter' && (
            <Tag color="blue" style={{ border: 'none', background: '#eff6ff', color: '#3b82f6', fontWeight: 600 }}>
              Q{record.period}
            </Tag>
          )}
          {record.level === 'month' && (
            <Tag style={{ border: 'none', background: '#f8fafc', color: '#64748b', fontWeight: 600 }}>
              {record.period}月
            </Tag>
          )}
          {record.level === 'year' && <span style={{ fontWeight: 700 }}>{text}</span>}
        </Space>
      ),
    },
    {
      title: '销售责任人',
      dataIndex: 'userId',
      key: 'userId',
      width: 120,
      render: (uid: number, record: TreeRow) =>
        record.level === 'year' ? <span style={{ fontWeight: 600 }}>{getUserName(uid)}</span> : <span style={{ color: '#94a3b8' }}>-</span>,
    },
    {
      title: '营收目标',
      dataIndex: 'target_amount',
      key: 'target_amount',
      width: 120,
      render: (v: number) => (
        <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 500 }}>
          {formatWan(v)} 万
        </span>
      ),
    },
    {
      title: '毛利目标',
      dataIndex: 'gross_profit_target',
      key: 'gross_profit_target',
      width: 120,
      render: (v: number) => (
        <span style={{ fontFamily: 'var(--font-mono)', color: '#64748b' }}>
          {formatWan(v)} 万
        </span>
      ),
    },
    {
      title: '实际营收',
      dataIndex: 'actual_amount',
      key: 'actual_amount',
      width: 120,
      render: (v: number, record: TreeRow) => (
        <span
          style={{
            color: progressColor(record.progress_pct),
            fontFamily: 'var(--font-mono)',
            fontWeight: 700,
          }}
        >
          {formatWan(v)} 万
        </span>
      ),
    },
    {
      title: '完成进度',
      dataIndex: 'progress_pct',
      key: 'progress_pct',
      width: 180,
      render: (pct: number) => (
        <Space direction="vertical" size={0} style={{ width: '100%' }}>
          <Progress
            percent={Math.min(pct, 100)}
            strokeColor={progressColor(pct)}
            trailColor="#f1f5f9"
            size={[100, 8]}
            showInfo={false}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: progressColor(pct) }}>{pct.toFixed(1)}%</span>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>{progressLabel(pct)}</span>
          </div>
        </Space>
      ),
    },
    {
      title: '待分配额度',
      key: 'remaining',
      width: 130,
      render: (_: unknown, record: TreeRow) => {
        if (record.level === 'year' || record.level === 'quarter') {
          const hasRem = record.remaining_rev > 0.01 || record.remaining_gp > 0.01;
          if (!hasRem) return <span style={{ color: '#10B981', fontSize: '12px' }}>已分配完</span>;
          return (
            <span style={{ color: '#F59E0B', fontSize: '12px', fontWeight: 600 }}>
              <WarningOutlined style={{ marginRight: 4 }} />
              {formatWan(record.remaining_rev)}万
            </span>
          );
        }
        return '-';
      },
    },
    {
      title: '快捷操作',
      key: 'action',
      width: 150,
      render: (_: unknown, record: TreeRow) => {
        const hasChildren = Boolean(record.children?.length);
        const hasActual = record.level === 'month' && Boolean(record.has_actual);
        const deleteBlocked = hasChildren || hasActual;
        const deleteDisabledReason = hasChildren
          ? '请先删除下级目标'
          : hasActual
            ? '请先删除已填报的业绩'
            : undefined;

        return (
          <Space size="small">
            {record.level === 'year' && (
              <Button
                size="small"
                type="link"
                icon={<SplitCellsOutlined />}
                onClick={() => openYearSplitModal(record)}
              >
                分配
              </Button>
            )}
            {record.level === 'month' && (
              <Button
                size="small"
                type="link"
                icon={<EditOutlined />}
                onClick={() => openEntryDrawer(record)}
              >
                填报
              </Button>
            )}
            {record.level === 'quarter' && (
              <Button
                size="small"
                type="link"
                icon={<SplitCellsOutlined />}
                onClick={() => openSplitDrawer(record)}
              >
                拆分
              </Button>
            )}
            {isAdmin && (
              <Button
                size="small"
                type="link"
                icon={<EditOutlined />}
                onClick={() => openEditDrawer(record)}
              >
                编辑
              </Button>
            )}
            {isAdmin && (
              deleteBlocked ? (
                <Button
                  size="small"
                  type="link"
                  danger
                  disabled
                  title={deleteDisabledReason}
                  icon={<DeleteOutlined />}
                >
                  删除
                </Button>
              ) : (
                <Popconfirm
                  title="确定删除该考核目标？"
                  description="删除后不可恢复，请确认是否继续。"
                  onConfirm={() => handleDeleteTarget(record)}
                  okText="确定"
                  cancelText="取消"
                  okButtonProps={{ danger: true }}
                >
                  <Button
                    size="small"
                    type="link"
                    danger
                    icon={<DeleteOutlined />}
                  >
                    删除
                  </Button>
                </Popconfirm>
              )
            )}
          </Space>
        );
      },
    },
  ];

  const currentYear = new Date().getFullYear();

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24, alignItems: 'center', background: 'white', padding: '16px 24px', borderRadius: '12px', border: '1px solid #f1f5f9' }}>
        <Space size={16}>
          <div style={{ width: 40, height: 40, borderRadius: '10px', background: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#0052cc' }}>
            <TrophyOutlined style={{ fontSize: 20 }} />
          </div>
          <div>
            <div style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a' }}>销售考核目标</div>
            <div style={{ fontSize: '12px', color: '#64748b' }}>管理并追踪各销售人员的业绩指标达成情况</div>
          </div>
        </Space>
        <Space size={12}>
          <Select
            value={selectedYear}
            onChange={setSelectedYear}
            style={{ width: 120 }}
            options={yearOptions}
            size="large"
          />
          <Button icon={<ReloadOutlined />} onClick={() => refetchTree()} size="large" />
          {isAdmin && (
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => {
                form.setFieldsValue({ target_year: selectedYear });
                setCreateModalOpen(true);
              }}
              size="large"
              className="btn--gradient"
            >
              新建年目标
            </Button>
          )}
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={nestedData}
        loading={treeLoading || usersLoading}
        rowKey="key"
        pagination={false}
        defaultExpandAllRows
        size="middle"
        className="customer-table"
        bordered={false}
        onRow={(record: TreeRow) => ({
          onDoubleClick: () => {
            if (record.level === 'month') {
              openEntryDrawer(record);
            }
          },
        })}
      />

      <PageModal
        title="设置年度业绩指标"
        open={createModalOpen}
        onClose={() => {
          setCreateModalOpen(false);
          form.resetFields();
        }}
        width={560}
        footer={[
            <Button key="cancel" onClick={() => setCreateModalOpen(false)}>取消</Button>,
            <Button key="submit" type="primary" className="btn--gradient" onClick={handleCreateYear} loading={createMutation.isPending}>同步到系统</Button>
        ]}
      >
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 24, borderRadius: '8px' }}
          message="规则提示"
          description="考核额度以万元为单位，录入后系统将自动按季度/月度进行默认平摊，您可在后续进行手动精细化拆分。"
        />
        <Form form={form} layout="vertical">
          <Form.Item
            name="user_id"
            label="考核人员"
            rules={[{ required: true, message: '请选择销售人员' }]}
          >
            <Select placeholder="选择需要考核的员工" showSearch optionFilterProp="children">
              {users
                .filter((u) => u.id !== 1)
                .map((u) => (
                  <Option key={u.id} value={u.id}>
                    {u.name}
                  </Option>
                ))}
            </Select>
          </Form.Item>
          <Form.Item name="target_year" label="目标年度" rules={[{ required: true }]}>
            <Select placeholder="选择年度">
              {[currentYear - 1, currentYear, currentYear + 1].map((y) => (
                <Option key={y} value={y}>
                  {y}年
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
                <Form.Item
                    name="target_amount"
                    label="营收指标 (万元)"
                    rules={[{ required: true, message: '请输入目标金额' }]}
                >
                    <InputNumber
                    style={{ width: '100%' }}
                    placeholder="0.0"
                    min={0}
                    precision={1}
                    addonAfter="万"
                    />
                </Form.Item>
            </Col>
            <Col span={12}>
                <Form.Item name="gross_profit_target" label="毛利指标 (万元)" rules={[{ required: true, message: '请输入毛利目标' }]}>
                    <InputNumber
                    style={{ width: '100%' }}
                    placeholder="0.0"
                    min={0}
                    precision={1}
                    addonAfter="万"
                    />
                </Form.Item>
            </Col>
          </Row>
        </Form>
      </PageModal>

      <ActualEntryModal
        open={entryModal.open}
        onClose={() => setEntryModal((p) => ({ ...p, open: false }))}
        year={entryModal.year}
        month={entryModal.month}
        userId={entryModal.userId}
        targetId={entryModal.targetId}
        revTarget={entryModal.revTarget}
        gpTarget={entryModal.gpTarget}
        existingActual={entryModal.existingActual}
      />

      <YearSplitModal
        open={yearSplitModal.open}
        onClose={() => setYearSplitModal((p) => ({ ...p, open: false }))}
        yearTargetId={yearSplitModal.yearTargetId}
        targetYear={yearSplitModal.targetYear}
        yearRevTarget={yearSplitModal.yearRevTarget}
        yearGpTarget={yearSplitModal.yearGpTarget}
        existingQuarters={yearSplitModal.existingQuarters}
        onSplitSuccess={() => refetchTree()}
      />

      <QuarterSplitModal
        open={splitModal.open}
        onClose={() => setSplitModal((p) => ({ ...p, open: false }))}
        yearTargetId={splitModal.yearTargetId}
        targetYear={splitModal.targetYear}
        quarter={splitModal.quarter}
        quarterRevTarget={splitModal.quarterRevTarget}
        quarterGpTarget={splitModal.quarterGpTarget}
        onSplitSuccess={() => refetchTree()}
      />

      <PageModal
        title={`修正指标 · ${editTarget?.periodDisplay}`}
        open={editModalOpen}
        onClose={() => {
          setEditModalOpen(false);
          setEditTarget(null);
          editForm.resetFields();
        }}
        width={520}
        footer={[
            <Button key="cancel" onClick={() => setEditModalOpen(false)}>取消</Button>,
            <Button key="submit" type="primary" className="btn--gradient" onClick={handleEditTarget} loading={updateMutation.isPending}>更新指标</Button>
        ]}
      >
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 24, borderRadius: '8px' }}
          message="约束检查"
          description="修改上级目标时，需确保其数值不低于下级已分配的目标之和；修改下级目标时，总额不能超过父级目标。"
        />
        <Form form={editForm} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
                <Form.Item
                    name="target_amount"
                    label="营收目标 (万元)"
                    rules={[{ required: true, message: '请输入目标金额' }]}
                >
                    <InputNumber
                    style={{ width: '100%' }}
                    placeholder="0.0"
                    min={0}
                    precision={1}
                    addonAfter="万"
                    />
                </Form.Item>
            </Col>
            <Col span={12}>
                <Form.Item name="gross_profit_target" label="毛利目标 (万元)">
                    <InputNumber
                    style={{ width: '100%' }}
                    placeholder="0.0"
                    min={0}
                    precision={1}
                    addonAfter="万"
                    />
                </Form.Item>
            </Col>
          </Row>
        </Form>
      </PageModal>
    </div>
  );
};

export default SalesTargetTree;
