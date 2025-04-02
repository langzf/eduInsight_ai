import React, { useState } from 'react';
import { Form, Input, Button, Card, Row, Col, message, Spin, Checkbox } from 'antd';
import { UserOutlined, LockOutlined, MobileOutlined, MailOutlined, IdcardOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:6060/api/v1';

const Register = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const [form] = Form.useForm();
  
  const onFinish = async (values) => {
    setLoading(true);
    try {
      // 删除确认密码字段
      const { confirmPassword, agreement, ...userData } = values;
      
      // 发送注册请求
      const response = await axios.post(`${API_URL}/auth/register`, userData);
      
      message.success('注册成功，请登录');
      navigate('/login');
    } catch (error) {
      let errorMsg = '注册失败';
      if (error.response) {
        errorMsg = error.response.data.error || errorMsg;
      }
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div style={{ 
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)'
    }}>
      <Row justify="center" align="middle">
        <Col xs={22} sm={16} md={12} lg={8} xl={6}>
          <Card 
            title={
              <div style={{ textAlign: 'center', fontSize: '22px', fontWeight: 'bold' }}>
                <span>教育洞察AI系统</span>
                <div style={{ fontSize: '16px', fontWeight: 'normal', marginTop: '8px' }}>新用户注册</div>
              </div>
            } 
            bordered={false}
            style={{ boxShadow: '0 10px 25px rgba(0,0,0,0.1)', borderRadius: '8px' }}
          >
            <Spin spinning={loading}>
              <Form
                form={form}
                name="register"
                onFinish={onFinish}
                layout="vertical"
                requiredMark={false}
              >
                <Form.Item
                  name="phone"
                  rules={[
                    { required: true, message: '请输入手机号' },
                    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号格式' }
                  ]}
                >
                  <Input 
                    prefix={<MobileOutlined style={{ color: '#1890ff' }} />} 
                    placeholder="手机号" 
                    maxLength={11}
                  />
                </Form.Item>
                
                <Form.Item
                  name="username"
                  rules={[
                    { required: false, message: '请输入用户名' },
                    { min: 4, message: '用户名至少4个字符' }
                  ]}
                >
                  <Input 
                    prefix={<UserOutlined style={{ color: '#1890ff' }} />} 
                    placeholder="用户名（选填）" 
                  />
                </Form.Item>
                
                <Form.Item
                  name="email"
                  rules={[
                    { required: false, message: '请输入邮箱' },
                    { type: 'email', message: '请输入有效的邮箱地址' }
                  ]}
                >
                  <Input 
                    prefix={<MailOutlined style={{ color: '#1890ff' }} />} 
                    placeholder="邮箱（选填）" 
                  />
                </Form.Item>
                
                <Form.Item
                  name="full_name"
                  rules={[{ required: false, message: '请输入姓名' }]}
                >
                  <Input 
                    prefix={<IdcardOutlined style={{ color: '#1890ff' }} />} 
                    placeholder="真实姓名（选填）" 
                  />
                </Form.Item>
                
                <Form.Item
                  name="password"
                  rules={[
                    { required: true, message: '请输入密码' },
                    { min: 6, message: '密码至少6个字符' }
                  ]}
                >
                  <Input.Password 
                    prefix={<LockOutlined style={{ color: '#1890ff' }} />} 
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
                    prefix={<LockOutlined style={{ color: '#1890ff' }} />} 
                    placeholder="确认密码" 
                  />
                </Form.Item>
                
                <Form.Item
                  name="agreement"
                  valuePropName="checked"
                  rules={[
                    { 
                      validator: (_, value) => 
                        value ? Promise.resolve() : Promise.reject(new Error('请同意用户协议和隐私政策')) 
                    },
                  ]}
                >
                  <Checkbox>
                    我已阅读并同意 <a href="/terms">用户协议</a> 和 <a href="/privacy">隐私政策</a>
                  </Checkbox>
                </Form.Item>
                
                <Form.Item>
                  <Button 
                    type="primary" 
                    htmlType="submit" 
                    block 
                    style={{ height: '40px', borderRadius: '4px' }}
                  >
                    注册
                  </Button>
                </Form.Item>
                
                <div style={{ textAlign: 'center' }}>
                  已有账号？ <a href="/login">立即登录</a>
                </div>
              </Form>
            </Spin>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Register; 