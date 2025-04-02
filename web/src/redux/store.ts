import { configureStore } from '@reduxjs/toolkit';
import modelReducer from './slices/modelSlice';
import resourceReducer from './slices/resourceSlice';
import dataReducer from './slices/dataSlice';
import monitorReducer from './slices/monitorSlice';

export const store = configureStore({
  reducer: {
    model: modelReducer,
    resource: resourceReducer,
    data: dataReducer,
    monitor: monitorReducer
  }
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch; 