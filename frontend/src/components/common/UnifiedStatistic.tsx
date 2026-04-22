import React from 'react';
import { Typography, Statistic } from 'antd';
import { DollarOutlined, TeamOutlined, UserOutlined, BellOutlined, PhoneOutlined, FundProjectionScreenOutlined } from '@ant-design/icons';

interface UnifiedStatisticProps {
  title: string;
  value: number | string;
  formatter?: (value: number | string) => string;
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
  precision?: number;
  size?: 'small' | 'default' | 'large';
  className?: string;
}

const UnifiedStatistic: React.FC<UnifiedStatisticProps> = ({ 
  title, 
  value, 
  formatter,
  prefix,
  suffix,
  precision = 0,
  size = 'default',
  className = ''
}) => {
  // 处理数字格式化
  const formatValue = (val: number | string): string => {
    if (typeof val === 'string') return val;
    if (formatter) return formatter(val);
    
    // 默认格式化大数字
    if (Math.abs(val) >= 1000000) {
      return (val / 1000000).toFixed(1) + 'M';
    }
    if (Math.abs(val) >= 1000) {
      return (val / 1000).toFixed(1) + 'K';
    }
    return val.toLocaleString();
  };

  // 根据大小设置字体大小
  const getTitleSize = () => {
    switch (size) {
      case 'small': return 12;
      case 'large': return 16;
      default: return 14;
    }
  };

  const getValueSize = () => {
    switch (size) {
      case 'small': return 16;
      case 'large': return 28;
      default: return 20;
    }
  };

  return (
    <div className={`unified-statistic ${className}`.trim()}>
      <Typography.Text 
        type="secondary" 
        style={{ 
          fontSize: getTitleSize(),
          fontFamily: 'var(--font-body)',
          lineHeight: 1.4
        }}
      >
        {title}
      </Typography.Text>
      <Statistic
        value={formatValue(value)}
        prefix={prefix}
        suffix={suffix}
        precision={precision}
        className="unified-statistic-value"
        style={{
          fontFamily: 'var(--font-mono)',
          fontWeight: 600,
          fontSize: getValueSize(),
          color: '#1e293b',
          margin: '4px 0'
        }}
      />
    </div>
  );
};

export default UnifiedStatistic;

// 导出常用的图标映射
export const StatisticIcons = {
  leads: <UserOutlined />,
  opportunities: <TeamOutlined />,
  projects: <FundProjectionScreenOutlined />,
  contracts: <DollarOutlined />,
  followups: <PhoneOutlined />,
  alerts: <BellOutlined />,
};