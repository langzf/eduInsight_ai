import React from 'react';
import { Tag } from 'antd';

interface StatusConfig {
  [key: string]: {
    color: string;
    text: string;
  };
}

interface StatusTagProps {
  status: string;
  config: StatusConfig;
}

const StatusTag: React.FC<StatusTagProps> = ({ status, config }) => {
  const { color, text } = config[status] || { color: 'default', text: '未知' };
  
  return (
    <Tag color={color}>{text}</Tag>
  );
};

export default StatusTag; 