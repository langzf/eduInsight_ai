import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import './App.css';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import NotFound from './pages/NotFound';
import MainLayout from './components/Layout';
import ModelManage from './pages/ModelManage';
import ResourceManage from './pages/ResourceManage';
import DataManage from './pages/DataManage';
import SystemMonitor from './pages/SystemMonitor';
import StudentList from './pages/student/StudentList';
import StudentForm from './pages/student/StudentForm';
import TeacherList from './pages/teacher/TeacherList';
import TeacherForm from './pages/teacher/TeacherForm';

// 检查用户是否已登录
const isAuthenticated = () => {
  return localStorage.getItem('token') !== null;
};

// 受保护的路由
const ProtectedRoute = ({ children }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

// 公开路由 - 已登录用户将被重定向到仪表板
const PublicRoute = ({ children }) => {
  if (isAuthenticated()) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
};

function App() {
  return (
    <Router>
      <Routes>
        {/* 公开路由 */}
        <Route 
          path="/login" 
          element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          } 
        />
        <Route 
          path="/register" 
          element={
            <PublicRoute>
              <Register />
            </PublicRoute>
          } 
        />
        
        {/* 受保护的路由 */}
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute>
              <MainLayout>
                <Dashboard />
              </MainLayout>
            </ProtectedRoute>
          } 
        />
        <Route path="/models" element={
          <ProtectedRoute>
            <MainLayout>
              <ModelManage />
            </MainLayout>
          </ProtectedRoute>
        } />
        <Route path="/resources" element={
          <ProtectedRoute>
            <MainLayout>
              <ResourceManage />
            </MainLayout>
          </ProtectedRoute>
        } />
        <Route path="/data" element={
          <ProtectedRoute>
            <MainLayout>
              <DataManage />
            </MainLayout>
          </ProtectedRoute>
        } />
        <Route path="/monitor" element={
          <ProtectedRoute>
            <MainLayout>
              <SystemMonitor />
            </MainLayout>
          </ProtectedRoute>
        } />

        {/* 学生管理路由 */}
        <Route path="/students" element={
          <ProtectedRoute>
            <MainLayout>
              <StudentList />
            </MainLayout>
          </ProtectedRoute>
        } />
        <Route path="/students/add" element={
          <ProtectedRoute>
            <MainLayout>
              <StudentForm />
            </MainLayout>
          </ProtectedRoute>
        } />
        <Route path="/students/edit/:id" element={
          <ProtectedRoute>
            <MainLayout>
              <StudentForm />
            </MainLayout>
          </ProtectedRoute>
        } />

        {/* 教师管理路由 */}
        <Route path="/teachers" element={
          <ProtectedRoute>
            <MainLayout>
              <TeacherList />
            </MainLayout>
          </ProtectedRoute>
        } />
        <Route path="/teachers/add" element={
          <ProtectedRoute>
            <MainLayout>
              <TeacherForm />
            </MainLayout>
          </ProtectedRoute>
        } />
        <Route path="/teachers/edit/:id" element={
          <ProtectedRoute>
            <MainLayout>
              <TeacherForm />
            </MainLayout>
          </ProtectedRoute>
        } />
        
        {/* 首页重定向 */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        
        {/* 404 页面 */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Router>
  );
}

export default App; 