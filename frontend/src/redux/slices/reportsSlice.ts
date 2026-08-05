import { createAsyncThunk, createSlice, PayloadAction } from "@reduxjs/toolkit";
import { reportsApi } from "@/api/reportsApi";
import { Report } from "@/types/report.types";

interface ReportsState {
  items: Report[];
  status: "idle" | "loading" | "failed";
}

const initialState: ReportsState = { items: [], status: "idle" };

export const fetchReports = createAsyncThunk("reports/fetch", async () => {
  return reportsApi.getReports();
});

export const deleteReport = createAsyncThunk("reports/delete", async (id: string) => {
  return reportsApi.deleteReport(id);
});

const reportsSlice = createSlice({
  name: "reports",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchReports.pending, (state) => {
        state.status = "loading";
      })
      .addCase(fetchReports.fulfilled, (state, action: PayloadAction<Report[]>) => {
        state.status = "idle";
        state.items = action.payload;
      })
      .addCase(deleteReport.fulfilled, (state, action) => {
        state.items = state.items.filter((r) => r.id !== action.payload.id);
      });
  },
});

export default reportsSlice.reducer;
