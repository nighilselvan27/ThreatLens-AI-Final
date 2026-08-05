import { createSlice, PayloadAction, nanoid } from "@reduxjs/toolkit";

export interface ToastItem {
  id: string;
  title: string;
  description?: string;
  variant: "success" | "error" | "info" | "warning";
}

interface UiState {
  darkMode: boolean;
  sidebarCollapsed: boolean;
  toasts: ToastItem[];
}

const initialState: UiState = {
  darkMode: true,
  sidebarCollapsed: false,
  toasts: [],
};

const uiSlice = createSlice({
  name: "ui",
  initialState,
  reducers: {
    toggleDarkMode(state) {
      state.darkMode = !state.darkMode;
    },
    toggleSidebar(state) {
      state.sidebarCollapsed = !state.sidebarCollapsed;
    },
    addToast: {
      reducer(state, action: PayloadAction<ToastItem>) {
        state.toasts.push(action.payload);
      },
      prepare(toast: Omit<ToastItem, "id">) {
        return { payload: { ...toast, id: nanoid() } };
      },
    },
    removeToast(state, action: PayloadAction<string>) {
      state.toasts = state.toasts.filter((t) => t.id !== action.payload);
    },
  },
});

export const { toggleDarkMode, toggleSidebar, addToast, removeToast } = uiSlice.actions;
export default uiSlice.reducer;
