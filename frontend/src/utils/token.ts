const TOKEN_STORAGE_KEY = "txt-reader/token";

export const authTokenStorage = {
  get() {
    return window.localStorage.getItem(TOKEN_STORAGE_KEY);
  },
  set(token: string) {
    window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
  },
  clear() {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
  },
};
