import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  systemStatus: {
    cpu: 0,
    memory: 0,
    disk: 0,
    network: 0
  },
  loading: false,
  error: null
};

const monitorSlice = createSlice({
  name: 'monitor',
  initialState,
  reducers: {
    setSystemStatus: (state, action) => {
      state.systemStatus = action.payload;
    },
    setLoading: (state, action) => {
      state.loading = action.payload;
    },
    setError: (state, action) => {
      state.error = action.payload;
    }
  }
});

export const { setSystemStatus, setLoading, setError } = monitorSlice.actions;
export default monitorSlice.reducer; 