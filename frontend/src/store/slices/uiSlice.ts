import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface UIState {
  loading: boolean;
  sidebarCollapsed: boolean;
  notification: {
    message: string;
    type: 'success' | 'error' | 'warning' | 'info';
    visible: boolean;
  };
}

const initialState: UIState = {
  loading: false,
  sidebarCollapsed: false,
  notification: {
    message: '',
    type: 'info',
    visible: false,
  },
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    toggleSidebar: (state) => {
      state.sidebarCollapsed = !state.sidebarCollapsed;
    },
    showNotification: (
      state,
      action: PayloadAction<{ message: string; type: 'success' | 'error' | 'warning' | 'info' }>
    ) => {
      state.notification = {
        message: action.payload.message,
        type: action.payload.type,
        visible: true,
      };
    },
    hideNotification: (state) => {
      state.notification.visible = false;
    },
  },
});

export const { setLoading, toggleSidebar, showNotification, hideNotification } = uiSlice.actions;
export default uiSlice.reducer;