import { createApp } from "vue";

import App from "./App.vue";
import { router } from "./router";
import { useAuthStore } from "./stores/auth";
import { useAppThemeStore } from "./stores/app-theme";
import { pinia } from "./stores";
import { installGlobalErrorHandling, notifyGlobalError } from "./utils/app-notifier";
import "./styles/index.css";
import "./styles/tailwind.css";

installGlobalErrorHandling();

// PWA Service Worker 更新检测：当 SW 更新后自动刷新页面
// 避免 PC 端触发 SW 更新后，安卓 PWA 加载新旧资源混合导致渲染异常（如白线）
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.addEventListener("controllerchange", () => {
    window.location.reload();
  });
}

const app = createApp(App);

app.config.errorHandler = (error) => {
  notifyGlobalError(error, "页面渲染出现异常，请刷新后重试");
  console.error(error);
};

router.onError((error) => {
  notifyGlobalError(error, "页面跳转失败，请稍后重试");
});

app.use(pinia);

// 应用启动时先恢复全局主题，避免页面首次渲染出现明显闪烁。
const appThemeStore = useAppThemeStore(pinia);
appThemeStore.initialize();

const authStore = useAuthStore(pinia);
void authStore.ensureReady();

app.use(router);
app.mount("#app");
