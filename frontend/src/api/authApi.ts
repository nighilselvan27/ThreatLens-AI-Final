import { AuthResponse, LoginCredentials } from "@/types/auth.types";
import { mockUser } from "@/data/userData";

/**
 * Backend contract (wire this up to your real endpoint):
 *   POST /api/v1/auth/login  -> { user, token }
 * Mocked here so the frontend is fully demoable without a backend.
 */
export const authApi = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    await new Promise((r) => setTimeout(r, 900));
    if (!credentials.email || credentials.password.length < 8) {
      throw new Error("Invalid email or password");
    }
    return {
      user: { ...mockUser, email: credentials.email },
      token: "mock-jwt-token." + btoa(credentials.email) + ".signature",
    };
  },
  logout: async (): Promise<void> => {
    await new Promise((r) => setTimeout(r, 200));
  },
};
