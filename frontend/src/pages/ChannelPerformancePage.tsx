import React, { useMemo, useState } from 'react';
import {
  Alert,
  App,
  Button,
  Card,
  Col,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  Progress,
} from 'antd';
import { DeleteOutlined, DownloadOutlined, EditOutlined, PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';

import {
  ChannelPerformanceRow,
  useChannelPerformanceOverview,
  useRefreshChannelPerformance,
} from '../hooks/useChannelPerformanceOverview';
import {
  UnifiedTarget,
  useCreateUnifiedTarget,
  useDeleteUnifiedTarget,
  useUnifiedTargets,
  useUpdateUnifiedTarget,
} from '../hooks/useUnifiedTargets';
import { useChannels } from '../hooks/useChannels';
import { useManageableChannels } from '../hooks/useManageableChannels';
import { RootState } from '../store/store';

type TargetTableRow = UnifiedTarget & {
  key: string | number;
  children?: TargetTableRow[];
};

type TargetFormPayload = {
  target_type: 'channel';
  channel_id: number;
  user_id: null;
  year: number;
  quarter: number | null;
  month: null;
  performance_target: number | null;
  opportunity_target: number | null;
  project_count_target: number | null;
  development_goal: string | null;
};

type MetricField = keyof Pick<
  TargetFormPayload,
  'performance_target' | 'opportunity_target' | 'project_count_target'
>;

type TargetMetricConfig = {
  field: MetricField;
  label: string;
  unit: string;
  isAmount: boolean;
};

type MetricAnalysis = {
  metric: string;
  annual: number;
  quarterlySum: number;
  quartersCount: number;
  allQuartersComplete: boolean;
  percentage: number;
  status: 'success' | 'warning' | 'error';
  statusText: string;
  suggestion: string;
  unit: string;
  isAmount: boolean;
};

// 新增：目标验证预览组件
interface TargetValidationPreviewProps {
  channel_id: number;
  year: number;
  quarter?: number | null;
  currentValues: {
    performance_target: number | null;
    opportunity_target: number | null;
    project_count_target: number | null;
  };
  existingTargets: UnifiedTarget[];
}

const TargetValidationPreview: React.FC<TargetValidationPreviewProps> = ({
  channel_id,
  year,
  quarter,
  currentValues,
  existingTargets,
}) => {
  const annualTarget = existingTargets.find(t => 
    t.channel_id === channel_id && 
    t.year === year && 
    !t.quarter && 
    !t.month
  );

  if (!annualTarget) {
    return (
      <Alert 
        message="请先创建年目标" 
        description="需要先设置年度业绩目标，才能录入季度目标和查看配比情况" 
        type="info" 
        showIcon 
        style={{ marginBottom: 16 }} 
      />
    );
  }

  const effectiveQuarterlyTargets = buildEffectiveQuarterlyTargets(
    existingTargets,
    channel_id,
    year,
    quarter,
    currentValues
  );
  const previews = analyzeQuarterlyAllocation(annualTarget, effectiveQuarterlyTargets);

  return (
    <Card size="small" title="🎯 实时目标配比预览" style={{ marginBottom: 16 }}>
      <Space direction="vertical" size={12} style={{ width: '100%' }}>
        {previews.map((preview, index) => (
          <div key={index} style={{ padding: '8px 0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
              <span style={{ fontWeight: 500 }}>{preview.metric}</span>
              <Tag color={preview.status === 'success' ? 'green' : preview.status === 'error' ? 'red' : 'orange'}>
                {preview.statusText}
              </Tag>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#666', marginBottom: 4 }}>
              <span>年度: {(preview.annual / (preview.isAmount ? 10000 : 1)).toLocaleString('zh-CN', { 
                minimumFractionDigits: preview.isAmount ? 1 : 0,
                maximumFractionDigits: preview.isAmount ? 1 : 0 
              })}{preview.unit}</span>
              <span>季度: {(preview.quarterlySum / (preview.isAmount ? 10000 : 1)).toLocaleString('zh-CN', { 
                minimumFractionDigits: preview.isAmount ? 1 : 0,
                maximumFractionDigits: preview.isAmount ? 1 : 0 
              })}{preview.unit}</span>
              <span>{preview.quartersCount}/4 季度</span>
            </div>
            
            <Progress 
              percent={Math.round(preview.percentage)} 
              size="small" 
              status={preview.status as any}
              style={{ marginBottom: 4 }}
            />
            
            {preview.suggestion && (
              <div style={{ fontSize: '12px', color: '#888' }}>{preview.suggestion}</div>
            )}
          </div>
        ))}
      </Space>
    </Card>
  );
};

const formatAmountWan = (value: number | string | null | undefined) => {
  if (value === null || value === undefined) {
    return '-';
  }
  const normalized = Number(value);
  if (Number.isNaN(normalized)) {
    return '-';
  }
  return (normalized / 10000).toLocaleString('zh-CN', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
};

const toWanInputValue = (value: number | string | null | undefined) => {
  if (value === null || value === undefined) {
    return undefined;
  }
  const normalized = Number(value);
  if (Number.isNaN(normalized)) {
    return undefined;
  }
  return Number((normalized / 10000).toFixed(1));
};

const fromWanInputValue = (value: number | null | undefined) => {
  if (value === null || value === undefined) {
    return null;
  }
  return Math.round(value * 10000);
};

const metricLabels: Array<{
  field: MetricField;
  label: string;
}> = [
  { field: 'performance_target', label: '业绩目标' },
  { field: 'opportunity_target', label: '商机目标' },
  { field: 'project_count_target', label: '项目目标' },
];

const targetMetricConfigs: TargetMetricConfig[] = [
  { field: 'performance_target', label: '业绩目标', unit: '万元', isAmount: true },
  { field: 'opportunity_target', label: '商机目标', unit: '万元', isAmount: true },
  { field: 'project_count_target', label: '项目目标', unit: '个', isAmount: false },
];

const buildEffectiveQuarterlyTargets = (
  existingTargets: UnifiedTarget[],
  channel_id: number,
  year: number,
  quarter?: number | null,
  currentValues?: Partial<Record<MetricField, number | null>>
) => {
  let quarterlyTargets = existingTargets.filter(
    (target) =>
      target.channel_id === channel_id &&
      target.year === year &&
      target.quarter &&
      !target.month
  );

  if (quarter !== undefined && quarter !== null) {
    quarterlyTargets = quarterlyTargets.filter((target) => target.quarter !== quarter);
    quarterlyTargets.push({
      id: -1,
      target_type: 'channel',
      channel_id,
      user_id: null,
      year,
      quarter,
      month: null,
      performance_target: currentValues?.performance_target ?? null,
      opportunity_target: currentValues?.opportunity_target ?? null,
      project_count_target: currentValues?.project_count_target ?? null,
      development_goal: null,
      achieved_performance: null,
      achieved_opportunity: null,
      achieved_project_count: null,
      channel_name: null,
      user_name: null,
    });
  }

  return quarterlyTargets;
};

const analyzeQuarterlyAllocation = (
  annualTarget: UnifiedTarget | undefined,
  quarterlyTargets: UnifiedTarget[]
): MetricAnalysis[] => {
  const uniqueQuarters = new Set(
    quarterlyTargets
      .map((target) => target.quarter)
      .filter((value): value is number => value !== null && value !== undefined)
  );
  const quartersCount = uniqueQuarters.size;
  const allQuartersComplete = [1, 2, 3, 4].every((q) => uniqueQuarters.has(q));

  return targetMetricConfigs.map((metric) => {
    const annualValue = Number(annualTarget?.[metric.field] || 0);
    const quarterlySum = quarterlyTargets.reduce((sum, target) => {
      return sum + Number(target[metric.field] || 0);
    }, 0);
    const percentage = annualValue > 0 ? Math.min(100, (quarterlySum / annualValue) * 100) : 0;

    let status: MetricAnalysis['status'] = 'warning';
    let statusText = '进行中';
    let suggestion = '';

    if (allQuartersComplete) {
      if (Math.abs(quarterlySum - annualValue) < 0.01) {
        status = 'success';
        statusText = '配比完成';
      } else {
        status = 'error';
        statusText = '配比不一致';
        suggestion = `建议调整至 ${(annualValue / (metric.isAmount ? 10000 : 1)).toLocaleString('zh-CN', {
          minimumFractionDigits: metric.isAmount ? 1 : 0,
          maximumFractionDigits: metric.isAmount ? 1 : 0,
        })}${metric.unit}`;
      }
    } else if (quarterlySum > annualValue && annualValue > 0) {
      status = 'error';
      statusText = '已超限';
      suggestion = '请降低季度目标';
    } else if (quarterlySum === annualValue && quartersCount < 4 && annualValue > 0) {
      status = 'warning';
      statusText = '提前配齐';
    } else {
        const remaining = annualValue - quarterlySum;
        if (remaining > 0 && quartersCount > 0 && quartersCount < 4) {
        const avgPerQuarter = remaining / (4 - quartersCount);
        const displayValue = metric.isAmount ? avgPerQuarter / 10000 : avgPerQuarter;
        suggestion = `建议每季度约 ${displayValue.toLocaleString('zh-CN', {
          minimumFractionDigits: metric.isAmount ? 1 : 0,
          maximumFractionDigits: metric.isAmount ? 1 : 0,
        })}${metric.unit}`;
        }
      }

    return {
      metric: metric.label,
      annual: annualValue,
      quarterlySum,
      quartersCount,
      allQuartersComplete,
      percentage,
      status,
      statusText,
      suggestion,
      unit: metric.unit,
      isAmount: metric.isAmount,
    };
  });
};

const ChannelPerformancePage: React.FC = () => {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const { capabilities } = useSelector((state: RootState) => state.auth);

  const [keyword, setKeyword] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [targetFilter, setTargetFilter] = useState<string>('all');
  const [yearFilter, setYearFilter] = useState<number | undefined>(new Date().getFullYear());
  const [quarterFilter, setQuarterFilter] = useState<number | undefined>();
  const [monthFilter, setMonthFilter] = useState<number | undefined>();
  const [targetModalOpen, setTargetModalOpen] = useState(false);
  const [batchModalOpen, setBatchModalOpen] = useState(false);
  const [editingTarget, setEditingTarget] = useState<UnifiedTarget | null>(null);
  const [form] = Form.useForm();
  const [batchForm] = Form.useForm();

  const { data, isLoading, refetch } = useChannelPerformanceOverview({
    year: yearFilter,
    quarter: quarterFilter,
    month: monthFilter,
  });
  const refreshMutation = useRefreshChannelPerformance();
  const { data: channels = [] } = useManageableChannels();
  const { data: targets = [], isLoading: targetsLoading } = useUnifiedTargets({
    year: yearFilter,
    quarter: quarterFilter,
    month: monthFilter,
  });
  const createTargetMutation = useCreateUnifiedTarget();
  const updateTargetMutation = useUpdateUnifiedTarget();
  const deleteTargetMutation = useDeleteUnifiedTarget();
  const canReadPerformance = Boolean(capabilities['channel_performance:read']);
  const canManagePerformance = Boolean(capabilities['channel_performance:manage_page'] || capabilities['channel_performance:manage']);
  const hasChildTargets = (record: TargetTableRow) =>
    Boolean(record.children && record.children.length > 0);

  const rows = data?.rows || [];
  const channelTargetRows = useMemo(
    () => targets.filter((target) => target.target_type === 'channel').sort((a, b) => b.id - a.id),
    [targets]
  );
  const groupedTargetRows = useMemo<TargetTableRow[]>(() => {
    const annualTargets = new Map<string, TargetTableRow>();
    const childTargetsByGroup = new Map<string, TargetTableRow[]>();
    const topLevelRows: TargetTableRow[] = [];

    channelTargetRows.forEach((target) => {
      const row: TargetTableRow = { ...target, key: target.id };
      const groupKey = `${target.channel_id}-${target.year}`;
      const isAnnualTarget = !target.quarter && !target.month;

      if (isAnnualTarget) {
        annualTargets.set(groupKey, row);
        return;
      }

      const existingChildren = childTargetsByGroup.get(groupKey) || [];
      existingChildren.push(row);
      childTargetsByGroup.set(groupKey, existingChildren);
    });

    annualTargets.forEach((row, groupKey) => {
      const children = (childTargetsByGroup.get(groupKey) || []).sort((a, b) => {
        const quarterDiff = (a.quarter || 0) - (b.quarter || 0);
        if (quarterDiff !== 0) {
          return quarterDiff;
        }
        return (a.month || 0) - (b.month || 0);
      });
      if (children.length > 0) {
        row.children = children;
      }
      topLevelRows.push(row);
      childTargetsByGroup.delete(groupKey);
    });

    childTargetsByGroup.forEach((children) => {
      topLevelRows.push(...children);
    });

    return topLevelRows.sort((a, b) => {
      if (a.year !== b.year) {
        return b.year - a.year;
      }
      return Number(b.id) - Number(a.id);
    });
  }, [channelTargetRows]);
  const validateTargetPayload = (
    payload: TargetFormPayload,
    options?: { excludeId?: number }
  ): string | null => {
    const scopedTargets = channelTargetRows.filter(
      (target) =>
        target.channel_id === payload.channel_id &&
        target.year === payload.year &&
        (!options?.excludeId || target.id !== options.excludeId)
    );

    const annualTarget =
      scopedTargets.find((target) => !target.quarter && !target.month) || null;
    const quarterlyTargets = scopedTargets.filter((target) => Boolean(target.quarter) && !target.month);

    if (!payload.quarter) {
      if (annualTarget) {
        return '同一渠道同一年只能有一个年目标';
      }

      const simulatedAnnualTarget: UnifiedTarget = {
        id: -1,
        target_type: 'channel',
        channel_id: payload.channel_id,
        user_id: null,
        year: payload.year,
        quarter: null,
        month: null,
        performance_target: payload.performance_target,
        opportunity_target: payload.opportunity_target,
        project_count_target: payload.project_count_target,
        development_goal: payload.development_goal,
        achieved_performance: null,
        achieved_opportunity: null,
        achieved_project_count: null,
        channel_name: null,
        user_name: null,
      };
      const analysis = analyzeQuarterlyAllocation(simulatedAnnualTarget, quarterlyTargets);
      for (const item of analysis) {
        if (item.status === 'error' && item.statusText === '已超限') {
          return `已有季度${item.metric}合计不能超过年${item.metric}`;
        }
        if (item.status === 'error' && item.statusText === '配比不一致') {
          return `Q1-Q4 ${item.metric}合计必须等于年${item.metric}`;
        }
      }
      return null;
    }

    if (![1, 2, 3, 4].includes(payload.quarter)) {
      return '季度只能是 Q1-Q4';
    }

    if (!annualTarget && !editingTarget) {
      return '请先创建年目标，再创建季度目标';
    }

    const referenceAnnualTarget = annualTarget;

    if (!referenceAnnualTarget || referenceAnnualTarget.quarter) {
      return '请先创建年目标，再创建季度目标';
    }

    const duplicateQuarter = quarterlyTargets.find(
      (target) => target.quarter === payload.quarter
    );
    if (duplicateQuarter) {
      return `Q${payload.quarter} 目标已存在，不能重复创建`;
    }

    for (const metric of metricLabels) {
      const currentValue = Number(payload[metric.field] || 0);
      const annualValue = Number(referenceAnnualTarget[metric.field] || 0);
      if (currentValue > 0 && annualValue <= 0) {
        return `请先设置年${metric.label}，再设置季度${metric.label}`;
      }
      if (currentValue > annualValue && annualValue > 0) {
        return `单季度${metric.label}不能超过年${metric.label}`;
      }
    }

    const effectiveQuarterlyTargets = buildEffectiveQuarterlyTargets(
      scopedTargets,
      payload.channel_id,
      payload.year,
      payload.quarter,
      {
        performance_target: payload.performance_target,
        opportunity_target: payload.opportunity_target,
        project_count_target: payload.project_count_target,
      }
    );
    const analysis = analyzeQuarterlyAllocation(referenceAnnualTarget, effectiveQuarterlyTargets);
    for (const item of analysis) {
      if (item.status === 'error' && item.statusText === '已超限') {
        return `季度${item.metric}合计不能超过年${item.metric}`;
      }
      if (item.status === 'error' && item.statusText === '配比不一致') {
        return `Q1-Q4 ${item.metric}合计必须等于年${item.metric}`;
      }
    }

    return null;
  };
  const filteredRows = useMemo(() => {
    const text = keyword.trim().toLowerCase();
    return rows.filter((row) => {
      const textMatched =
        !text ||
        row.company_name.toLowerCase().includes(text) ||
        row.channel_code.toLowerCase().includes(text) ||
        row.channel_type.toLowerCase().includes(text);
      const statusMatched = statusFilter === 'all' || row.status === statusFilter;
      const targetMatched =
        targetFilter === 'all' ||
        (targetFilter === 'met' && row.is_target_met) ||
        (targetFilter === 'unmet' && row.completion_rate !== null && !row.is_target_met) ||
        (targetFilter === 'no_target' && row.completion_rate === null);
      return textMatched && statusMatched && targetMatched;
    });
  }, [keyword, rows, statusFilter, targetFilter]);

  const statusOptions = useMemo(() => {
    const values = Array.from(new Set(rows.map((row) => row.status).filter(Boolean)));
    return values.map((value) => ({ label: value, value }));
  }, [rows]);

  const exportCsv = () => {
    if (filteredRows.length === 0) {
      message.warning('没有可导出的数据');
      return;
    }
    const headers = [
      '渠道编号',
      '渠道名称',
      '渠道类型',
      '状态',
      '客户数',
      '线索数',
      '商机数',
      '项目数',
      '累计签约额(万元)',
      '业绩目标(万元)',
      '业绩完成(万元)',
      '达成率',
    ];
    const lines = filteredRows.map((row) => [
      row.channel_code,
      row.company_name,
      row.channel_type || '',
      row.status || '',
      row.customers_count,
      row.leads_count,
      row.opportunities_count,
      row.projects_count,
      formatAmountWan(row.total_contract_amount),
      formatAmountWan(row.performance_target),
      formatAmountWan(row.achieved_performance),
      row.completion_rate ?? '',
    ]);
    const csv = [headers, ...lines]
      .map((line) =>
        line.map((cell) => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(',')
      )
      .join('\n');
    const blob = new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `channel-performance-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  const handleRefreshSingle = async (channelId: number) => {
    try {
      await refreshMutation.mutateAsync(channelId);
      message.success('已刷新该渠道业绩');
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '刷新失败');
    }
  };

  const openCreateTargetModal = () => {
    setEditingTarget(null);
    form.resetFields();
    form.setFieldsValue({
      target_type: 'channel',
      year: yearFilter ?? new Date().getFullYear(),
      quarter: quarterFilter ?? null,
    });
    setTargetModalOpen(true);
  };

  const openEditTargetModal = (target: UnifiedTarget) => {
    setEditingTarget(target);
    form.setFieldsValue({
      ...target,
      performance_target: toWanInputValue(target.performance_target),
      opportunity_target: toWanInputValue(target.opportunity_target),
      project_count_target: target.project_count_target ?? undefined,
    });
    setTargetModalOpen(true);
  };

  const handleSaveTarget = async () => {
    try {
      const values = await form.validateFields();
      const payload = {
        target_type: 'channel' as const,
        channel_id: values.channel_id,
        user_id: null,
        year: values.year,
        quarter: values.quarter ?? null,
        month: null,
        performance_target: fromWanInputValue(values.performance_target),
        opportunity_target: fromWanInputValue(values.opportunity_target),
        project_count_target: values.project_count_target ?? null,
        development_goal: values.development_goal ?? null,
      };
      const validationError = validateTargetPayload(payload, {
        excludeId: editingTarget?.id,
      });
      if (validationError) {
        message.error(validationError);
        return;
      }

      if (editingTarget) {
        await updateTargetMutation.mutateAsync({ id: editingTarget.id, payload });
        message.success('业绩目标已更新');
      } else {
        await createTargetMutation.mutateAsync(payload);
        message.success('业绩目标已创建');
      }

      setTargetModalOpen(false);
      setEditingTarget(null);
      form.resetFields();
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  const handleDeleteTarget = async (targetId: number) => {
    try {
      await deleteTargetMutation.mutateAsync(targetId);
      message.success('业绩目标已删除');
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '删除失败');
    }
  };

  const openBatchModal = () => {
    batchForm.resetFields();
      batchForm.setFieldsValue({
        channel_ids: filteredRows.map((row) => row.channel_id),
        year: yearFilter ?? new Date().getFullYear(),
        quarter: quarterFilter ?? null,
      });
    setBatchModalOpen(true);
  };

  const handleBatchAssign = async () => {
    try {
      const values = await batchForm.validateFields();
      const channelIds: number[] = values.channel_ids || [];
      if (channelIds.length === 0) {
        message.error('请至少选择一个渠道');
        return;
      }

      const payloads = channelIds.map((channelId) => ({
        target_type: 'channel' as const,
        channel_id: channelId,
        user_id: null,
        year: values.year,
        quarter: values.quarter ?? null,
        month: null,
        performance_target: fromWanInputValue(values.performance_target),
        opportunity_target: fromWanInputValue(values.opportunity_target),
        project_count_target: values.project_count_target ?? null,
        development_goal: values.development_goal ?? null,
      }));

      for (const payload of payloads) {
        const validationError = validateTargetPayload(payload);
        if (validationError) {
          const channel = channels.find((item) => item.id === payload.channel_id);
          message.error(
            `${channel?.company_name || `渠道#${payload.channel_id}`}: ${validationError}`
          );
          return;
        }
      }

      await Promise.all(
        payloads.map((payload) => createTargetMutation.mutateAsync(payload))
      );

      message.success(`已为 ${channelIds.length} 个渠道批量分配业绩目标`);
      setBatchModalOpen(false);
      batchForm.resetFields();
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail);
      }
    }
  };

  const columns = [
    {
      title: '渠道',
      key: 'channel',
      width: 220,
      render: (_: unknown, record: ChannelPerformanceRow) => (
        <div>
          <div style={{ fontWeight: 600 }}>{record.company_name}</div>
          <div style={{ color: '#999' }}>{record.channel_code}</div>
        </div>
      ),
    },
    {
      title: '类型/状态',
      key: 'meta',
      width: 150,
      render: (_: unknown, record: ChannelPerformanceRow) => (
        <Space direction="vertical" size={2}>
          <Tag color="geekblue">{record.channel_type || '-'}</Tag>
          <Tag color={record.status === '合作中' ? 'green' : 'default'}>{record.status || '-'}</Tag>
        </Space>
      ),
    },
    {
      title: '客户/线索/商机/项目',
      key: 'pipeline',
      width: 190,
      render: (_: unknown, record: ChannelPerformanceRow) =>
        `${record.customers_count}/${record.leads_count}/${record.opportunities_count}/${record.projects_count}`,
    },
    {
      title: '累计签约额(万元)',
      dataIndex: 'total_contract_amount',
      key: 'total_contract_amount',
      width: 140,
      render: (value: number) => formatAmountWan(value),
    },
    {
      title: '业绩目标(万元)',
      dataIndex: 'performance_target',
      key: 'performance_target',
      width: 130,
      render: (value: number | null) => formatAmountWan(value),
    },
    {
      title: '实际完成(万元)',
      dataIndex: 'achieved_performance',
      key: 'achieved_performance',
      width: 130,
      render: (value: number | null) => formatAmountWan(value),
    },
    {
      title: '达成率',
      dataIndex: 'completion_rate',
      key: 'completion_rate',
      width: 110,
      render: (value: number | null) => {
        if (value === null) {
          return '-';
        }
        return <Tag color={value >= 100 ? 'green' : value >= 70 ? 'blue' : 'orange'}>{value}%</Tag>;
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 190,
      render: (_: unknown, record: ChannelPerformanceRow) => (
        <Space>
          <Button size="small" onClick={() => navigate(`/channels/${record.channel_id}/full`)}>
            查看档案
          </Button>
          <Button
            size="small"
            icon={<ReloadOutlined />}
            loading={refreshMutation.isPending}
            disabled={!record.can_edit}
            onClick={() => handleRefreshSingle(record.channel_id)}
          >
            刷新业绩
          </Button>
        </Space>
      ),
    },
  ];

  const targetColumns = [
    {
      title: '渠道',
      key: 'channel',
      width: 220,
      render: (_: unknown, record: TargetTableRow) => (
        <div>
          <div style={{ fontWeight: 600 }}>{record.channel_name || `渠道#${record.channel_id}`}</div>
          <div style={{ color: '#999' }}>
            {record.year}年
            {record.quarter ? ` Q${record.quarter}` : ''}
            {record.month ? ` / ${record.month}月` : ''}
          </div>
        </div>
      ),
    },
    {
      title: '业绩目标(万元)',
      dataIndex: 'performance_target',
      key: 'performance_target',
      width: 140,
      render: (value: number | null) => formatAmountWan(value),
    },
    {
      title: '商机目标(万元)',
      dataIndex: 'opportunity_target',
      key: 'opportunity_target',
      width: 120,
      render: (value: number | null) => formatAmountWan(value),
    },
    {
      title: '项目目标',
      dataIndex: 'project_count_target',
      key: 'project_count_target',
      width: 100,
      render: (value: number | null) => value ?? '-',
    },
    {
      title: '实际完成(万元)',
      dataIndex: 'achieved_performance',
      key: 'achieved_performance',
      width: 140,
      render: (value: number | null) => formatAmountWan(value),
    },
    {
      title: '发展目标',
      dataIndex: 'development_goal',
      key: 'development_goal',
      ellipsis: true,
    },
    ...(canManagePerformance
      ? [
          {
            title: '操作',
            key: 'actions',
            width: 140,
            render: (_: unknown, record: TargetTableRow) => (
              <Space>
                <Button size="small" icon={<EditOutlined />} onClick={() => openEditTargetModal(record)}>
                  编辑
                </Button>
                <Popconfirm
                  title={
                    hasChildTargets(record)
                      ? '请先删除该年目标下的季度目标'
                      : '确定删除该业绩目标？'
                  }
                  onConfirm={() => handleDeleteTarget(record.id)}
                  disabled={hasChildTargets(record)}
                >
                  <Button
                    size="small"
                    danger
                    icon={<DeleteOutlined />}
                    disabled={hasChildTargets(record)}
                    title={hasChildTargets(record) ? '请先删除季度目标后再删除年目标' : undefined}
                  />
                </Popconfirm>
              </Space>
            ),
          },
        ]
      : []),
  ];

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      {!canReadPerformance && (
        <Alert
          type="warning"
          showIcon
          message="当前账号无渠道业绩查看权限"
          description="如需开通，请联系管理员配置 channel_performance:read 能力。"
        />
      )}
      {canManagePerformance && (
        <Card
          title="管理操作"
          extra={<Tag color="blue">渠道业绩分配</Tag>}
        >
          <Space wrap>
            <Button type="primary" size="large" icon={<PlusOutlined />} onClick={openCreateTargetModal}>
              新增业绩目标
            </Button>
            <Button size="large" icon={<PlusOutlined />} onClick={openBatchModal}>
              批量分配目标
            </Button>
          </Space>
        </Card>
      )}
      <Row gutter={16}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="渠道数量" value={data?.channel_count || 0} />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="累计签约额(万元)"
              value={formatAmountWan(data?.total_contract_amount || 0)}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="平均达成率" value={data?.avg_completion_rate || 0} suffix="%" />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="达标渠道数" value={data?.target_met_count || 0} />
          </Card>
        </Col>
      </Row>

      <Card
        title="渠道业绩明细"
        extra={
          <Space>
            <Input.Search
              allowClear
              placeholder="搜索渠道名称/编号/类型"
              onSearch={setKeyword}
              onChange={(event) => setKeyword(event.target.value)}
              style={{ width: 260 }}
            />
            <Select
              value={yearFilter}
              allowClear
              onChange={(value) => setYearFilter(value)}
              style={{ width: 120 }}
              options={Array.from({ length: 6 }, (_, index) => {
                const year = new Date().getFullYear() - 1 + index;
                return { value: year, label: `${year}年` };
              })}
            />
            <Select
              value={quarterFilter}
              allowClear
              onChange={(value) => {
                setQuarterFilter(value);
                if (!value) {
                  setMonthFilter(undefined);
                }
              }}
              style={{ width: 120 }}
              options={[
                { value: 1, label: 'Q1' },
                { value: 2, label: 'Q2' },
                { value: 3, label: 'Q3' },
                { value: 4, label: 'Q4' },
              ]}
            />
            <Select
              value={monthFilter}
              allowClear
              onChange={(value) => setMonthFilter(value)}
              style={{ width: 120 }}
              options={Array.from({ length: 12 }, (_, index) => ({
                value: index + 1,
                label: `${index + 1}月`,
              }))}
            />
            <Select
              value={statusFilter}
              onChange={setStatusFilter}
              style={{ width: 140 }}
              options={[{ label: '全部状态', value: 'all' }, ...statusOptions]}
            />
            <Select
              value={targetFilter}
              onChange={setTargetFilter}
              style={{ width: 140 }}
              options={[
                { label: '目标全部', value: 'all' },
                { label: '已达标', value: 'met' },
                { label: '未达标', value: 'unmet' },
                { label: '未设置目标', value: 'no_target' },
              ]}
            />
            <Button icon={<DownloadOutlined />} onClick={exportCsv}>
              导出CSV
            </Button>
            <Button icon={<ReloadOutlined />} loading={isLoading} onClick={() => refetch()}>
              刷新列表
            </Button>
          </Space>
        }
      >
        <Table
          rowKey="channel_id"
          loading={isLoading}
          columns={columns}
          dataSource={filteredRows}
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1200 }}
          locale={{ emptyText: '暂无可展示的渠道业绩数据' }}
        />
      </Card>

      <Card
        title="业绩分配与管理"
        extra={
          canManagePerformance ? (
            <Space>
              <Button icon={<PlusOutlined />} onClick={openBatchModal}>
                批量分配
              </Button>
              <Button type="primary" icon={<PlusOutlined />} onClick={openCreateTargetModal}>
                新增业绩目标
              </Button>
            </Space>
          ) : null
        }
      >
        <Table
          rowKey="key"
          loading={targetsLoading}
          columns={targetColumns}
          dataSource={groupedTargetRows}
          pagination={{ pageSize: 8 }}
          scroll={{ x: 1100 }}
          expandable={{
            rowExpandable: (record) => Boolean(record.children && record.children.length > 0),
          }}
          locale={{ emptyText: '暂无渠道业绩目标，请先分配目标' }}
        />
      </Card>

        <Modal
          title={editingTarget ? '编辑业绩目标' : '新增业绩目标'}
          open={targetModalOpen}
          onOk={handleSaveTarget}
          onCancel={() => {
            setTargetModalOpen(false);
            setEditingTarget(null);
          }}
          confirmLoading={createTargetMutation.isPending || updateTargetMutation.isPending}
          forceRender
          destroyOnClose
        >
          <Form form={form} layout="vertical">
            <Alert
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
              message="录入规则"
              description="请先创建年目标，再创建季度目标。Q1-Q4 不能重复；四个季度齐全时，各项季度目标合计必须等于年目标；未配齐时合计不能超过年目标。金额单位统一为万元，保留 1 位小数。"
            />
            
            {/* 新增：实时目标配比预览 */}
            <Form.Item shouldUpdate>
              {() => {
                const channel_id = form.getFieldValue('channel_id');
                const year = form.getFieldValue('year');
                const quarter = form.getFieldValue('quarter');
                
                const currentValues = {
                  performance_target: fromWanInputValue(form.getFieldValue('performance_target')),
                  opportunity_target: fromWanInputValue(form.getFieldValue('opportunity_target')),
                  project_count_target: form.getFieldValue('project_count_target'),
                };
                
                return (
                  <TargetValidationPreview
                    channel_id={channel_id}
                    year={year}
                    quarter={quarter}
                    currentValues={currentValues}
                    existingTargets={channelTargetRows}
                  />
                );
              }}
            </Form.Item>
            
            <Form.Item
              name="channel_id"
              label="渠道"
              rules={[{ required: true, message: '请选择渠道' }]}
            >
            <Select
              showSearch
              optionFilterProp="label"
              options={channels.map((channel) => ({
                value: channel.id,
                label: `${channel.channel_code} - ${channel.company_name}`,
              }))}
            />
          </Form.Item>
          <Space style={{ width: '100%' }} size="middle" wrap>
            <Form.Item name="year" label="年份" rules={[{ required: true, message: '请输入年份' }]}>
              <InputNumber min={2020} max={2100} style={{ width: 120 }} />
            </Form.Item>
            <Form.Item name="quarter" label="季度">
              <Select
                allowClear
                style={{ width: 120 }}
                options={[
                  { value: 1, label: 'Q1' },
                  { value: 2, label: 'Q2' },
                  { value: 3, label: 'Q3' },
                  { value: 4, label: 'Q4' },
                ]}
              />
            </Form.Item>
          </Space>
          <Space style={{ width: '100%' }} size="middle" wrap>
            <Form.Item name="performance_target" label="业绩目标（万元）">
              <InputNumber min={0} precision={1} style={{ width: 180 }} />
            </Form.Item>
            <Form.Item name="opportunity_target" label="商机目标（万元）">
              <InputNumber min={0} precision={1} style={{ width: 180 }} />
            </Form.Item>
            <Form.Item name="project_count_target" label="项目目标数">
              <InputNumber min={0} style={{ width: 140 }} />
            </Form.Item>
          </Space>
          <Form.Item name="development_goal" label="发展目标">
            <Input.TextArea rows={4} placeholder="填写该渠道阶段发展目标" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="批量分配业绩目标"
        open={batchModalOpen}
        onOk={handleBatchAssign}
        onCancel={() => setBatchModalOpen(false)}
        confirmLoading={createTargetMutation.isPending}
        forceRender
        destroyOnClose
      >
        <Form form={batchForm} layout="vertical">
          <Alert
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
            message="批量分配规则"
            description="批量分配也会按单渠道逐条校验。若某个渠道缺少年目标、季度重复、或季度合计超出年目标，将直接阻止本次提交。金额单位统一为万元，保留 1 位小数。"
          />
          <Form.Item
            name="channel_ids"
            label="渠道"
            rules={[{ required: true, message: '请选择至少一个渠道' }]}
          >
            <Select
              mode="multiple"
              showSearch
              optionFilterProp="label"
              options={filteredRows.map((row) => ({
                value: row.channel_id,
                label: `${row.channel_code} - ${row.company_name}`,
              }))}
            />
          </Form.Item>
          <Space style={{ width: '100%' }} size="middle" wrap>
            <Form.Item name="year" label="年份" rules={[{ required: true, message: '请输入年份' }]}>
              <InputNumber min={2020} max={2100} style={{ width: 120 }} />
            </Form.Item>
            <Form.Item name="quarter" label="季度">
              <Select
                allowClear
                style={{ width: 120 }}
                options={[
                  { value: 1, label: 'Q1' },
                  { value: 2, label: 'Q2' },
                  { value: 3, label: 'Q3' },
                  { value: 4, label: 'Q4' },
                ]}
              />
            </Form.Item>
          </Space>
          <Space style={{ width: '100%' }} size="middle" wrap>
            <Form.Item name="performance_target" label="业绩目标（万元）">
              <InputNumber min={0} precision={1} style={{ width: 180 }} />
            </Form.Item>
            <Form.Item name="opportunity_target" label="商机目标（万元）">
              <InputNumber min={0} precision={1} style={{ width: 180 }} />
            </Form.Item>
            <Form.Item name="project_count_target" label="项目目标数">
              <InputNumber min={0} style={{ width: 140 }} />
            </Form.Item>
          </Space>
          <Form.Item name="development_goal" label="发展目标">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </Space>
  );
};

export default ChannelPerformancePage;
