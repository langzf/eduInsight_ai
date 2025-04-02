import React, { useState, useEffect } from 'react';
import { Table, Upload, Button, Space, Tag, message, Tabs } from 'antd';
import { UploadOutlined, InboxOutlined } from '@ant-design/icons';
import { useDispatch, useSelector } from 'react-redux';
import { fetchResources } from '../../redux/slices/resourceSlice';
import { resourceApi } from '../../api';
import type { AppDispatch, RootState } from '../../redux/store';
import ResourceReviewModal from './components/ResourceReviewModal';

const { Dragger } = Upload;
const { TabPane } = Tabs;

const ResourceManage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { list, loading } = useSelector((state: RootState) => state.resource);
  const [selectedResource, setSelectedResource] = useState<any>(null);
  const [reviewModalVisible, setReviewModalVisible] = useState(false);

  useEffect(() => {
    dispatch(fetchResources());
  }, [dispatch]);

  const handleUpload = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    try {
      await resourceApi.upload(formData);
      message.success('上传成功');
      dispatch(fetchResources());
    } catch (error) {
      message.error('上传失败');
    }
  };

  const handleReview = async (id: string, status: 'approved' | 'rejected') => {
    try {
      await resourceApi.review(id, status);
      message.success('审核完成');
      dispatch(fetchResources());
      setReviewModalVisible(false);
    } catch (error) {
      message.error('审核失败');
    }
  };

  const columns = [
    {
      title: '资源名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag color={type === 'video' ? 'blue' : 'green'}>
          {type === 'video' ? '视频' : '文档'}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'pending' ? 'orange' : 'green'}>
          {status === 'pending' ? '待审核' : '已审核'}
        </Tag>
      ),
    },
    {
      title: '上传时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button 
            type="link"
            onClick={() => {
              setSelectedResource(record);
              setReviewModalVisible(true);
            }}
          >
            审核
          </Button>
          <Button 
            type="link" 
            href={record.url} 
            target="_blank"
          >
            预览
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div className="resource-manage">
      <Tabs defaultActiveKey="list">
        <TabPane tab="资源列表" key="list">
          <Table 
            columns={columns}
            dataSource={list}
            loading={loading}
            rowKey="id"
          />
        </TabPane>
        <TabPane tab="上传资源" key="upload">
          <Dragger
            name="file"
            multiple={true}
            action="/api/resources/upload"
            onChange={info => {
              if (info.file.status === 'done') {
                message.success(`${info.file.name} 上传成功`);
              } else if (info.file.status === 'error') {
                message.error(`${info.file.name} 上传失败`);
              }
            }}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p className="ant-upload-hint">
              支持单个或批量上传，严禁上传违规内容
            </p>
          </Dragger>
        </TabPane>
      </Tabs>

      <ResourceReviewModal
        visible={reviewModalVisible}
        resource={selectedResource}
        onClose={() => {
          setReviewModalVisible(false);
          setSelectedResource(null);
        }}
        onReview={handleReview}
      />
    </div>
  );
};

export default ResourceManage; 