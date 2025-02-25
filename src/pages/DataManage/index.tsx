import React, { useEffect } from 'react';
import { Table, Upload, Button, message, Card, Space } from 'antd';
import { UploadOutlined, DownloadOutlined } from '@ant-design/icons';
import { useDispatch, useSelector } from 'react-redux';
import { fetchImports, importData } from '../../redux/slices/dataSlice';
import { dataApi } from '../../api';
import type { AppDispatch, RootState } from '../../redux/store';

const DataManage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { imports, loading } = useSelector((state: RootState) => state.data);

  useEffect(() => {
    dispatch(fetchImports());
  }, [dispatch]);

  const handleDownloadTemplate = async () => {
    try {
      const response = await dataApi.downloadTemplate();
      // 创建下载链接
      const url = window.URL.createObjectURL(new Blob([response]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'template.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      message.error('下载模板失败');
    }
  };

  const columns = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
    },
    {
      title: '导入时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusMap = {
          success: { text: '成功', color: '#52c41a' },
          failed: { text: '失败', color: '#ff4d4f' },
          processing: { text: '处理中', color: '#1890ff' }
        };
        const { text, color } = statusMap[status] || { text: '未知', color: '#000' };
        return <span style={{ color }}>{text}</span>;
      }
    },
    {
      title: '结果',
      dataIndex: 'result',
      key: 'result',
      render: (result: any) => (
        <span>
          成功: {result?.success || 0} / 
          失败: {result?.failed || 0}
        </span>
      )
    }
  ];

  return (
    <div className="data-manage">
      <Card title="数据导入" className="import-card">
        <Space direction="vertical" style={{ width: '100%' }}>
          <Space>
            <Upload
              accept=".csv,.xlsx"
              showUploadList={false}
              beforeUpload={async (file) => {
                const formData = new FormData();
                formData.append('file', file);
                try {
                  await dispatch(importData(formData)).unwrap();
                  message.success('导入成功');
                  dispatch(fetchImports());
                } catch (error) {
                  message.error('导入失败');
                }
                return false;
              }}
            >
              <Button icon={<UploadOutlined />}>选择文件</Button>
            </Upload>
            <Button 
              icon={<DownloadOutlined />}
              onClick={handleDownloadTemplate}
            >
              下载模板
            </Button>
          </Space>
          <div className="import-tip">
            支持.csv或.xlsx格式,请先下载模板填写数据
          </div>
        </Space>
      </Card>

      <Card title="导入历史" className="history-card">
        <Table
          columns={columns}
          dataSource={imports}
          loading={loading}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showTotal: (total) => `共 ${total} 条记录`
          }}
        />
      </Card>
    </div>
  );
};

export default DataManage; 