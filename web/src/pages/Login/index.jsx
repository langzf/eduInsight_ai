import React, { useState } from 'react';
import { Form, Input, Button, Card, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const Login = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (values) => {
    try {
      setLoading(true);
      // 这里替换成实际的登录API路径
      const loginUrl = `${process.env.REACT_APP_API_URL}/auth/login`;
      console.log('Login URL:', loginUrl);
      
      // 模拟登录成功，实际项目中应该调用后端API
      // 由于后端API可能尚未实现，这里模拟登录逻辑
      // const response = await axios.post(loginUrl, values);
      // localStorage.setItem('token', response.data.token);
      
      // 模拟登录
      localStorage.setItem('token', 'test-token-123456');
      message.success('登录成功');
      navigate('/dashboard');
    } catch (error) {
      console.error('登录失败:', error);
      message.error('用户名或密码错误');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      width: '100%', 
      height: '100vh', 
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      background: '#f0f2f5' 
    }}>
      <Card 
        title="教育洞察AI系统" 
        style={{ width: 400, boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}
        headStyle={{ fontSize: '22px', textAlign: 'center' }}
      >
        <Form
          name="login"
          initialValues={{ remember: true }}
          onFinish={handleSubmit}
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input 
              prefix={<UserOutlined />} 
              placeholder="用户名" 
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password 
              prefix={<LockOutlined />} 
              placeholder="密码" 
            />
          </Form.Item>

          <Form.Item>
            <Button 
              type="primary" 
              htmlType="submit" 
              block 
              loading={loading}
            >
              登录
            </Button>
          </Form.Item>
          
          <div style={{ textAlign: 'center' }}>
            <a href="/register">注册账号</a>
          </div>
        </Form>
      </Card>
    </div>
  );
};

export default Login; 