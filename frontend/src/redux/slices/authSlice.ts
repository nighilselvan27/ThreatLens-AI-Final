import { createAsyncThunk, createSlice, PayloadAction } from "@reduxjs/toolkit";
import { authApi } from "@/api/authApi";
import { LoginCredentials, User } from "@/types/auth.types";

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  status: "idle" | "loading" | "failed";
  error: string | null;
}

const persistedToken = localStorage.getItem("threatlens_token");

function getPersistedUser(): User | null {
  const raw = localStorage.getItem("threatlens_user");
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

const initialState: AuthState = {
  user: getPersistedUser(),
  token: persistedToken,
  isAuthenticated: !!persistedToken,
  status: "idle",
  error: null,
};

export const loginUser = createAsyncThunk(
  "auth/login",
  async (credentials: LoginCredentials, { rejectWithValue }) => {
    try {
      return await authApi.login(credentials);
    } catch (err) {
      return rejectWithValue((err as Error).message);
    }
  }
);

export const logoutUser = createAsyncThunk("auth/logout", async () => {
  await authApi.logout();
});

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    clearAuthError(state) {
      state.error = null;
    },
    updateProfile(state, action: PayloadAction<{ name: string; email: string }>) {
      if (state.user) {
        state.user = { ...state.user, ...action.payload };
        localStorage.setItem("threatlens_user", JSON.stringify(state.user));
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(loginUser.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action: PayloadAction<{ user: User; token: string }>) => {
        state.status = "idle";
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.isAuthenticated = true;
        localStorage.setItem("threatlens_token", action.payload.token);
        localStorage.setItem("threatlens_user", JSON.stringify(action.payload.user));
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.status = "failed";
        state.error = (action.payload as string) || "Login failed";
      })
      .addCase(logoutUser.fulfilled, (state) => {
        state.user = null;
        state.token = null;
        state.isAuthenticated = false;
        localStorage.removeItem("threatlens_token");
        localStorage.removeItem("threatlens_user");
      });
  },
});

export const { clearAuthError, updateProfile } = authSlice.actions;
export default authSlice.reducer;