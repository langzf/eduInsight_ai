import React, { useState } from 'react';
import { Form, Input, Button, Card, Row, Col, message, Spin, Checkbox } from 'antd';
import { UserOutlined, LockOutlined, MobileOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import apiConfig from '../config/api';
import './Login.css'; // 引入自定义样式

// 使用集中配置的API地址
const API_URL = apiConfig.apiBaseURL;

const Login = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const [form] = Form.useForm();
  
  const onFinish = async (values) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/auth/login`, {
        phone: values.phone,
        password: values.password,
      });
      
      const { access_token, user } = response.data;
      
      // 保存用户信息和token到localStorage
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      
      message.success('登录成功');
      navigate('/dashboard');
    } catch (error) {
      let errorMsg = '登录失败';
      if (error.response) {
        errorMsg = error.response.data.error || errorMsg;
      }
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="login-page">
      <div className="login-container">
        <Card 
          className="login-card"
          title={
            <div className="login-title">
              <h1>教育洞察AI系统</h1>
              <p>用户登录</p>
            </div>
          }
          bordered={false}
        >
          <Spin spinning={loading}>
            <Form
              form={form}
              name="login"
              onFinish={onFinish}
              layout="vertical"
              size="large"
              requiredMark={false}
              className="login-form"
            >
              <Form.Item
                name="phone"
                rules={[
                  { required: true, message: '请输入手机号' },
                  { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号格式' }
                ]}
              >
                <Input 
                  prefix={<MobileOutlined className="input-icon" />} 
                  placeholder="手机号" 
                  maxLength={11}
                />
              </Form.Item>
              
              <Form.Item
                name="password"
                rules={[{ required: true, message: '请输入密码' }]}
              >
                <Input.Password 
                  prefix={<LockOutlined className="input-icon" />} 
                  placeholder="密码" 
                />
              </Form.Item>
              
              <Form.Item>
                <Button 
                  type="primary" 
                  htmlType="submit" 
                  block
                  className="login-button"
                >
                  登录
                </Button>
              </Form.Item>
              
              <div className="login-links">
                <a href="/register">新用户注册</a>
                <a href="/forgot-password">忘记密码</a>
              </div>
            </Form>
          </Spin>
        </Card>
      </div>
    </div>
  );
};

export default Login; 