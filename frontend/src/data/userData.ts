import { User } from "@/types/auth.types";

export const MOCK_USERS: User[] = [
  { id: "usr-1", name: "Ayaan Sharma", email: "analyst@example.com", role: "security_analyst" },
  { id: "usr-2", name: "Priya Nair", email: "soc@example.com", role: "soc_team_member" },
  { id: "usr-3", name: "Devraj Singh", email: "admin@example.com", role: "administrator" },
  { id: "usr-4", name: "Meera Iyer", email: "researcher@example.com", role: "researcher" },
];

export const mockUser: User = MOCK_USERS[0];