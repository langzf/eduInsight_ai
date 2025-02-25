import React, { useEffect } from 'react';
import { Row, Col, Card } from 'antd';
import { useDispatch, useSelector } from 'react-redux';
import { Line, Bar } from '@ant-design/charts';
import { fetchMetrics } from '../../redux/slices/monitorSlice';
import type { AppDispatch, RootState } from '../../redux/store';
import MetricCard from '../../components/MetricCard';
import {
  UserOutlined,
  DownloadOutlined,
  ExperimentOutlined,
  CloudServerOutlined
} from '@ant-design/icons';

const SystemMonitor: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { metrics, loading } = useSelector((state: RootState) => state.monitor);

  useEffect(() => {
    // 每30秒刷新一次数据
    const fetchData = () => {
      dispatch(fetchMetrics());
    };
    fetchData();
    const timer = setInterval(fetchData, 30000);
    return () => clearInterval(timer);
  }, [dispatch]);

  // 用户活跃度趋势配置
  const userTrendConfig = {
    data: metrics.users.trend.map((value, index) => ({
      time: index,
      value
    })),
    xField: 'time',
    yField: 'value',
    smooth: true,
    areaStyle: {
      fill: 'l(270) 0:#ffffff 1:#1890ff',
    }
  };

  // 资源使用TOP10配置
  const resourceTopConfig = {
    data: metrics.resources.top,
    xField: 'downloads',
    yField: 'name',
    seriesField: 'type',
    legend: {
      position: 'top-right'
    }
  };

  // 系统资源使用趋势配置
  const systemMetricsConfig = {
    data: metrics.system.cpu.map((value, index) => ({
      time: index,
      cpu: value,
      memory: metrics.system.memory[index],
      gpu: metrics.system.gpu[index]
    })),
    xField: 'time',
    yField: ['cpu', 'memory', 'gpu'],
    seriesField: 'type',
    legend: {
      position: 'top'
    }
  };

  return (
    <div className="system-monitor">
      {/* 关键指标卡片 */}
      <Row gutter={16}>
        <Col span={6}>
          <MetricCard
            title="活跃用户"
            value={metrics.users.active}
            prefix={<UserOutlined />}
            suffix="人"
          />
        </Col>
        <Col span={6}>
          <MetricCard
            title="资源下载"
            value={metrics.resources.downloads}
            prefix={<DownloadOutlined />}
            suffix="次"
          />
        </Col>
        <Col span={6}>
          <MetricCard
            title="模型准确率"
            value={metrics.models.accuracy}
            prefix={<ExperimentOutlined />}
            suffix="%"
          />
        </Col>
        <Col span={6}>
          <MetricCard
            title="存储使用"
            value={metrics.resources.storage}
            prefix={<CloudServerOutlined />}
            suffix="GB"
          />
        </Col>
      </Row>

      {/* 趋势图表 */}
      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={16}>
          <Card title="用户活跃度趋势" loading={loading}>
            <Line {...userTrendConfig} />
          </Card>
        </Col>
        <Col span={8}>
          <Card title="资源使用TOP10" loading={loading}>
            <Bar {...resourceTopConfig} />
          </Card>
        </Col>
      </Row>

      {/* 系统资源监控 */}
      <Card title="系统资源使用趋势" style={{ marginTop: 24 }} loading={loading}>
        <Line {...systemMetricsConfig} />
      </Card>
    </div>
  );
};

export default SystemMonitor; 