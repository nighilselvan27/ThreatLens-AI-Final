import { configureStore } from "@reduxjs/toolkit";
import authReducer from "./slices/authSlice";
import uiReducer from "./slices/uiSlice";
import dashboardReducer from "./slices/dashboardSlice";
import uploadReducer from "./slices/uploadSlice";
import reportsReducer from "./slices/reportsSlice";
import alertsReducer from "./slices/alertsSlice";
import analyticsReducer from "./slices/analyticsSlice";
import userReducer from "./slices/userSlice";

export const store = configureStore({
  reducer: {
    auth: authReducer,
    ui: uiReducer,
    dashboard: dashboardReducer,
    upload: uploadReducer,
    reports: reportsReducer,
    alerts: alertsReducer,
    analytics: analyticsReducer,
    user: userReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
