import { describe, it, expect } from 'vitest';
import { ROLE_LABELS, getRoleLabel, AppRole } from './roles';

describe('ROLE_LABELS', () => {
  it('contains all expected roles including channel_ops', () => {
    const expectedRoles: AppRole[] = ['admin', 'sales', 'business', 'finance', 'technician', 'channel_ops'];
    expectedRoles.forEach((role) => {
      expect(ROLE_LABELS[role]).toBeDefined();
    });
  });

  it('maps channel_ops to 渠道运营', () => {
    expect(ROLE_LABELS.channel_ops).toBe('渠道运营');
  });

  it('maps admin to 管理员', () => {
    expect(ROLE_LABELS.admin).toBe('管理员');
  });

  it('maps sales to 销售', () => {
    expect(ROLE_LABELS.sales).toBe('销售');
  });

  it('maps technician to 技术员', () => {
    expect(ROLE_LABELS.technician).toBe('技术员');
  });
});

describe('getRoleLabel', () => {
  it('returns 未设置角色 for undefined', () => {
    expect(getRoleLabel(undefined)).toBe('未设置角色');
  });

  it('returns 未设置角色 for null', () => {
    expect(getRoleLabel(null)).toBe('未设置角色');
  });

  it('returns label for valid role', () => {
    expect(getRoleLabel('admin')).toBe('管理员');
    expect(getRoleLabel('channel_ops')).toBe('渠道运营');
  });

  it('returns original role string for unknown role', () => {
    expect(getRoleLabel('unknown_role')).toBe('unknown_role');
  });
});