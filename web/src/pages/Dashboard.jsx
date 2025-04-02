import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Button, Typography, message, Layout } from 'antd';
import { useNavigate } from 'react-router-dom';
import { 
  UserOutlined, 
  BookOutlined, 
  ScheduleOutlined, 
  LogoutOutlined 
} from '@ant-design/icons';

const { Title, Paragraph } = Typography;
const { Header, Content, Footer } = Layout;

const Dashboard = () => {
  const [user, setUser] = useState(null);
  const navigate = useNavigate();
  
  useEffect(() => {
    // 从localStorage获取用户信息
    const userData = localStorage.getItem('user');
    if (userData) {
      setUser(JSON.parse(userData));
    }
  }, []);
  
  const handleLogout = () => {
    // 清除本地存储的token和用户信息
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    message.success('退出登录成功');
    navigate('/login');
  };
  
  if (!user) {
    return <div>加载中...</div>;
  }
  
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#fff', padding: '0 20px', boxShadow: '0 1px 4px rgba(0,21,41,.08)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', height: '100%' }}>
          <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
            教育洞察AI系统
          </div>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <span style={{ marginRight: '12px' }}>
              <UserOutlined style={{ marginRight: '5px' }} />
              {user.username || user.phone}
            </span>
            <Button type="link" icon={<LogoutOutlined />} onClick={handleLogout}>
              退出登录
            </Button>
          </div>
        </div>
      </Header>
      
      <Content style={{ padding: '24px', background: '#f0f2f5' }}>
        <Title level={2} style={{ marginBottom: '24px' }}>控制面板</Title>
        
        <Paragraph style={{ marginBottom: '24px' }}>
          欢迎回来，{user.full_name || user.username || user.phone}！
        </Paragraph>
        
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={8}>
            <Card>
              <Statistic
                title="我的课程"
                value={0}
                prefix={<BookOutlined />}
                suffix="门"
              />
              <div style={{ marginTop: '12px' }}>
                <Button type="primary">进入课程</Button>
              </div>
            </Card>
          </Col>
          
          <Col xs={24} sm={8}>
            <Card>
              <Statistic
                title="学习进度"
                value={0}
                prefix={<ScheduleOutlined />}
                suffix="%"
              />
              <div style={{ marginTop: '12px' }}>
                <Button>继续学习</Button>
              </div>
            </Card>
          </Col>
          
          <Col xs={24} sm={8}>
            <Card>
              <Statistic
                title="消息通知"
                value={0}
                prefix={<UserOutlined />}
                suffix="条"
              />
              <div style={{ marginTop: '12px' }}>
                <Button>查看消息</Button>
              </div>
            </Card>
          </Col>
        </Row>
        
        <Card style={{ marginTop: '24px' }}>
          <Title level={4}>最近课程</Title>
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <p>暂无课程数据</p>
            <Button type="primary">浏览课程</Button>
          </div>
        </Card>
      </Content>
      
      <Footer style={{ textAlign: 'center' }}>
        教育洞察AI系统 ©2025 Created by EduInsight
      </Footer>
    </Layout>
  );
};

export default Dashboard; 