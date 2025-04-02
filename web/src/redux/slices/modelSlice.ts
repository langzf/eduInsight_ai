import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { modelApi } from '../../api';

export interface ModelState {
  list: any[];
  loading: boolean;
  error: string | null;
  selectedModel: any | null;
}

const initialState: ModelState = {
  list: [],
  loading: false,
  error: null,
  selectedModel: null
};

export const fetchModels = createAsyncThunk(
  'model/fetchModels',
  async (params?: any) => {
    const response = await modelApi.getList(params);
    return response;
  }
);

export const modelSlice = createSlice({
  name: 'model',
  initialState,
  reducers: {
    setSelectedModel: (state, action) => {
      state.selectedModel = action.payload;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchModels.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchModels.fulfilled, (state, action) => {
        state.loading = false;
        state.list = action.payload;
      })
      .addCase(fetchModels.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '加载失败';
      });
  }
});

export const { setSelectedModel } = modelSlice.actions;
export default modelSlice.reducer; 