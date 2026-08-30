import { AuthResponse, LoginCredentials, User } from "@/types/auth.types";
import { MOCK_USERS } from "@/data/userData";

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    await new Promise((r) => setTimeout(r, 900));
    if (!credentials.email || credentials.password.length < 8) {
      throw new Error("Invalid email or password");
    }

    const matchedUser = MOCK_USERS.find(
      (u) => u.email.toLowerCase() === credentials.email.toLowerCase()
    );

    const user: User = matchedUser
      ? { ...matchedUser }
      : {
          id: "usr-guest",
          name: credentials.email.split("@")[0],
          email: credentials.email,
          role: "security_analyst",
        };

    return {
      user,
      token: "mock-jwt-token." + btoa(credentials.email) + ".signature",
    };
  },
  logout: async (): Promise<void> => {
    await new Promise((r) => setTimeout(r, 200));
  },
};