import React, { useState, useEffect } from 'react';
import { Form, Input, Select, Button, message, Card } from 'antd';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import './TeacherForm.css';

const { Option } = Select;
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:6060/api/v1';

const TeacherForm = () => {
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const { id } = useParams();
  const [loading, setLoading] = useState(false);
  const isEdit = !!id;

  // 获取教师信息
  useEffect(() => {
    if (isEdit) {
      const fetchTeacher = async () => {
        try {
          const response = await axios.get(`${API_URL}/teachers/${id}`, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          });
          form.setFieldsValue(response.data);
        } catch (error) {
          message.error('获取教师信息失败');
          navigate('/teachers');
        }
      };
      fetchTeacher();
    }
  }, [id, form, navigate, isEdit]);

  // 提交表单
  const onFinish = async (values) => {
    setLoading(true);
    try {
      if (isEdit) {
        await axios.put(`${API_URL}/teachers/${id}`, values, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        message.success('更新成功');
      } else {
        await axios.post(`${API_URL}/teachers`, values, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        message.success('添加成功');
      }
      navigate('/teachers');
    } catch (error) {
      message.error(isEdit ? '更新失败' : '添加失败');
    }
    setLoading(false);
  };

  return (
    <div className="teacher-form-container">
      <Card title={isEdit ? '编辑教师信息' : '新增教师'}>
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
                name="teacher_id"
                label="工号"
                rules={[{ required: true, message: '请输入工号' }]}
              >
                <Input placeholder="请输入工号" />
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
                name="title"
                label="职称"
                rules={[{ required: true, message: '请输入职称' }]}
              >
                <Select>
                  <Option value="教授">教授</Option>
                  <Option value="副教授">副教授</Option>
                  <Option value="讲师">讲师</Option>
                  <Option value="助教">助教</Option>
                </Select>
              </Form.Item>
            </div>

            <div className="form-row">
              <Form.Item
                name="department"
                label="所属部门"
                rules={[{ required: true, message: '请输入所属部门' }]}
              >
                <Input placeholder="请输入所属部门" />
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
                name="email"
                label="邮箱"
                rules={[
                  { required: true, message: '请输入邮箱' },
                  { type: 'email', message: '请输入有效的邮箱地址' }
                ]}
              >
                <Input placeholder="请输入邮箱" />
              </Form.Item>
              <Form.Item
                name="office"
                label="办公室"
                rules={[{ required: true, message: '请输入办公室' }]}
              >
                <Input placeholder="请输入办公室" />
              </Form.Item>
            </div>

            <Form.Item
              name="research_area"
              label="研究方向"
              rules={[{ required: true, message: '请输入研究方向' }]}
            >
              <Input.TextArea
                placeholder="请输入研究方向"
                rows={3}
              />
            </Form.Item>
          </div>

          <div className="form-actions">
            <Button onClick={() => navigate('/teachers')}>取消</Button>
            <Button type="primary" htmlType="submit" loading={loading}>
              {isEdit ? '更新' : '添加'}
            </Button>
          </div>
        </Form>
      </Card>
    </div>
  );
};

export default TeacherForm; 