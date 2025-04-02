import React, { useState, useEffect } from 'react';
import { Table, Button, Space, Modal, message } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './StudentList.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:6060/api/v1';

const StudentList = () => {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // 获取学生列表
  const fetchStudents = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/students`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      setStudents(response.data);
    } catch (error) {
      message.error('获取学生列表失败');
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchStudents();
  }, []);

  // 删除学生
  const handleDelete = (id) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个学生吗？此操作不可恢复。',
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        try {
          await axios.delete(`${API_URL}/students/${id}`, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          });
          message.success('删除成功');
          fetchStudents();
        } catch (error) {
          message.error('删除失败');
        }
      }
    });
  };

  // 表格列定义
  const columns = [
    {
      title: '学号',
      dataIndex: 'student_id',
      key: 'student_id',
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
      title: '年级',
      dataIndex: 'grade',
      key: 'grade',
    },
    {
      title: '班级',
      dataIndex: 'class',
      key: 'class',
    },
    {
      title: '联系电话',
      dataIndex: 'phone',
      key: 'phone',
    },
    {
      title: '家长姓名',
      dataIndex: ['parent', 'name'],
      key: 'parentName',
    },
    {
      title: '家长电话',
      dataIndex: ['parent', 'phone'],
      key: 'parentPhone',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          <Button 
            type="primary" 
            icon={<EditOutlined />}
            onClick={() => navigate(`/students/edit/${record.id}`)}
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
    <div className="student-list-container">
      <div className="student-list-header">
        <h1>学生管理</h1>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => navigate('/students/add')}
        >
          新增学生
        </Button>
      </div>
      <Table
        columns={columns}
        dataSource={students}
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

export default StudentList; 