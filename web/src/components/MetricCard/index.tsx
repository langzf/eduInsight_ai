import React from 'react';
import { Card, Statistic } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';

interface MetricCardProps {
  title: string;
  value: number;
  precision?: number;
  prefix?: React.ReactNode;
  suffix?: string;
  trend?: number;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  precision = 2,
  prefix,
  suffix,
  trend
}) => {
  return (
    <Card>
      <Statistic
        title={title}
        value={value}
        precision={precision}
        prefix={prefix}
        suffix={suffix}
      />
      {trend && (
        <div className="trend">
          {trend > 0 ? (
            <ArrowUpOutlined style={{ color: '#52c41a' }} />
          ) : (
            <ArrowDownOutlined style={{ color: '#ff4d4f' }} />
          )}
          <span>{Math.abs(trend)}%</span>
        </div>
      )}
    </Card>
  );
};

export default MetricCard; 