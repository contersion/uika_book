import { defineStore } from "pinia";

import { authApi } from "../api/auth";
import { ApiError, getErrorMessage } from "../api/client";
import type { LoginPayload, User } from "../types/api";
import { authTokenStorage } from "../utils/token";

interface AuthState {
  token: string | null;
  user: User | null;
  initialized: boolean;
  restorePending: boolean;
  loginPending: boolean;
  errorMessage: string | null;
  bootstrapPromise: Promise<void> | null;
}

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    token: authTokenStorage.get(),
    user: null,
    initialized: false,
    restorePending: false,
    loginPending: false,
    errorMessage: null,
    bootstrapPromise: null,
  }),
  getters: {
    hasToken: (state) => Boolean(state.token),
    isAuthenticated: (state) => Boolean(state.token && state.user),
    isRestoringSession: (state) => state.restorePending,
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
        this.restorePending = false;
        return;
      }

      this.restorePending = true;

      try {
        this.user = await authApi.getCurrentUser();
        this.errorMessage = null;
      } catch (error) {
        const message = error instanceof ApiError && error.status === 401
          ? "登录状态已失效，请重新登录。"
          : getErrorMessage(error);

        this.clearAuth();
        this.errorMessage = message;
      } finally {
        this.restorePending = false;
        this.initialized = true;
      }
    },
    async login(payload: LoginPayload) {
      this.loginPending = true;
      this.errorMessage = null;

      try {
        const tokenResponse = await authApi.login(payload);
        this.setToken(tokenResponse.access_token);
        this.user = await authApi.getCurrentUser();
        this.initialized = true;
      } catch (error) {
        this.clearAuth();
        this.errorMessage = getErrorMessage(error);
        throw error;
      } finally {
        this.loginPending = false;
      }
    },
    logout() {
      this.clearAuth();
      this.initialized = true;
      this.restorePending = false;
      this.loginPending = false;
      this.errorMessage = null;
    },
    setError(message: string | null) {
      this.errorMessage = message;
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
