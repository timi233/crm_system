import React from 'react';
import { Card, CardProps } from 'antd';
import './BrandCard.css';

export type BrandCardVariant = 'primary' | 'secondary' | 'tertiary';

export interface BrandCardProps extends CardProps {
  variant?: BrandCardVariant;
}

const BrandCard: React.FC<BrandCardProps> = ({ 
  variant = 'tertiary', 
  className = '', 
  ...props 
}) => {
  const variantClass = `card--${variant}`;
  const combinedClassName = `${variantClass} ${className}`.trim();
  
  return (
    <Card 
      {...props} 
      className={combinedClassName}
      bordered={false}
    />
  );
};

export default BrandCard;