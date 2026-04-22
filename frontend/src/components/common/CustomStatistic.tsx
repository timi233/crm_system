import React from 'react';
import { Card, Typography } from 'antd';
import { DollarOutlined, TeamOutlined, UserOutlined, BellOutlined } from '@ant-design/icons';
import './CustomStatistic.css';

interface CustomStatisticProps {
  title: string;
  value: number;
  formatter?: (value: number) => string;
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
  precision?: number;
  color?: string;
  onClick?: () => void;
}

const CustomStatistic: React.FC<CustomStatisticProps> = ({ 
  title, 
  value, 
  formatter = (v) => v.toLocaleString(),
  prefix,
  suffix,
  precision = 0,
  color = '#1e293b',
  onClick
}) => {
  const formattedValue = formatter(value);
  
  return (
    <div 
      className="custom-statistic"
      onClick={onClick}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      <Typography.Text type="secondary" className="statistic-title">
        {title}
      </Typography.Text>
      <Typography.Title 
        level={4} 
        className="statistic-value"
        style={{ 
          color,
          margin: '8px 0',
          fontFamily: 'var(--font-mono)'
        }}
      >
        {prefix && <span className="statistic-prefix">{prefix}</span>}
        <span className="statistic-number">
          {formattedValue}
        </span>
        {suffix && <span className="statistic-suffix">{suffix}</span>}
      </Typography.Title>
    </div>
  );
};

export default CustomStatistic;