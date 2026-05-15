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
import PageModal from '../common/PageModal';
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

export interface QuarterSplitModalProps {
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

const QuarterSplitModal: React.FC<QuarterSplitModalProps> = ({
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
    <PageModal
      title={`季度目标拆分 · ${targetYear}年 Q${quarter}`}
      open={open}
      onClose={handleClose}
      width={680}
      footer={[
        <Button key="cancel" onClick={handleClose}>
          取消
        </Button>,
        <Button
          key="submit"
          type="primary"
          className="btn--gradient"
          loading={decomposeMutation.isPending}
          disabled={isOverBudget || !isValid}
          onClick={handleSubmit}
        >
          {isOverBudget ? '超出目标不可提交' : '提交拆分方案'}
        </Button>
      ]}
    >
      <div style={{
        background: '#eff6ff',
        padding: '20px 24px',
        borderRadius: '12px',
        border: '1px solid #dbeafe',
        marginBottom: 24
      }}>
        <Row gutter={24}>
          <Col span={12}>
            <div style={{ fontSize: '13px', color: '#1e40af', marginBottom: '4px' }}>营收目标 (Q{quarter})</div>
            <div style={{ fontSize: '20px', fontWeight: 800, color: '#1e3a8a' }}>{fmtWan(quarterRevTarget)} 万元</div>
          </Col>
          <Col span={12}>
            <div style={{ fontSize: '13px', color: '#1e40af', marginBottom: '4px' }}>毛利目标 (Q{quarter})</div>
            <div style={{ fontSize: '20px', fontWeight: 800, color: '#1e3a8a' }}>{fmtWan(quarterGpTarget)} 万元</div>
          </Col>
        </Row>
      </div>

      <Title level={5} style={{ marginBottom: 16, fontWeight: 700 }}>
        月度拆分明细 ({months[0]}-{months[months.length - 1]}月)
      </Title>

      <Row gutter={[16, 16]}>
        {months.map((m) => (
          <Col key={m} span={24}>
            <div style={{
              background: 'white',
              padding: '16px 20px',
              borderRadius: '12px',
              border: '1px solid #f1f5f9',
              display: 'flex',
              alignItems: 'center',
              gap: '20px'
            }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '10px',
                background: '#f8fafc',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 800,
                fontSize: '18px',
                color: '#64748b',
                border: '1px solid #e2e8f0'
              }}>
                {m}
              </div>
              <div style={{ flex: 1 }}>
                <Row gutter={16}>
                  <Col span={12}>
                    <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>营收额 (万元)</div>
                    <InputNumber
                      value={values.rev[m]}
                      onChange={(v) => updateField('rev', m, v)}
                      min={0}
                      precision={1}
                      style={{ width: '100%' }}
                    />
                  </Col>
                  <Col span={12}>
                    <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>毛利额 (万元)</div>
                    <InputNumber
                      value={values.gp[m]}
                      onChange={(v) => updateField('gp', m, v)}
                      min={0}
                      precision={1}
                      style={{ width: '100%' }}
                    />
                  </Col>
                </Row>
              </div>
            </div>
          </Col>
        ))}
      </Row>

      <div style={{
        marginTop: 24,
        padding: '16px 20px',
        background: '#f8fafc',
        borderRadius: '12px',
        border: '1px solid #f1f5f9'
      }}>
        <Row gutter={16}>
          <Col span={12}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <Text type="secondary">已分配营收</Text>
              <Text strong>{fmtWan(allocated.rev)} 万</Text>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Text type="secondary">剩余额度</Text>
              <Text style={{
                fontWeight: 700,
                color: remaining.rev < 0 ? '#ef4444' : remaining.rev === 0 ? '#10b981' : '#f59e0b'
              }}>
                {fmtWan(remaining.rev)} 万
              </Text>
            </div>
          </Col>
          <Col span={12} style={{ borderLeft: '1px solid #e2e8f0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <Text type="secondary">已分配毛利</Text>
              <Text strong>{fmtWan(allocated.gp)} 万</Text>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Text type="secondary">剩余额度</Text>
              <Text style={{
                fontWeight: 700,
                color: remaining.gp < 0 ? '#ef4444' : remaining.gp === 0 ? '#10b981' : '#f59e0b'
              }}>
                {fmtWan(remaining.gp)} 万
              </Text>
            </div>
          </Col>
        </Row>
      </div>

      {isOverBudget && (
        <div style={{ marginTop: 12, textAlign: 'center' }}>
          <Text type="danger" style={{ fontWeight: 600 }}>
            <WarningOutlined /> 分配总额已超出季度目标，请核对后提交
          </Text>
        </div>
      )}
    </PageModal>
  );
};

export default QuarterSplitModal;
