import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { analyticsApi } from "@/api/analyticsApi";
import { DashboardStats } from "@/types/dashboard.types";

interface DashboardState {
  stats: DashboardStats | null;
  recentActivity: { id: string; actor: string; action: string; time: string }[];
  recentScans: { id: string; fileName: string; riskLevel: string; time: string }[];
  status: "idle" | "loading" | "failed";
}

const initialState: DashboardState = {
  stats: null,
  recentActivity: [],
  recentScans: [],
  status: "idle",
};

export const fetchDashboardData = createAsyncThunk("dashboard/fetch", async () => {
  return analyticsApi.getDashboardBundle();
});

const dashboardSlice = createSlice({
  name: "dashboard",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchDashboardData.pending, (state) => {
        state.status = "loading";
      })
      .addCase(fetchDashboardData.fulfilled, (state, action) => {
        state.status = "idle";
        state.stats = action.payload.stats;
        state.recentActivity = action.payload.recentActivity;
        state.recentScans = action.payload.recentScans as any;
      })
      .addCase(fetchDashboardData.rejected, (state) => {
        state.status = "failed";
      });
  },
});

export default dashboardSlice.reducer;
