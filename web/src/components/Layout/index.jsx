import React from 'react';
import { Layout, Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  ExperimentOutlined,
  FileOutlined,
  DatabaseOutlined,
  MonitorOutlined,
  LogoutOutlined,
  TeamOutlined,
  UserOutlined
} from '@ant-design/icons';

const { Header, Sider, Content } = Layout;

const MainLayout = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表盘'
    },
    {
      key: '/students',
      icon: <TeamOutlined />,
      label: '学生管理'
    },
    {
      key: '/teachers',
      icon: <UserOutlined />,
      label: '教师管理'
    },
    {
      key: '/models',
      icon: <ExperimentOutlined />,
      label: '模型管理'
    },
    {
      key: '/resources', 
      icon: <FileOutlined />,
      label: '资源管理'
    },
    {
      key: '/data',
      icon: <DatabaseOutlined />,
      label: '数据管理'
    },
    {
      key: '/monitor',
      icon: <MonitorOutlined />,
      label: '系统监控'
    }
  ];

  const handleMenuClick = ({ key }) => {
    navigate(key);
  };

  const handleLogout = () => {
    // 清除本地存储的token
    localStorage.removeItem('token');
    // 跳转到登录页
    navigate('/login');
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header className="header">
        <div className="logo">EduInsight AI</div>
        <div className="user-info">
          <span>管理员</span>
          <LogoutOutlined onClick={handleLogout} style={{ marginLeft: 16, cursor: 'pointer' }} />
        </div>
      </Header>
      <Layout>
        <Sider width={200}>
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            onClick={handleMenuClick}
            style={{ height: '100%', borderRight: 0 }}
          />
        </Sider>
        <Layout style={{ padding: '24px' }}>
          <Content className="site-layout-content">
            {children}
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
};

export default MainLayout; 