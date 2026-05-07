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
import SidebarDrawer from '../common/SidebarDrawer';
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

export interface ActualEntryDrawerProps {
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

const ActualEntryDrawer: React.FC<ActualEntryDrawerProps> = ({
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
      if (pct >= 100) return { emoji: '🚀', label: '超额', color: 'var(--success-color)', icon: <RocketOutlined /> };
      if (pct >= 80) return { emoji: '✅', label: '达标', color: 'var(--primary-color)', icon: <CheckCircleOutlined /> };
      return { emoji: '💤', label: '不足', color: 'var(--error-color)', icon: <PauseCircleOutlined /> };
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
  };

  return (
    <SidebarDrawer
      title={`填报实际业绩 - ${year}年${month}月`}
      open={open}
      onClose={onClose}
      width={520}
      footer={
        <Space style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button onClick={onClose}>取消</Button>
          <Button
            type="primary"
            loading={createMutation.isPending || updateMutation.isPending}
            onClick={handleSubmit}
          >
            提交
          </Button>
        </Space>
      }
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
          label="实际营收（万元）"
          rules={[{ required: true, message: '请输入实际营收金额' }]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="请输入实际营收"
            min={0}
            precision={1}
            addonAfter="万元"
          />
        </Form.Item>

        <Form.Item
          name="gross_profit_actual"
          label="实际毛利（万元）"
          rules={[{ required: true, message: '请输入实际毛利金额' }]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="请输入实际毛利"
            min={0}
            precision={1}
            addonAfter="万元"
          />
        </Form.Item>

        <Divider style={{ margin: '16px 0' }} />

        <Title level={5} style={{ marginBottom: 12 }}>
          与目标对比
        </Title>

        {revTarget != null && revTarget > 0 && (
          <div
            style={{
              background: '#f8fafc',
              borderRadius: 8,
              padding: 12,
              marginBottom: 12,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <Text type="secondary">营收目标</Text>
              <Text strong>{formatWan(revTarget)} 万元</Text>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <Text type="secondary">实际营收</Text>
              <Text strong>{formatWan(comparison.rev.diff + revTarget)} 万元</Text>
            </div>
            <Divider style={{ margin: '8px 0' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text type="secondary">差额</Text>
              <Space>
                {comparison.rev.status.icon}
                <Text
                  style={{
                    color: comparison.rev.status.color,
                    fontWeight: 600,
                  }}
                >
                  {comparison.rev.diff >= 0 ? '+' : ''}
                  {formatWan(comparison.rev.diff)} 万元
                </Text>
              </Space>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text type="secondary">完成率</Text>
              <Statistic
                value={comparison.rev.pct}
                precision={1}
                suffix="%"
                valueStyle={{
                  color: comparison.rev.status.color,
                  fontSize: 16,
                }}
              />
            </div>
          </div>
        )}

        {gpTarget != null && gpTarget > 0 && (
          <div
            style={{
              background: '#f8fafc',
              borderRadius: 8,
              padding: 12,
              marginBottom: 12,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <Text type="secondary">毛利目标</Text>
              <Text strong>{formatWan(gpTarget)} 万元</Text>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <Text type="secondary">实际毛利</Text>
              <Text strong>{formatWan(comparison.gp.diff + gpTarget)} 万元</Text>
            </div>
            <Divider style={{ margin: '8px 0' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text type="secondary">差额</Text>
              <Space>
                {comparison.gp.status.icon}
                <Text
                  style={{
                    color: comparison.gp.status.color,
                    fontWeight: 600,
                  }}
                >
                  {comparison.gp.diff >= 0 ? '+' : ''}
                  {formatWan(comparison.gp.diff)} 万元
                </Text>
              </Space>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text type="secondary">完成率</Text>
              <Statistic
                value={comparison.gp.pct}
                precision={1}
                suffix="%"
                valueStyle={{
                  color: comparison.gp.status.color,
                  fontSize: 16,
                }}
              />
            </div>
          </div>
        )}

        {(!revTarget || revTarget <= 0) && (!gpTarget || gpTarget <= 0) && (
          <Text type="secondary" style={{ textAlign: 'center', display: 'block' }}>
            暂无目标数据，请先设置目标
          </Text>
        )}
      </Form>
    </SidebarDrawer>
  );
};

export default ActualEntryDrawer;
