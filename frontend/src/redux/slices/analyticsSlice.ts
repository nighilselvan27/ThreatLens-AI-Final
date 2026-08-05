import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { analyticsApi } from "@/api/analyticsApi";

interface AnalyticsState {
  data: Awaited<ReturnType<typeof analyticsApi.getAnalyticsBundle>> | null;
  status: "idle" | "loading" | "failed";
}

const initialState: AnalyticsState = { data: null, status: "idle" };

export const fetchAnalytics = createAsyncThunk("analytics/fetch", async () => {
  return analyticsApi.getAnalyticsBundle();
});

const analyticsSlice = createSlice({
  name: "analytics",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchAnalytics.pending, (state) => {
        state.status = "loading";
      })
      .addCase(fetchAnalytics.fulfilled, (state, action) => {
        state.status = "idle";
        state.data = action.payload;
      })
      .addCase(fetchAnalytics.rejected, (state) => {
        state.status = "failed";
      });
  },
});

export default analyticsSlice.reducer;
