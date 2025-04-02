import React, { useState, useEffect } from 'react';
import { Table, Button, Space, Modal, message } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './TeacherList.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:6060/api/v1';

const TeacherList = () => {
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // 获取教师列表
  const fetchTeachers = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/teachers`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      setTeachers(response.data);
    } catch (error) {
      message.error('获取教师列表失败');
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchTeachers();
  }, []);

  // 删除教师
  const handleDelete = (id) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这位教师吗？此操作不可恢复。',
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        try {
          await axios.delete(`${API_URL}/teachers/${id}`, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          });
          message.success('删除成功');
          fetchTeachers();
        } catch (error) {
          message.error('删除失败');
        }
      }
    });
  };

  // 表格列定义
  const columns = [
    {
      title: '工号',
      dataIndex: 'teacher_id',
      key: 'teacher_id',
    },
    {
      title: '姓名',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '性别',
      dataIndex: 'gender',
      key: 'gender',
      render: (gender) => gender === 'M' ? '男' : '女',
    },
    {
      title: '职称',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: '所属部门',
      dataIndex: 'department',
      key: 'department',
    },
    {
      title: '联系电话',
      dataIndex: 'phone',
      key: 'phone',
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          <Button 
            type="primary" 
            icon={<EditOutlined />}
            onClick={() => navigate(`/teachers/edit/${record.id}`)}
          >
            编辑
          </Button>
          <Button 
            type="primary" 
            danger 
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div className="teacher-list-container">
      <div className="teacher-list-header">
        <h1>教师管理</h1>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => navigate('/teachers/add')}
        >
          新增教师
        </Button>
      </div>
      <Table
        columns={columns}
        dataSource={teachers}
        rowKey="id"
        loading={loading}
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条记录`,
        }}
      />
    </div>
  );
};

export default TeacherList; 