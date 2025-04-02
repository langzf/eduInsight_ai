import React, { useEffect, useState } from 'react';
import { Table, Button, Space, message, Modal } from 'antd';
import { useDispatch, useSelector } from 'react-redux';
import { fetchModels } from '../../redux/slices/modelSlice';
import { modelApi } from '../../api';
import ModelDrawer from './components/ModelDrawer';
import type { AppDispatch, RootState } from '../../redux/store';

const ModelManage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { list, loading } = useSelector((state: RootState) => state.model);
  const [selectedModel, setSelectedModel] = useState<any>(null);
  const [drawerVisible, setDrawerVisible] = useState(false);

  useEffect(() => {
    dispatch(fetchModels());
  }, [dispatch]);

  const handleTrain = async (id: string) => {
    try {
      await modelApi.train(id);
      message.success('开始训练');
      dispatch(fetchModels());
    } catch (error) {
      message.error('训练失败');
    }
  };

  const handleDelete = async (id: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个模型吗？',
      onOk: async () => {
        try {
          await modelApi.delete(id);
          message.success('删除成功');
          dispatch(fetchModels());
        } catch (error) {
          message.error('删除失败');
        }
      }
    });
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
    },
    {
      title: '更新时间',
      dataIndex: 'updatedAt',
      key: 'updatedAt',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button 
            type="link" 
            onClick={() => {
              setSelectedModel(record);
              setDrawerVisible(true);
            }}
          >
            查看
          </Button>
          <Button 
            type="link"
            onClick={() => handleTrain(record.id)}
          >
            训练
          </Button>
          <Button 
            type="link" 
            danger
            onClick={() => handleDelete(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div className="model-manage">
      <Table 
        columns={columns}
        dataSource={list}
        loading={loading}
        rowKey="id"
      />
      <ModelDrawer
        visible={drawerVisible}
        model={selectedModel}
        onClose={() => {
          setDrawerVisible(false);
          setSelectedModel(null);
        }}
      />
    </div>
  );
};

export default ModelManage; 