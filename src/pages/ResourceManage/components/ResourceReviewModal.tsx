import React from 'react';
import { Modal, Button, Space, Typography } from 'antd';

const { Text } = Typography;

interface ResourceReviewModalProps {
  visible: boolean;
  resource: any;
  onClose: () => void;
  onReview: (id: string, status: 'approved' | 'rejected') => void;
}

const ResourceReviewModal: React.FC<ResourceReviewModalProps> = ({
  visible,
  resource,
  onClose,
  onReview
}) => {
  return (
    <Modal
      title="资源审核"
      visible={visible}
      onCancel={onClose}
      footer={null}
      width={800}
    >
      {resource && (
        <div>
          <div className="resource-info">
            <Text strong>资源名称：</Text>
            <Text>{resource.name}</Text>
          </div>
          <div className="resource-preview">
            {resource.type === 'video' ? (
              <video
                src={resource.url}
                controls
                style={{ width: '100%', maxHeight: 400 }}
              />
            ) : (
              <iframe
                src={resource.url}
                style={{ width: '100%', height: 400, border: 'none' }}
              />
            )}
          </div>
          <div className="review-actions" style={{ marginTop: 24 }}>
            <Space>
              <Button
                type="primary"
                onClick={() => onReview(resource.id, 'approved')}
              >
                通过
              </Button>
              <Button
                danger
                onClick={() => onReview(resource.id, 'rejected')}
              >
                拒绝
              </Button>
            </Space>
          </div>
        </div>
      )}
    </Modal>
  );
};

export default ResourceReviewModal; 