import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { alertsApi } from "@/api/alertsApi";
import { Alert } from "@/types/alert.types";

interface AlertsState {
  items: Alert[];
  status: "idle" | "loading" | "failed";
}

const initialState: AlertsState = { items: [], status: "idle" };

export const fetchAlerts = createAsyncThunk("alerts/fetch", async () => {
  return alertsApi.getAlerts();
});

export const markAlertAsRead = createAsyncThunk("alerts/markRead", async (id: string) => {
  return alertsApi.markAsRead(id);
});

export const deleteAlert = createAsyncThunk("alerts/delete", async (id: string) => {
  return alertsApi.deleteAlert(id);
});

const alertsSlice = createSlice({
  name: "alerts",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchAlerts.fulfilled, (state, action: import("@reduxjs/toolkit").PayloadAction<Alert[]>) => {
        state.items = action.payload;
      })
      .addCase(markAlertAsRead.fulfilled, (state, action) => {
        const alert = state.items.find((a) => a.id === action.payload.id);
        if (alert) alert.isRead = true;
      })
      .addCase(deleteAlert.fulfilled, (state, action) => {
        state.items = state.items.filter((a) => a.id !== action.payload.id);
      });
  },
});

export default alertsSlice.reducer;
