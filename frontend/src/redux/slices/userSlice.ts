import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { User } from "@/types/auth.types";

interface UserState {
  profile: User | null;
}

const initialState: UserState = { profile: null };

const userSlice = createSlice({
  name: "user",
  initialState,
  reducers: {
    setProfile(state, action: PayloadAction<User>) {
      state.profile = action.payload;
    },
  },
});

export const { setProfile } = userSlice.actions;
export default userSlice.reducer;
