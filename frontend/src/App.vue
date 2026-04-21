<template>
  <!-- 全局 Naive UI 主题配置：注入二次元配色、圆角与字体覆盖 -->
  <n-config-provider :theme="naiveTheme" :theme-overrides="naiveThemeOverrides">
    <n-global-style />
    <n-message-provider>
      <n-dialog-provider>
        <div class="app-shell" :class="appThemeClass">
          <router-view />

          <transition name="boot-fade">
            <div v-if="authStore.isRestoringSession" class="boot-screen" aria-live="polite">
              <div class="boot-screen__panel">
                <div class="boot-screen__badge">TXT</div>
                <n-spin size="large" />
                <div class="boot-screen__title">正在恢复登录状态</div>
                <p class="boot-screen__description">正在确认你的账号信息与阅读入口，请稍候。</p>
              </div>
            </div>
          </transition>
        </div>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { computed, watch } from "vue";
import type { GlobalThemeOverrides } from "naive-ui";
import {
  NConfigProvider,
  NDialogProvider,
  NGlobalStyle,
  NMessageProvider,
  NSpin,
  darkTheme,
} from "naive-ui";
import { useRoute } from "vue-router";

import { useAuthStore } from "./stores/auth";
import { useAppThemeStore } from "./stores/app-theme";
import { usePreferencesStore } from "./stores/preferences";

const authStore = useAuthStore();
const route = useRoute();
const appThemeStore = useAppThemeStore();
const preferencesStore = usePreferencesStore();
const appThemeClass = computed(() => `app-theme--${appThemeStore.theme}`);
const naiveTheme = computed(() => (appThemeStore.theme === "dark" ? darkTheme : null));

/** 根据用户二次元偏好动态构建 Naive UI 主题覆盖配置 */
const naiveThemeOverrides = computed<GlobalThemeOverrides>(() => {
  const primary = preferencesStore.reader.themeColor || "#f4a4b4";
  const isSoft = preferencesStore.reader.borderRadius === "soft";
  const baseRadius = isSoft ? "12px" : "8px";
  const cardRadius = isSoft ? "20px" : "12px";
  const fontFamily = preferencesStore.reader.fontFamily === "lxgwwenkai"
    ? '"LXGW WenKai", "PingFang SC", "Microsoft YaHei", sans-serif'
    : '"PingFang SC", "Microsoft YaHei", sans-serif';

  return {
    common: {
      primaryColor: primary,
      primaryColorHover: primary,
      primaryColorPressed: primary,
      primaryColorSuppl: primary,
      borderRadius: baseRadius,
      borderRadiusSmall: isSoft ? "8px" : "6px",
      fontFamily,
    },
    Button: {
      borderRadiusSmall: baseRadius,
      borderRadiusMedium: baseRadius,
      borderRadiusLarge: isSoft ? "16px" : "10px",
    },
    Card: {
      borderRadius: cardRadius,
    },
    Modal: {
      borderRadius: cardRadius,
    },
    Input: {
      borderRadius: baseRadius,
    },
    Slider: {
      fillColor: primary,
      fillColorHover: primary,
    },
    Progress: {
      lineBgProcessing: primary,
    },
  };
});

watch(
  () => preferencesStore.reader.theme,
  (theme, previousTheme) => {
    // 阅读页里的局部主题切换仍然保留时，这里顺手把全局主题同步过去。
    if (
      !preferencesStore.initialized ||
      route.name !== "reader" ||
      theme === previousTheme ||
      theme === appThemeStore.theme
    ) {
      return;
    }

    appThemeStore.setTheme(theme, true);
  },
);
</script>

<style scoped>
.app-shell {
  min-height: 100dvh;
}

.boot-screen {
  position: fixed;
  inset: 0;
  z-index: 999;
  display: grid;
  place-items: center;
  padding: 24px;
  background: color-mix(in srgb, var(--app-shell-color) 78%, white 22%);
  backdrop-filter: blur(16px);
}

.boot-screen__panel {
  width: min(420px, 100%);
  display: grid;
  justify-items: center;
  gap: 18px;
  padding: 36px 28px;
  border: 1px solid var(--border-color);
  border-radius: 28px;
  background: color-mix(in srgb, var(--surface-color) 90%, white 10%);
  box-shadow: var(--surface-shadow);
  text-align: center;
}

.boot-screen__badge {
  display: grid;
  place-items: center;
  width: 56px;
  height: 56px;
  border-radius: 18px;
  background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
  color: white;
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.boot-screen__title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 700;
}

.boot-screen__description {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.boot-fade-enter-active,
.boot-fade-leave-active {
  transition: opacity 180ms ease;
}

.boot-fade-enter-from,
.boot-fade-leave-to {
  opacity: 0;
}
</style>
