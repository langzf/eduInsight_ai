import React from 'react';
import { Drawer, Form, Input, Button, message } from 'antd';
import { modelApi } from '../../../api';

interface ModelDrawerProps {
  visible: boolean;
  model: any;
  onClose: () => void;
}

const ModelDrawer: React.FC<ModelDrawerProps> = ({
  visible,
  model,
  onClose
}) => {
  const [form] = Form.useForm();

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      await modelApi.update(model.id, values);
      message.success('更新成功');
      onClose();
    } catch (error) {
      message.error('更新失败');
    }
  };

  return (
    <Drawer
      title="模型详情"
      width={600}
      visible={visible}
      onClose={onClose}
      extra={
        <Button type="primary" onClick={handleSubmit}>
          保存
        </Button>
      }
    >
      {model && (
        <Form
          form={form}
          layout="vertical"
          initialValues={model}
        >
          <Form.Item
            label="学习率"
            name="learningRate"
            rules={[{ required: true }]}
          >
            <Input type="number" />
          </Form.Item>
          <Form.Item
            label="训练轮数"
            name="epochs"
            rules={[{ required: true }]}
          >
            <Input type="number" />
          </Form.Item>
          <Form.Item
            label="批次大小"
            name="batchSize"
            rules={[{ required: true }]}
          >
            <Input type="number" />
          </Form.Item>
        </Form>
      )}
    </Drawer>
  );
};

export default ModelDrawer; 