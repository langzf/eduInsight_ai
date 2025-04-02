import React, { useState } from 'react';
import { Form, Input, Button, Card, message } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const Register = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (values) => {
    try {
      setLoading(true);
      // 这里替换成实际的注册API路径
      const registerUrl = `${process.env.REACT_APP_API_URL}/auth/register`;
      console.log('Register URL:', registerUrl);
      
      // 模拟注册成功，实际项目中应该调用后端API
      // const response = await axios.post(registerUrl, values);
      
      // 模拟注册
      message.success('注册成功，请登录');
      navigate('/login');
    } catch (error) {
      console.error('注册失败:', error);
      message.error('注册失败，请稍后再试');
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
        title="账号注册" 
        style={{ width: 400, boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}
        headStyle={{ fontSize: '22px', textAlign: 'center' }}
      >
        <Form
          name="register"
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
            name="email"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' }
            ]}
          >
            <Input 
              prefix={<MailOutlined />} 
              placeholder="邮箱" 
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码长度不能少于6个字符' }
            ]}
          >
            <Input.Password 
              prefix={<LockOutlined />} 
              placeholder="密码" 
            />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            dependencies={['password']}
            rules={[
              { required: true, message: '请确认密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'));
                },
              }),
            ]}
          >
            <Input.Password 
              prefix={<LockOutlined />} 
              placeholder="确认密码" 
            />
          </Form.Item>

          <Form.Item>
            <Button 
              type="primary" 
              htmlType="submit" 
              block 
              loading={loading}
            >
              注册
            </Button>
          </Form.Item>
          
          <div style={{ textAlign: 'center' }}>
            <a href="/login">已有账号？前往登录</a>
          </div>
        </Form>
      </Card>
    </div>
  );
};

export default Register; 