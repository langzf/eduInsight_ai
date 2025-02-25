import React from 'react';
import { Button, Popconfirm } from 'antd';
import type { ButtonProps } from 'antd/lib/button';

interface ConfirmButtonProps extends ButtonProps {
  title: string;
  onConfirm: () => void;
  confirmText?: string;
  cancelText?: string;
}

const ConfirmButton: React.FC<ConfirmButtonProps> = ({
  title,
  onConfirm,
  confirmText = '确定',
  cancelText = '取消',
  children,
  ...buttonProps
}) => {
  return (
    <Popconfirm
      title={title}
      onConfirm={onConfirm}
      okText={confirmText}
      cancelText={cancelText}
    >
      <Button {...buttonProps}>
        {children}
      </Button>
    </Popconfirm>
  );
};

export default ConfirmButton; 