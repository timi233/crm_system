export const STAGE_COLORS = {
  '初步接触': 'blue',
  '意向沟通': 'gold',
  '需求挖掘中': 'green',
  '需求方案': 'blue',
  '需求确认': 'cyan',
  '报价投标': 'gold',
  '合同签订': 'purple',
  '已成交': 'green',
  '已流失': 'red',
  high: 'red',
  medium: 'orange',
  low: 'blue',
  '高': 'red',
  '中': 'orange',
  '低': 'blue',
};

export const STATUS_COLORS = {
  active: 'green',
  inactive: 'default',
  pending: 'gold',
  draft: 'default',
  signed: 'green',
  fulfilled: 'blue',
  assigned: 'blue',
  in_progress: 'gold',
  cancelled: 'red',
};

export const ALERT_TYPES = {
  follow_up: { color: 'gold', label: '待跟进' },
  opportunity_stagnant: { color: 'orange', label: '商机停滞' },
  target_miss: { color: 'red', label: '目标未达成' },
  contract_overdue: { color: 'red', label: '合同逾期' },
  customer_risk: { color: 'red', label: '客户风险' },
};
