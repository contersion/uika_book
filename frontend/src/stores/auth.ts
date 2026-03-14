import { defineStore } from "pinia";

import { authApi } from "../api/auth";
import type { LoginPayload, User } from "../types/api";
import { authTokenStorage } from "../utils/token";

interface AuthState {
  token: string | null;
  user: User | null;
  initialized: boolean;
  bootstrapPromise: Promise<void> | null;
}

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    token: authTokenStorage.get(),
    user: null,
    initialized: false,
    bootstrapPromise: null,
  }),
  getters: {
    hasToken: (state) => Boolean(state.token),
    isAuthenticated: (state) => Boolean(state.token && state.user),
  },
  actions: {
    async ensureReady() {
      if (this.initialized) {
        return;
      }

      if (!this.bootstrapPromise) {
        this.bootstrapPromise = this.bootstrap().finally(() => {
          this.bootstrapPromise = null;
        });
      }

      await this.bootstrapPromise;
    },
    async bootstrap() {
      if (!this.token) {
        this.initialized = true;
        return;
      }

      try {
        this.user = await authApi.getCurrentUser();
      } catch {
        this.clearAuth();
      } finally {
        this.initialized = true;
      }
    },
    async login(payload: LoginPayload) {
      const tokenResponse = await authApi.login(payload);
      this.setToken(tokenResponse.access_token);

      try {
        this.user = await authApi.getCurrentUser();
        this.initialized = true;
      } catch (error) {
        this.clearAuth();
        throw error;
      }
    },
    logout() {
      this.clearAuth();
      this.initialized = true;
    },
    setToken(token: string) {
      this.token = token;
      authTokenStorage.set(token);
    },
    clearAuth() {
      this.token = null;
      this.user = null;
      authTokenStorage.clear();
    },
  },
});
