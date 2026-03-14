import { apiClient } from "./client";
import type { LoginPayload, TokenResponse, User } from "../types/api";

export const authApi = {
  login(payload: LoginPayload) {
    return apiClient.post<TokenResponse>("/api/auth/login", payload, {
      auth: false,
    });
  },
  getCurrentUser() {
    return apiClient.get<User>("/api/auth/me");
  },
};
