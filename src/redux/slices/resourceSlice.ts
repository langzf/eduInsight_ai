import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { resourceApi } from '../../api';

export interface ResourceState {
  list: any[];
  loading: boolean;
  error: string | null;
}

const initialState: ResourceState = {
  list: [],
  loading: false,
  error: null
};

export const fetchResources = createAsyncThunk(
  'resource/fetchResources',
  async (params?: any) => {
    const response = await resourceApi.getList(params);
    return response;
  }
);

export const resourceSlice = createSlice({
  name: 'resource',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchResources.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchResources.fulfilled, (state, action) => {
        state.loading = false;
        state.list = action.payload;
      })
      .addCase(fetchResources.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '加载失败';
      });
  }
});

export default resourceSlice.reducer; 