import React, { useState, useEffect } from 'react';
import { Form, Input, Select, Button, message, Card } from 'antd';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import './StudentForm.css';

const { Option } = Select;
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:6060/api/v1';

const StudentForm = () => {
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const { id } = useParams();
  const [loading, setLoading] = useState(false);
  const isEdit = !!id;

  // 获取学生信息
  useEffect(() => {
    if (isEdit) {
      const fetchStudent = async () => {
        try {
          const response = await axios.get(`${API_URL}/students/${id}`, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          });
          form.setFieldsValue({
            ...response.data,
            parent_name: response.data.parent?.name,
            parent_phone: response.data.parent?.phone,
            parent_address: response.data.parent?.address,
          });
        } catch (error) {
          message.error('获取学生信息失败');
          navigate('/students');
        }
      };
      fetchStudent();
    }
  }, [id, form, navigate, isEdit]);

  // 提交表单
  const onFinish = async (values) => {
    setLoading(true);
    try {
      const studentData = {
        ...values,
        parent: {
          name: values.parent_name,
          phone: values.parent_phone,
          address: values.parent_address,
        },
      };
      delete studentData.parent_name;
      delete studentData.parent_phone;
      delete studentData.parent_address;

      if (isEdit) {
        await axios.put(`${API_URL}/students/${id}`, studentData, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        message.success('更新成功');
      } else {
        await axios.post(`${API_URL}/students`, studentData, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        message.success('添加成功');
      }
      navigate('/students');
    } catch (error) {
      message.error(isEdit ? '更新失败' : '添加失败');
    }
    setLoading(false);
  };

  return (
    <div className="student-form-container">
      <Card title={isEdit ? '编辑学生信息' : '新增学生'}>
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          initialValues={{
            gender: 'M',
          }}
        >
          <div className="form-section">
            <h3>基本信息</h3>
            <div className="form-row">
              <Form.Item
                name="student_id"
                label="学号"
                rules={[{ required: true, message: '请输入学号' }]}
              >
                <Input placeholder="请输入学号" />
              </Form.Item>
              <Form.Item
                name="name"
                label="姓名"
                rules={[{ required: true, message: '请输入姓名' }]}
              >
                <Input placeholder="请输入姓名" />
              </Form.Item>
            </div>

            <div className="form-row">
              <Form.Item
                name="gender"
                label="性别"
                rules={[{ required: true, message: '请选择性别' }]}
              >
                <Select>
                  <Option value="M">男</Option>
                  <Option value="F">女</Option>
                </Select>
              </Form.Item>
              <Form.Item
                name="phone"
                label="联系电话"
                rules={[{ required: true, message: '请输入联系电话' }]}
              >
                <Input placeholder="请输入联系电话" />
              </Form.Item>
            </div>

            <div className="form-row">
              <Form.Item
                name="grade"
                label="年级"
                rules={[{ required: true, message: '请输入年级' }]}
              >
                <Input placeholder="请输入年级" />
              </Form.Item>
              <Form.Item
                name="class"
                label="班级"
                rules={[{ required: true, message: '请输入班级' }]}
              >
                <Input placeholder="请输入班级" />
              </Form.Item>
            </div>
          </div>

          <div className="form-section">
            <h3>家长信息</h3>
            <div className="form-row">
              <Form.Item
                name="parent_name"
                label="家长姓名"
                rules={[{ required: true, message: '请输入家长姓名' }]}
              >
                <Input placeholder="请输入家长姓名" />
              </Form.Item>
              <Form.Item
                name="parent_phone"
                label="家长电话"
                rules={[{ required: true, message: '请输入家长电话' }]}
              >
                <Input placeholder="请输入家长电话" />
              </Form.Item>
            </div>

            <Form.Item
              name="parent_address"
              label="家庭住址"
              rules={[{ required: true, message: '请输入家庭住址' }]}
            >
              <Input.TextArea
                placeholder="请输入家庭住址"
                rows={3}
              />
            </Form.Item>
          </div>

          <div className="form-actions">
            <Button onClick={() => navigate('/students')}>取消</Button>
            <Button type="primary" htmlType="submit" loading={loading}>
              {isEdit ? '更新' : '添加'}
            </Button>
          </div>
        </Form>
      </Card>
    </div>
  );
};

export default StudentForm; 