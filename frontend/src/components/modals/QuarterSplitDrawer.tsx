import React, { useCallback, useMemo, useState } from 'react';
import {
  Button,
  Card,
  InputNumber,
  Space,
  Typography,
  Divider,
  Row,
  Col,
  Tag,
} from 'antd';
import { CheckCircleOutlined, WarningOutlined } from '@ant-design/icons';
import SidebarDrawer from '../common/SidebarDrawer';
import { useDecomposeTarget } from '../../hooks/useSalesTargets';

const { Text, Title } = Typography;

const QUARTER_MONTHS: Record<number, number[]> = {
  1: [1, 2, 3],
  2: [4, 5, 6],
  3: [7, 8, 9],
  4: [10, 11, 12],
};

const toWanInput = (v: number) =>
  Number((v / 10000).toFixed(1));

const fromWanInput = (v: number | null | undefined) => {
  if (v === null || v === undefined) return 0;
  return Math.round(v * 10000);
};

const fmtWan = (v: number) =>
  (v / 10000).toLocaleString('zh-CN', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });

interface MonthValues {
  rev: Record<number, number | undefined>;
  gp: Record<number, number | undefined>;
}

export interface QuarterSplitDrawerProps {
  open: boolean;
  onClose: () => void;
  yearTargetId: number;
  targetYear: number;
  quarter: number;
  quarterRevTarget: number;
  quarterGpTarget: number;
  existingMonths?: {
    month: number;
    target_amount: number;
    gross_profit_target: number;
  }[];
  onSplitSuccess?: () => void;
}

const QuarterSplitDrawer: React.FC<QuarterSplitDrawerProps> = ({
  open,
  onClose,
  yearTargetId,
  targetYear,
  quarter,
  quarterRevTarget,
  quarterGpTarget,
  existingMonths,
  onSplitSuccess,
}) => {
  const decomposeMutation = useDecomposeTarget();

  const months = QUARTER_MONTHS[quarter] || [];

  const [values, setValues] = useState<MonthValues>(() => {
    const init: MonthValues = { rev: {}, gp: {} };
    const avgRev = toWanInput(quarterRevTarget / months.length);
    const avgGp = toWanInput(quarterGpTarget / months.length);

    if (existingMonths && existingMonths.length > 0) {
      existingMonths.forEach((m) => {
        init.rev[m.month] = toWanInput(m.target_amount);
        init.gp[m.month] = toWanInput(m.gross_profit_target);
      });
    } else {
      months.forEach((m) => {
        init.rev[m] = avgRev;
        init.gp[m] = avgGp;
      });
    }
    return init;
  });

  const resetValues = useCallback(() => {
    const init: MonthValues = { rev: {}, gp: {} };
    const avgRev = toWanInput(quarterRevTarget / months.length);
    const avgGp = toWanInput(quarterGpTarget / months.length);

    if (existingMonths && existingMonths.length > 0) {
      existingMonths.forEach((m) => {
        init.rev[m.month] = toWanInput(m.target_amount);
        init.gp[m.month] = toWanInput(m.gross_profit_target);
      });
    } else {
      months.forEach((m) => {
        init.rev[m] = avgRev;
        init.gp[m] = avgGp;
      });
    }
    setValues(init);
  }, [existingMonths, months, quarterRevTarget, quarterGpTarget]);

  const updateField = useCallback(
    (type: 'rev' | 'gp', month: number, v: number | null) => {
      setValues((prev) => ({
        ...prev,
        [type]: { ...prev[type], [month]: v ?? undefined },
      }));
    },
    [],
  );

  const allocated = useMemo(() => {
    let revSum = 0;
    let gpSum = 0;
    months.forEach((m) => {
      revSum += fromWanInput(values.rev[m]);
      gpSum += fromWanInput(values.gp[m]);
    });
    return { rev: revSum, gp: gpSum };
  }, [values, months]);

  const remaining = useMemo(
    () => ({
      rev: quarterRevTarget - allocated.rev,
      gp: quarterGpTarget - allocated.gp,
    }),
    [allocated, quarterRevTarget, quarterGpTarget],
  );

  const isOverBudget =
    remaining.rev < -0.01 || remaining.gp < -0.01;

  const isValid = months.every(
    (m) =>
      (values.rev[m] ?? 0) >= 0 &&
      (values.gp[m] ?? 0) >= 0 &&
      (values.rev[m] ?? 0) > 0 &&
      (values.gp[m] ?? 0) > 0,
  );

  const handleSubmit = async () => {
    if (!isValid) return;

    const mRev: Record<number, number> = {};
    const mGp: Record<number, number> = {};
    months.forEach((m) => {
      mRev[m] = fromWanInput(values.rev[m]);
      mGp[m] = fromWanInput(values.gp[m]);
    });

    await decomposeMutation.mutateAsync({
      targetId: yearTargetId,
      data: {
        quarters: { [quarter]: quarterRevTarget },
        quarters_gp: { [quarter]: quarterGpTarget },
        months_by_quarter: { [quarter]: mRev },
        months_gp_by_quarter: { [quarter]: mGp },
      },
    });

    resetValues();
    onSplitSuccess?.();
    onClose();
  };

  const handleClose = () => {
    resetValues();
    onClose();
  };

  return (
    <SidebarDrawer
      title={`拆分季度目标 - Q${quarter}`}
      open={open}
      onClose={handleClose}
      width={640}
      footer={
        <Space style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button onClick={handleClose}>取消</Button>
          <Button
            type="primary"
            loading={decomposeMutation.isPending}
            disabled={isOverBudget || !isValid}
            onClick={handleSubmit}
          >
            {isOverBudget ? '超出目标不可提交' : '提交拆分'}
          </Button>
        </Space>
      }
    >
      <Card
        size="small"
        style={{
          background: '#e6f0ff',
          borderColor: '#91c5ff',
          marginBottom: 16,
        }}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Text type="secondary">年度</Text>
            <br />
            <Text strong style={{ fontSize: 18 }}>{targetYear}年</Text>
          </Col>
          <Col span={12}>
            <Text type="secondary">当前季度</Text>
            <br />
            <Tag color="blue">Q{quarter}</Tag>
          </Col>
        </Row>
        <Divider style={{ margin: '8px 0' }} />
        <Row gutter={16}>
          <Col span={12}>
            <Text type="secondary">营收目标</Text>
            <br />
            <Text strong style={{ fontFamily: 'var(--font-mono)', fontSize: 16 }}>
              {fmtWan(quarterRevTarget)} 万元
            </Text>
          </Col>
          <Col span={12}>
            <Text type="secondary">毛利目标</Text>
            <br />
            <Text strong style={{ fontFamily: 'var(--font-mono)', fontSize: 16 }}>
              {fmtWan(quarterGpTarget)} 万元
            </Text>
          </Col>
        </Row>
      </Card>

      <Title level={5} style={{ marginBottom: 12 }}>
        {months[0]}-{months[months.length - 1]}月 月度拆分
      </Title>

      {months.map((m) => (
        <Card
          key={m}
          size="small"
          title={`${m}月`}
          style={{ marginBottom: 8 }}
          headStyle={{ padding: '0 12px', minHeight: 32 }}
          bodyStyle={{ padding: '8px 12px' }}
        >
          <Row gutter={12}>
            <Col span={12}>
              <Text type="secondary" style={{ fontSize: 12 }}>
                营收（万元）
              </Text>
              <InputNumber
                value={values.rev[m]}
                onChange={(v) => updateField('rev', m, v)}
                min={0}
                precision={1}
                style={{ width: '100%', marginTop: 4 }}
              />
            </Col>
            <Col span={12}>
              <Text type="secondary" style={{ fontSize: 12 }}>
                毛利（万元）
              </Text>
              <InputNumber
                value={values.gp[m]}
                onChange={(v) => updateField('gp', m, v)}
                min={0}
                precision={1}
                style={{ width: '100%', marginTop: 4 }}
              />
            </Col>
          </Row>
        </Card>
      ))}

      <Divider />

      <Card size="small" style={{ marginBottom: 8 }}>
        <Row gutter={16} style={{ marginBottom: 8 }}>
          <Col span={12}>
            <Text type="secondary">已分配营收</Text>
            <br />
            <Text strong style={{ fontFamily: 'var(--font-mono)' }}>
              {fmtWan(allocated.rev)} 万元
            </Text>
          </Col>
          <Col span={12}>
            <Text type="secondary">已分配毛利</Text>
            <br />
            <Text strong style={{ fontFamily: 'var(--font-mono)' }}>
              {fmtWan(allocated.gp)} 万元
            </Text>
          </Col>
        </Row>
        <Divider style={{ margin: '8px 0' }} />
        <Row gutter={16}>
          <Col span={12}>
            <Space>
              {isOverBudget ? (
                <WarningOutlined style={{ color: 'var(--error-color)' }} />
              ) : (
                <CheckCircleOutlined style={{ color: 'var(--success-color)' }} />
              )}
              <Text strong>剩余可分配</Text>
            </Space>
          </Col>
        </Row>
        <Row gutter={16} style={{ marginTop: 4 }}>
          <Col span={12}>
            <Text
              style={{
                fontFamily: 'var(--font-mono)',
                fontWeight: 600,
                color: isOverBudget
                  ? 'var(--error-color)'
                  : remaining.rev <= 0
                    ? 'var(--warning-color)'
                    : 'var(--success-color)',
              }}
            >
              营收: {fmtWan(remaining.rev)} 万
            </Text>
          </Col>
          <Col span={12}>
            <Text
              style={{
                fontFamily: 'var(--font-mono)',
                fontWeight: 600,
                color: isOverBudget
                  ? 'var(--error-color)'
                  : remaining.gp <= 0
                    ? 'var(--warning-color)'
                    : 'var(--success-color)',
              }}
            >
              毛利: {fmtWan(remaining.gp)} 万
            </Text>
          </Col>
        </Row>
      </Card>

      {isOverBudget && (
        <Text type="danger" style={{ display: 'block', marginTop: 8 }}>
          <WarningOutlined /> 月度合计已超过季度目标，请调整
        </Text>
      )}
    </SidebarDrawer>
  );
};

export default QuarterSplitDrawer;
