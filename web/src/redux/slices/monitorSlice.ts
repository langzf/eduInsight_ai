import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { monitorApi } from '../../api';

export interface MonitorState {
  metrics: {
    users: {
      active: number;
      total: number;
      trend: number[];
    };
    resources: {
      downloads: number;
      storage: number;
      top: any[];
    };
    models: {
      accuracy: number;
      training: number;
      deployed: number;
    };
    system: {
      cpu: number[];
      memory: number[];
      gpu: number[];
    };
  };
  loading: boolean;
  error: string | null;
}

const initialState: MonitorState = {
  metrics: {
    users: {
      active: 0,
      total: 0,
      trend: []
    },
    resources: {
      downloads: 0,
      storage: 0,
      top: []
    },
    models: {
      accuracy: 0,
      training: 0,
      deployed: 0
    },
    system: {
      cpu: [],
      memory: [],
      gpu: []
    }
  },
  loading: false,
  error: null
};

export const fetchMetrics = createAsyncThunk(
  'monitor/fetchMetrics',
  async (params?: any) => {
    const response = await monitorApi.getMetrics(params);
    return response;
  }
);

export const monitorSlice = createSlice({
  name: 'monitor',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchMetrics.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchMetrics.fulfilled, (state, action) => {
        state.loading = false;
        state.metrics = action.payload;
      })
      .addCase(fetchMetrics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '加载失败';
      });
  }
});

export default monitorSlice.reducer; 