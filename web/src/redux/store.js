import { configureStore } from '@reduxjs/toolkit';

// 导入reducer
import monitorReducer from './slices/monitorSlice';

// 配置store
export const store = configureStore({
  reducer: {
    monitor: monitorReducer,
    // 其他reducer可以在这里添加
  },
}); 