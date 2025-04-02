import React from 'react';
import { Spin } from 'antd';

interface LoadingContainerProps {
  loading: boolean;
  error?: string | null;
  children: React.ReactNode;
}

const LoadingContainer: React.FC<LoadingContainerProps> = ({
  loading,
  error,
  children
}) => {
  if (error) {
    return (
      <div className="error-container">
        <div className="error-message">{error}</div>
      </div>
    );
  }

  return (
    <Spin spinning={loading}>
      {children}
    </Spin>
  );
};

export default LoadingContainer; 