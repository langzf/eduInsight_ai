import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => Promise.reject(error)
);

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      // 未授权,跳转登录
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// 模型相关API
export const modelApi = {
  getList: (params) => api.get('/models', { params }),
  getDetail: (id) => api.get(`/models/${id}`),
  update: (id, data) => api.post(`/models/${id}/update`, data),
  train: (id) => api.post(`/models/${id}/train`),
  delete: (id) => api.delete(`/models/${id}`)
};

// 资源相关API
export const resourceApi = {
  getList: (params) => api.get('/resources', { params }),
  upload: (data) => api.post('/resources', data),
  review: (id, status) => api.post(`/resources/${id}/review`, { status }),
  delete: (id) => api.delete(`/resources/${id}`)
};

// 数据相关API
export const dataApi = {
  import: (data) => api.post('/data/import', data),
  getImports: (params) => api.get('/data/imports', { params }),
  downloadTemplate: () => api.get('/data/template', { responseType: 'blob' })
};

// 监控相关API
export const monitorApi = {
  getMetrics: (params) => api.get('/metrics', { params }),
  getModelPerformance: (params) => api.get('/metrics/models', { params }),
  getResourceUsage: (params) => api.get('/metrics/resources', { params })
}; 