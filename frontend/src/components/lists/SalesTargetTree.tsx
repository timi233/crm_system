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
  Drawer,
  Alert,
  Progress,
  SelectProps,
} from 'antd';
import {
  PlusOutlined,
  TrophyOutlined,
  SplitCellsOutlined,
  EditOutlined,
  DeleteOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import ActualEntryDrawer from '../modals/ActualEntryDrawer';
import QuarterSplitDrawer from '../modals/QuarterSplitDrawer';
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

const { Text } = Typography;
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
  if (pct >= 100) return 'var(--success-color)';
  if (pct >= 80) return 'var(--warning-color)';
  if (pct > 0) return 'var(--error-color)';
  return '#d9d9d9';
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
  const [createDrawerOpen, setCreateDrawerOpen] = useState(false);
  const [editDrawerOpen, setEditDrawerOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<TreeRow | null>(null);
  const [entryDrawer, setEntryDrawer] = useState<{
    open: boolean;
    year: number;
    month: number;
    userId: number;
    targetId?: number | null;
    revTarget?: number;
    gpTarget?: number;
    existingActual?: ActualPerformance | null;
  }>({ open: false, year: 0, month: 0, userId: 0 });
  const [splitDrawer, setSplitDrawer] = useState<{
    open: boolean;
    yearTargetId: number;
    targetYear: number;
    quarter: number;
    quarterRevTarget: number;
    quarterGpTarget: number;
  }>({ open: false, yearTargetId: 0, targetYear: 0, quarter: 0, quarterRevTarget: 0, quarterGpTarget: 0 });

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
      setEntryDrawer({
        open: true,
        year: row.year,
        month: row.period,
        userId: row.userId ?? 0,
        targetId: row.id,
        revTarget: row.target_amount,
        gpTarget: row.gross_profit_target,
        existingActual: existing ?? null,
      });
    },
    [actuals],
  );

  const openSplitDrawer = useCallback((row: TreeRow) => {
    setSplitDrawer({
      open: true,
      yearTargetId: (row as any)._yearTargetId ?? 0,
      targetYear: row.year,
      quarter: row.period,
      quarterRevTarget: row.target_amount,
      quarterGpTarget: row.gross_profit_target,
    });
  }, []);

  const openEditDrawer = useCallback((row: TreeRow) => {
    setEditTarget(row);
    editForm.setFieldsValue({
      target_amount: toWan(row.target_amount),
      gross_profit_target: toWan(row.gross_profit_target),
    });
    setEditDrawerOpen(true);
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
    setEditDrawerOpen(false);
    setEditTarget(null);
    message.success('目标更新成功');
  };

  const handleDeleteTarget = async (row: TreeRow) => {
    await deleteMutation.mutateAsync(row.id);
    message.success('目标删除成功');
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
    setCreateDrawerOpen(false);
    message.success('年目标创建成功');
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
      title: '期间',
      dataIndex: 'periodDisplay',
      key: 'periodDisplay',
      width: 100,
      render: (text: string, record: TreeRow) => (
        <Space>
          {record.level === 'year' && <TrophyOutlined />}
          {record.level === 'quarter' && (
            <Tag color="blue" style={{ marginRight: 4 }}>
              季度
            </Tag>
          )}
          {record.level === 'month' && (
            <Tag color="green" style={{ marginRight: 4 }}>
              月度
            </Tag>
          )}
          {text}
        </Space>
      ),
    },
    {
      title: '',
      key: 'spacer',
      width: 1,
      render: () => null,
    },
    {
      title: '销售人员',
      dataIndex: 'userId',
      key: 'userId',
      width: 90,
      render: (uid: number, record: TreeRow) =>
        record.level === 'year' ? getUserName(uid) : '-',
    },
    {
      title: '营收目标',
      dataIndex: 'target_amount',
      key: 'target_amount',
      width: 110,
      render: (v: number) => (
        <span style={{ fontFamily: 'var(--font-mono)' }}>
          {formatWan(v)} 万
        </span>
      ),
    },
    {
      title: '毛利目标',
      dataIndex: 'gross_profit_target',
      key: 'gross_profit_target',
      width: 110,
      render: (v: number) => (
        <span style={{ fontFamily: 'var(--font-mono)' }}>
          {formatWan(v)} 万
        </span>
      ),
    },
    {
      title: '实际营收',
      dataIndex: 'actual_amount',
      key: 'actual_amount',
      width: 110,
      render: (v: number, record: TreeRow) => (
        <span
          style={{
            color: record.progress_pct >= 100
              ? 'var(--success-color)'
              : record.progress_pct >= 80
                ? 'var(--warning-color)'
                : 'var(--error-color)',
            fontFamily: 'var(--font-mono)',
            fontWeight: 600,
          }}
        >
          {formatWan(v)} 万
        </span>
      ),
    },
    {
      title: '实际毛利',
      dataIndex: 'actual_gross_profit',
      key: 'actual_gross_profit',
      width: 110,
      render: (v: number) => (
        <span style={{ fontFamily: 'var(--font-mono)' }}>
          {formatWan(v)} 万
        </span>
      ),
    },
    {
      title: '完成率',
      dataIndex: 'progress_pct',
      key: 'progress_pct',
      width: 160,
      render: (pct: number) => (
        <Space>
          <Progress
            percent={Math.min(pct, 100)}
            strokeColor={progressColor(pct)}
            trailColor="#f0f0f0"
            size="small"
            style={{ width: 80 }}
          />
          <Text style={{ fontSize: 12 }}>
            {pct.toFixed(1)}% {progressLabel(pct)}
          </Text>
        </Space>
      ),
    },
    {
      title: '剩余',
      key: 'remaining',
      width: 130,
      render: (_: unknown, record: TreeRow) => {
        if (record.level === 'year' || record.level === 'quarter') {
          const hasRem = record.remaining_rev > 0.01 || record.remaining_gp > 0.01;
          if (!hasRem) return <Text type="secondary">-</Text>;
          return (
            <Text type="warning" style={{ fontSize: 12 }}>
              <WarningOutlined /> 营{formatWan(record.remaining_rev)}万
            </Text>
          );
        }
        return '-';
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: unknown, record: TreeRow) => {
        const hasChildren = Boolean(record.children?.length);
        const hasActual = record.level === 'month' && Boolean(record.has_actual);
        const deleteBlocked = hasChildren || hasActual;
        const deleteDisabledReason = hasChildren
          ? '请先删除下级目标'
          : hasActual
            ? '请先删除或解除实际业绩'
            : undefined;

        return (
          <Space size="small">
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
                  title="确定删除该目标？"
                  description="删除前需确保没有下级目标或已关联的实际业绩。"
                  onConfirm={() => handleDeleteTarget(record)}
                  okText="确定"
                  cancelText="取消"
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
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16, alignItems: 'center' }}>
        <Space>
          <TrophyOutlined style={{ fontSize: 20, color: 'var(--primary-color)' }} />
          <Text strong style={{ fontSize: 16 }}>业绩目标管理</Text>
        </Space>
        <Space>
          <Select
            value={selectedYear}
            onChange={setSelectedYear}
            style={{ width: 100 }}
            options={yearOptions}
          />
          {isAdmin && (
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => {
                form.setFieldsValue({ target_year: selectedYear });
                setCreateDrawerOpen(true);
              }}
            >
              新建年度目标
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
        onRow={(record: TreeRow) => ({
          onDoubleClick: () => {
            if (record.level === 'month') {
              openEntryDrawer(record);
            }
          },
        })}
      />

      <Drawer
        title="新建年度目标"
        open={createDrawerOpen}
        onClose={() => {
          setCreateDrawerOpen(false);
          form.resetFields();
        }}
        width={520}
        destroyOnClose
      >
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
          message="年度目标规则"
          description="金额统一为万元，保留1位小数。同一销售同一年只能有一个年度目标。"
        />
        <Form form={form} layout="vertical">
          <Form.Item
            name="user_id"
            label="销售人员"
            rules={[{ required: true, message: '请选择销售人员' }]}
          >
            <Select placeholder="选择销售人员" showSearch optionFilterProp="children">
              {users
                .filter((u) => u.id !== 1)
                .map((u) => (
                  <Option key={u.id} value={u.id}>
                    {u.name}
                  </Option>
                ))}
            </Select>
          </Form.Item>
          <Form.Item name="target_year" label="年份" rules={[{ required: true }]}>
            <Select placeholder="选择年份">
              {[currentYear - 1, currentYear, currentYear + 1].map((y) => (
                <Option key={y} value={y}>
                  {y}年
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="target_amount"
            label="年度营收目标（万元）"
            rules={[{ required: true, message: '请输入目标金额' }]}
          >
            <InputNumber
              style={{ width: '100%' }}
              placeholder="输入金额"
              min={0}
              precision={1}
              addonAfter="万元"
            />
          </Form.Item>
          <Form.Item name="gross_profit_target" label="年度毛利目标（万元）">
            <InputNumber
              style={{ width: '100%' }}
              placeholder="输入毛利目标"
              min={0}
              precision={1}
              addonAfter="万元"
            />
          </Form.Item>
        </Form>
        <Button type="primary" onClick={handleCreateYear} block>
          保存
        </Button>
      </Drawer>

      <ActualEntryDrawer
        open={entryDrawer.open}
        onClose={() => setEntryDrawer((p) => ({ ...p, open: false }))}
        year={entryDrawer.year}
        month={entryDrawer.month}
        userId={entryDrawer.userId}
        targetId={entryDrawer.targetId}
        revTarget={entryDrawer.revTarget}
        gpTarget={entryDrawer.gpTarget}
        existingActual={entryDrawer.existingActual}
      />

      <QuarterSplitDrawer
        open={splitDrawer.open}
        onClose={() => setSplitDrawer((p) => ({ ...p, open: false }))}
        yearTargetId={splitDrawer.yearTargetId}
        targetYear={splitDrawer.targetYear}
        quarter={splitDrawer.quarter}
        quarterRevTarget={splitDrawer.quarterRevTarget}
        quarterGpTarget={splitDrawer.quarterGpTarget}
        onSplitSuccess={() => refetchTree()}
      />

      <Drawer
        title={`编辑目标 - ${editTarget?.periodDisplay}`}
        open={editDrawerOpen}
        onClose={() => {
          setEditDrawerOpen(false);
          setEditTarget(null);
          editForm.resetFields();
        }}
        width={400}
        destroyOnClose
      >
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
          message="目标编辑规则"
          description="修改目标金额时需确保不违反父子约束：子目标合计不能超过父目标，同级合计不能超过父目标。"
        />
        <Form form={editForm} layout="vertical">
          <Form.Item
            name="target_amount"
            label="营收目标（万元）"
            rules={[{ required: true, message: '请输入目标金额' }]}
          >
            <InputNumber
              style={{ width: '100%' }}
              placeholder="输入金额"
              min={0}
              precision={1}
              addonAfter="万元"
            />
          </Form.Item>
          <Form.Item name="gross_profit_target" label="毛利目标（万元）">
            <InputNumber
              style={{ width: '100%' }}
              placeholder="输入毛利目标"
              min={0}
              precision={1}
              addonAfter="万元"
            />
          </Form.Item>
        </Form>
        <Button type="primary" onClick={handleEditTarget} block loading={updateMutation.isPending}>
          保存
        </Button>
      </Drawer>
    </div>
  );
};

export default SalesTargetTree;
