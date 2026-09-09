import { createAsyncThunk, createSlice, PayloadAction } from "@reduxjs/toolkit";
import { uploadApi } from "@/api/uploadApi";
import { UploadedFile } from "@/types/upload.types";

interface UploadState {
  history: UploadedFile[];
  activeUploads: UploadedFile[];
  status: "idle" | "loading" | "failed";
}

const initialState: UploadState = {
  history: [],
  activeUploads: [],
  status: "idle",
};

export const fetchUploadHistory = createAsyncThunk("upload/fetchHistory", async () => {
  return uploadApi.getHistory();
});

const uploadSlice = createSlice({
  name: "upload",
  initialState,
  reducers: {
    addActiveUpload(state, action: PayloadAction<UploadedFile>) {
      state.activeUploads.unshift(action.payload);
    },
    updateActiveUploadProgress(
      state,
      action: PayloadAction<{ id: string; progress: number; status?: UploadedFile["status"] }>
    ) {
      const file = state.activeUploads.find((f) => f.id === action.payload.id);
      if (file) {
        file.progress = action.payload.progress;
        if (action.payload.status) file.status = action.payload.status;
      }
    },
    completeUpload(state, action: PayloadAction<UploadedFile>) {
      state.activeUploads = state.activeUploads.filter((f) => f.id !== action.payload.id);
      state.history.unshift(action.payload);
    },
  },
  extraReducers: (builder) => {
    builder.addCase(fetchUploadHistory.fulfilled, (state, action) => {
      state.history = action.payload;
    });
  },
});

export const { addActiveUpload, updateActiveUploadProgress, completeUpload } = uploadSlice.actions;
export default uploadSlice.reducer;
