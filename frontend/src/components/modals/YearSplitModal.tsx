import React, { useCallback, useMemo, useState } from 'react';
import {
  Button,
  InputNumber,
  Space,
  Typography,
  Divider,
  Row,
  Col,
  Tag,
} from 'antd';
import { CheckCircleOutlined, WarningOutlined, CalculatorOutlined } from '@ant-design/icons';
import PageModal from '../common/PageModal';
import { useDecomposeTarget } from '../../hooks/useSalesTargets';

const { Text, Title } = Typography;

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

interface QuarterValues {
  rev: Record<number, number | undefined>;
  gp: Record<number, number | undefined>;
}

export interface YearSplitModalProps {
  open: boolean;
  onClose: () => void;
  yearTargetId: number;
  targetYear: number;
  yearRevTarget: number;
  yearGpTarget: number;
  existingQuarters?: {
    quarter: number;
    target_amount: number;
    gross_profit_target: number;
  }[];
  onSplitSuccess?: () => void;
}

const YearSplitModal: React.FC<YearSplitModalProps> = ({
  open,
  onClose,
  yearTargetId,
  targetYear,
  yearRevTarget,
  yearGpTarget,
  existingQuarters,
  onSplitSuccess,
}) => {
  const decomposeMutation = useDecomposeTarget();

  const quarters = [1, 2, 3, 4];

  const [values, setValues] = useState<QuarterValues>(() => {
    const init: QuarterValues = { rev: {}, gp: {} };
    const avgRev = toWanInput(yearRevTarget / 4);
    const avgGp = toWanInput(yearGpTarget / 4);

    if (existingQuarters && existingQuarters.length > 0) {
      existingQuarters.forEach((q) => {
        init.rev[q.quarter] = toWanInput(q.target_amount);
        init.gp[q.quarter] = toWanInput(q.gross_profit_target);
      });
    } else {
      quarters.forEach((q) => {
        init.rev[q] = avgRev;
        init.gp[q] = avgGp;
      });
    }
    return init;
  });

  const resetValues = useCallback(() => {
    const init: QuarterValues = { rev: {}, gp: {} };
    const avgRev = toWanInput(yearRevTarget / 4);
    const avgGp = toWanInput(yearGpTarget / 4);

    if (existingQuarters && existingQuarters.length > 0) {
      existingQuarters.forEach((q) => {
        init.rev[q.quarter] = toWanInput(q.target_amount);
        init.gp[q.quarter] = toWanInput(q.gross_profit_target);
      });
    } else {
      quarters.forEach((q) => {
        init.rev[q] = avgRev;
        init.gp[q] = avgGp;
      });
    }
    setValues(init);
  }, [existingQuarters, yearRevTarget, yearGpTarget]);

  const updateField = useCallback(
    (type: 'rev' | 'gp', quarter: number, v: number | null) => {
      setValues((prev) => ({
        ...prev,
        [type]: { ...prev[type], [quarter]: v ?? undefined },
      }));
    },
    [],
  );

  const allocated = useMemo(() => {
    let revSum = 0;
    let gpSum = 0;
    quarters.forEach((q) => {
      revSum += fromWanInput(values.rev[q]);
      gpSum += fromWanInput(values.gp[q]);
    });
    return { rev: revSum, gp: gpSum };
  }, [values]);

  const remaining = useMemo(
    () => ({
      rev: yearRevTarget - allocated.rev,
      gp: yearGpTarget - allocated.gp,
    }),
    [allocated, yearRevTarget, yearGpTarget],
  );

  const isOverBudget =
    remaining.rev < -0.01 || remaining.gp < -0.01;

  const isValid = quarters.every(
    (q) =>
      (values.rev[q] ?? 0) >= 0 &&
      (values.gp[q] ?? 0) >= 0 &&
      (values.rev[q] ?? 0) > 0 &&
      (values.gp[q] ?? 0) > 0,
  );

  const handleSubmit = async () => {
    if (!isValid) return;

    const qRev: Record<number, number> = {};
    const qGp: Record<number, number> = {};
    quarters.forEach((q) => {
      qRev[q] = fromWanInput(values.rev[q]);
      qGp[q] = fromWanInput(values.gp[q]);
    });

    try {
      await decomposeMutation.mutateAsync({
        targetId: yearTargetId,
        data: {
          quarters: qRev,
          quarters_gp: qGp,
          months_by_quarter: {}, // Let backend handle default month split or keep as is
          months_gp_by_quarter: {},
        },
      });

      resetValues();
      onSplitSuccess?.();
      onClose();
    } catch (e) {}
  };

  const handleClose = () => {
    resetValues();
    onClose();
  };

  const distributeEqually = () => {
    const avgRev = toWanInput(yearRevTarget / 4);
    const avgGp = toWanInput(yearGpTarget / 4);
    const newValues: QuarterValues = { rev: {}, gp: {} };
    quarters.forEach(q => {
      newValues.rev[q] = avgRev;
      newValues.gp[q] = avgGp;
    });
    setValues(newValues);
  };

  return (
    <PageModal
      title={`年度目标分配 · ${targetYear}年`}
      open={open}
      onClose={handleClose}
      width={720}
      footer={[
        <Button key="equal" icon={<CalculatorOutlined />} onClick={distributeEqually} style={{ float: 'left' }}>
          平均分配
        </Button>,
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
          {isOverBudget ? '分配总额超出' : '确认分配方案'}
        </Button>
      ]}
    >
      <div style={{
        background: 'linear-gradient(135deg, #eff6ff 0%, #e0e7ff 100%)',
        padding: '24px',
        borderRadius: '16px',
        border: '1px solid #dbeafe',
        marginBottom: 24,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <div style={{ fontSize: '14px', color: '#1e40af', marginBottom: '4px', fontWeight: 600 }}>年度总营收目标</div>
          <div style={{ fontSize: '24px', fontWeight: 900, color: '#1e3a8a' }}>{fmtWan(yearRevTarget)} 万元</div>
        </div>
        <Divider type="vertical" style={{ height: '40px', borderColor: '#bfdbfe' }} />
        <div>
          <div style={{ fontSize: '14px', color: '#1e40af', marginBottom: '4px', fontWeight: 600 }}>年度总毛利目标</div>
          <div style={{ fontSize: '24px', fontWeight: 900, color: '#1e3a8a' }}>{fmtWan(yearGpTarget)} 万元</div>
        </div>
      </div>

      <Title level={5} style={{ marginBottom: 16, fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
        <CalculatorOutlined /> 季度分配明细
      </Title>

      <Row gutter={[16, 16]}>
        {quarters.map((q) => (
          <Col key={q} span={12}>
            <div style={{
              background: 'white',
              padding: '20px',
              borderRadius: '12px',
              border: '1px solid #f1f5f9',
              boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <Tag color="blue" style={{ border: 'none', background: '#eff6ff', color: '#3b82f6', fontWeight: 800, padding: '2px 12px', borderRadius: '6px' }}>
                  第 {q} 季度 (Q{q})
                </Tag>
              </div>
              <Row gutter={12}>
                <Col span={12}>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>营收额 (万元)</div>
                  <InputNumber
                    value={values.rev[q]}
                    onChange={(v) => updateField('rev', q, v)}
                    min={0}
                    precision={1}
                    style={{ width: '100%' }}
                    placeholder="0.0"
                  />
                </Col>
                <Col span={12}>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>毛利额 (万元)</div>
                  <InputNumber
                    value={values.gp[q]}
                    onChange={(v) => updateField('gp', q, v)}
                    min={0}
                    precision={1}
                    style={{ width: '100%' }}
                    placeholder="0.0"
                  />
                </Col>
              </Row>
            </div>
          </Col>
        ))}
      </Row>

      <div style={{
        marginTop: 24,
        padding: '20px 24px',
        background: '#f8fafc',
        borderRadius: '16px',
        border: '1px solid #f1f5f9'
      }}>
        <Row gutter={32}>
          <Col span={12}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <Text type="secondary">已分配营收总计</Text>
              <Text strong>{fmtWan(allocated.rev)} 万</Text>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Text type="secondary">营收剩余额度</Text>
              <Text style={{
                fontWeight: 800,
                fontSize: '16px',
                color: remaining.rev < -0.01 ? '#ef4444' : remaining.rev < 0.01 ? '#10b981' : '#f59e0b'
              }}>
                {remaining.rev < -0.01 ? '超出 ' : ''}{fmtWan(Math.abs(remaining.rev))} 万
              </Text>
            </div>
          </Col>
          <Col span={12} style={{ borderLeft: '1px solid #e2e8f0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <Text type="secondary">已分配毛利总计</Text>
              <Text strong>{fmtWan(allocated.gp)} 万</Text>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Text type="secondary">毛利剩余额度</Text>
              <Text style={{
                fontWeight: 800,
                fontSize: '16px',
                color: remaining.gp < -0.01 ? '#ef4444' : remaining.gp < 0.01 ? '#10b981' : '#f59e0b'
              }}>
                {remaining.gp < -0.01 ? '超出 ' : ''}{fmtWan(Math.abs(remaining.gp))} 万
              </Text>
            </div>
          </Col>
        </Row>
      </div>

      {isOverBudget && (
        <div style={{ marginTop: 16, textAlign: 'center' }}>
          <Tag color="error" icon={<WarningOutlined />} style={{ padding: '4px 16px', borderRadius: '20px' }}>
            分配总额不能超过年度目标，请核对数值
          </Tag>
        </div>
      )}
    </PageModal>
  );
};

export default YearSplitModal;
