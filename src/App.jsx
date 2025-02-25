import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './components/Layout';
import Dashboard from './pages/Dashboard';
import ModelManage from './pages/ModelManage';
import ResourceManage from './pages/ResourceManage';
import DataManage from './pages/DataManage';
import SystemMonitor from './pages/SystemMonitor';

const App = () => {
  return (
    <BrowserRouter>
      <MainLayout>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/models" element={<ModelManage />} />
          <Route path="/resources" element={<ResourceManage />} />
          <Route path="/data" element={<DataManage />} />
          <Route path="/monitor" element={<SystemMonitor />} />
        </Routes>
      </MainLayout>
    </BrowserRouter>
  );
};

export default App; 