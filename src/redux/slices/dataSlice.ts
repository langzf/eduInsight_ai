import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { dataApi } from '../../api';

export interface DataState {
  imports: any[];
  loading: boolean;
  error: string | null;
}

const initialState: DataState = {
  imports: [],
  loading: false,
  error: null
};

export const fetchImports = createAsyncThunk(
  'data/fetchImports',
  async (params?: any) => {
    const response = await dataApi.getImports(params);
    return response;
  }
);

export const importData = createAsyncThunk(
  'data/importData',
  async (data: FormData) => {
    const response = await dataApi.import(data);
    return response;
  }
);

export const dataSlice = createSlice({
  name: 'data',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchImports.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchImports.fulfilled, (state, action) => {
        state.loading = false;
        state.imports = action.payload;
      })
      .addCase(fetchImports.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '加载失败';
      })
      .addCase(importData.pending, (state) => {
        state.loading = true;
      })
      .addCase(importData.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(importData.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '导入失败';
      });
  }
});

export default dataSlice.reducer; 