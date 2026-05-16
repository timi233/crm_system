/**
 * Currency utility for formatting and scaling values between Yuan and Wan Yuan.
 */

export const toWan = (value: number | null | undefined): number | undefined => {
  if (value === null || value === undefined) return undefined;
  return Number((Number(value) / 10000).toFixed(1));
};

export const toWanNumber = (value: number | null | undefined): number => {
  return toWan(value) ?? 0;
};

export const fromWan = (value: number | null | undefined): number | undefined => {
  if (value === null || value === undefined) return undefined;
  return Math.round(Number(value) * 10000);
};

export const formatWan = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return '-';
  return (Number(value) / 10000).toLocaleString('zh-CN', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
};
