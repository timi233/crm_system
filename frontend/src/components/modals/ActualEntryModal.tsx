import React, { useCallback, useMemo, useState } from 'react';
import {
  Button,
  Form,
  InputNumber,
  Space,
  Statistic,
  Typography,
  Divider,
} from 'antd';
import {
  RocketOutlined,
  CheckCircleOutlined,
  PauseCircleOutlined,
} from '@ant-design/icons';
import PageModal from '../common/PageModal';
import { useCreateActual, useUpdateActual } from '../../hooks/useSalesTargets';

const { Text, Title } = Typography;

const toWanInputValue = (value: number | null | undefined) => {
  if (value === null || value === undefined) return undefined;
  return Number((Number(value) / 10000).toFixed(1));
};

const fromWanInputValue = (value: number | null | undefined) => {
  if (value === null || value === undefined) return 0;
  return Math.round(Number(value) * 10000);
};

const formatWan = (value: number | null | undefined) => {
  if (value === null || value === undefined) return '-';
  return (Number(value) / 10000).toLocaleString('zh-CN', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
};

export interface ActualEntryModalProps {
  open: boolean;
  onClose: () => void;
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
}

const ActualEntryModal: React.FC<ActualEntryModalProps> = ({
  open,
  onClose,
  year,
  month,
  userId,
  targetId,
  revTarget,
  gpTarget,
  existingActual,
}) => {
  const [form] = Form.useForm();
  const [currentValues, setCurrentValues] = useState<{
    amount_actual?: number;
    gross_profit_actual?: number;
  }>({});

  const createMutation = useCreateActual();
  const updateMutation = useUpdateActual();

  const handleFormValuesChange = useCallback(
    (_changed: unknown, all: {
      amount_actual?: number;
      gross_profit_actual?: number;
    }) => {
      setCurrentValues({
        amount_actual: fromWanInputValue(all.amount_actual),
        gross_profit_actual: fromWanInputValue(all.gross_profit_actual),
      });
    },
    [],
  );

  const comparison = useMemo(() => {
    const actualRev = currentValues.amount_actual ?? 0;
    const actualGp = currentValues.gross_profit_actual ?? 0;

    const revDiff = revTarget ? actualRev - revTarget : 0;
    const gpDiff = gpTarget ? actualGp - gpTarget : 0;
    const revPct = revTarget ? (actualRev / revTarget) * 100 : 0;
    const gpPct = gpTarget ? (actualGp / gpTarget) * 100 : 0;

    const getStatus = (pct: number) => {
      if (pct >= 100) return { emoji: '🚀', label: '超额', color: '#10B981', icon: <RocketOutlined /> };
      if (pct >= 80) return { emoji: '✅', label: '达标', color: '#0052cc', icon: <CheckCircleOutlined /> };
      return { emoji: '💤', label: '不足', color: '#EF4444', icon: <PauseCircleOutlined /> };
    };

    return {
      rev: {
        diff: revDiff,
        pct: revPct,
        status: getStatus(revPct),
      },
      gp: {
        diff: gpDiff,
        pct: gpPct,
        status: getStatus(gpPct),
      },
    };
  }, [currentValues, revTarget, gpTarget]);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const payload = {
        user_id: userId,
        year,
        month,
        amount_actual: fromWanInputValue(values.amount_actual),
        gross_profit_actual: fromWanInputValue(values.gross_profit_actual),
        target_id: targetId ?? null,
      };

      if (existingActual) {
        await updateMutation.mutateAsync({
          id: existingActual.id,
          data: {
            amount_actual: payload.amount_actual,
            gross_profit_actual: payload.gross_profit_actual,
          },
        });
      } else {
        await createMutation.mutateAsync(payload);
      }

      form.resetFields();
      onClose();
    } catch (e) {}
  };

  return (
    <PageModal
      title={`业绩填报 · ${year}年${month}月`}
      open={open}
      onClose={onClose}
      width={560}
      footer={[
        <Button key="cancel" onClick={onClose}>
          取消
        </Button>,
        <Button
          key="submit"
          type="primary"
          className="btn--gradient"
          loading={createMutation.isPending || updateMutation.isPending}
          onClick={handleSubmit}
        >
          确认提交
        </Button>
      ]}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={
          existingActual
            ? {
                amount_actual: toWanInputValue(existingActual.amount_actual),
                gross_profit_actual: toWanInputValue(
                  existingActual.gross_profit_actual,
                ),
              }
            : undefined
        }
        onValuesChange={handleFormValuesChange}
      >
        <Form.Item
          name="amount_actual"
          label="当月实际营收（万元）"
          rules={[{ required: true, message: '请输入实际营收金额' }]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="0.0"
            min={0}
            precision={1}
            addonAfter="万元"
          />
        </Form.Item>

        <Form.Item
          name="gross_profit_actual"
          label="当月实际毛利（万元）"
          rules={[{ required: true, message: '请输入实际毛利金额' }]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="0.0"
            min={0}
            precision={1}
            addonAfter="万元"
          />
        </Form.Item>

        <Divider style={{ margin: '24px 0' }}>目标对比分析</Divider>

        {revTarget != null && revTarget > 0 && (
          <div
            style={{
              background: '#f8fafc',
              borderRadius: 12,
              padding: '16px 20px',
              marginBottom: 16,
              border: '1px solid #f1f5f9'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <Text type="secondary" style={{ fontSize: 13 }}>营收目标</Text>
              <Text strong>{formatWan(revTarget)} 万元</Text>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
              <Text type="secondary" style={{ fontSize: 13 }}>实际营收</Text>
              <Text strong style={{ color: comparison.rev.status.color }}>{formatWan(comparison.rev.diff + revTarget)} 万元</Text>
            </div>
            <div style={{ height: 1, background: '#e2e8f0', margin: '0 0 12px 0' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Space>
                <div style={{
                  width: 24,
                  height: 24,
                  borderRadius: '50%',
                  background: comparison.rev.status.color + '15',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: comparison.rev.status.color
                }}>
                  {comparison.rev.status.icon}
                </div>
                <Text style={{ fontSize: 13, color: '#64748b' }}>业绩差距</Text>
              </Space>
              <Text
                style={{
                  color: comparison.rev.status.color,
                  fontWeight: 700,
                }}
              >
                {comparison.rev.diff >= 0 ? '+' : ''}
                {formatWan(comparison.rev.diff)} 万元
              </Text>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
              <Text style={{ fontSize: 13, color: '#64748b' }}>完成进度</Text>
              <Statistic
                value={comparison.rev.pct}
                precision={1}
                suffix="%"
                valueStyle={{
                  color: comparison.rev.status.color,
                  fontSize: 18,
                  fontWeight: 800,
                }}
              />
            </div>
          </div>
        )}

        {gpTarget != null && gpTarget > 0 && (
          <div
            style={{
              background: '#f8fafc',
              borderRadius: 12,
              padding: '16px 20px',
              border: '1px solid #f1f5f9'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <Text type="secondary" style={{ fontSize: 13 }}>毛利目标</Text>
              <Text strong>{formatWan(gpTarget)} 万元</Text>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
              <Text type="secondary" style={{ fontSize: 13 }}>实际毛利</Text>
              <Text strong style={{ color: comparison.gp.status.color }}>{formatWan(comparison.gp.diff + gpTarget)} 万元</Text>
            </div>
            <div style={{ height: 1, background: '#e2e8f0', margin: '0 0 12px 0' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Space>
                <div style={{
                  width: 24,
                  height: 24,
                  borderRadius: '50%',
                  background: comparison.gp.status.color + '15',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: comparison.gp.status.color
                }}>
                  {comparison.gp.status.icon}
                </div>
                <Text style={{ fontSize: 13, color: '#64748b' }}>业绩差距</Text>
              </Space>
              <Text
                style={{
                  color: comparison.gp.status.color,
                  fontWeight: 700,
                }}
              >
                {comparison.gp.diff >= 0 ? '+' : ''}
                {formatWan(comparison.gp.diff)} 万元
              </Text>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
              <Text style={{ fontSize: 13, color: '#64748b' }}>完成进度</Text>
              <Statistic
                value={comparison.gp.pct}
                precision={1}
                suffix="%"
                valueStyle={{
                  color: comparison.gp.status.color,
                  fontSize: 18,
                  fontWeight: 800,
                }}
              />
            </div>
          </div>
        )}

        {(!revTarget || revTarget <= 0) && (!gpTarget || gpTarget <= 0) && (
          <div style={{ textAlign: 'center', padding: '24px 0' }}>
            <Text type="secondary">暂无目标数据，请先在系统中设置年度/季度目标</Text>
          </div>
        )}
      </Form>
    </PageModal>
  );
};

export default ActualEntryModal;
