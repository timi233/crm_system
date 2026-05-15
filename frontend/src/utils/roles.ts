export type AppRole =
  | 'admin'
  | 'sales'
  | 'business'
  | 'finance'
  | 'technician'
  | 'channel_ops';

export const ROLE_LABELS: Record<AppRole, string> = {
  admin: '管理员',
  sales: '销售',
  business: '商务',
  finance: '财务',
  technician: '技术员',
  channel_ops: '渠道运营',
};

export const getRoleLabel = (role?: string | null) => {
  if (!role) {
    return '未设置角色';
  }

  return ROLE_LABELS[role as AppRole] || role;
};
