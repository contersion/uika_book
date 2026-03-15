<template>
  <div class="login-page">
    <n-grid cols="1 l:2" responsive="screen" :x-gap="24" :y-gap="24">
      <n-grid-item>
        <div class="login-page__intro">
          <div class="login-page__eyebrow">TXT Reader</div>
          <h1 class="login-page__title">继续你的阅读，而不是重新找回进度</h1>
          <p class="login-page__description">
            登录成功后会自动进入书架；如果你是从业务页被拦截回来的，系统会在认证成功后自动带你回到原来的页面。
          </p>

          <n-space vertical :size="12">
            <n-alert type="info" :show-icon="false">
              后端默认账号：<strong>admin</strong> / <strong>admin123</strong>
            </n-alert>
            <n-alert type="success" :show-icon="false">
              已启用登录态恢复与路由守卫，刷新后会自动尝试恢复会话。
            </n-alert>
          </n-space>

          <div class="login-page__feature-list" aria-label="登录后可用能力">
            <div class="login-page__feature-item">
              <span class="login-page__feature-dot" />
              进入书架、书籍详情、阅读页与规则管理页
            </div>
            <div class="login-page__feature-item">
              <span class="login-page__feature-dot" />
              使用 token 持久化登录状态
            </div>
            <div class="login-page__feature-item">
              <span class="login-page__feature-dot" />
              登录失败时显示后端真实错误提示
            </div>
          </div>
        </div>
      </n-grid-item>

      <n-grid-item>
        <n-card class="login-page__card" :bordered="false">
          <n-space vertical :size="18">
            <div>
              <h2 class="login-page__form-title">登录</h2>
              <p class="login-page__form-subtitle">
                {{ redirectHint }}
              </p>
            </div>

            <n-alert
              v-if="authStore.errorMessage"
              type="error"
              :show-icon="false"
              class="login-page__error"
            >
              {{ authStore.errorMessage }}
            </n-alert>

            <n-form label-placement="top">
              <n-form-item label="用户名">
                <n-input
                  v-model:value="form.username"
                  placeholder="请输入用户名"
                  :disabled="authStore.loginPending"
                  @update:value="clearError"
                />
              </n-form-item>

              <n-form-item label="密码">
                <n-input
                  v-model:value="form.password"
                  type="password"
                  show-password-on="click"
                  placeholder="请输入密码"
                  :disabled="authStore.loginPending"
                  @update:value="clearError"
                  @keydown.enter.prevent="handleLogin"
                />
              </n-form-item>

              <n-button
                type="primary"
                size="large"
                block
                :loading="authStore.loginPending"
                @click="handleLogin"
              >
                登录并进入书架
              </n-button>
            </n-form>

            <div class="login-page__footnote">
              如果后端未启动，登录页会直接提示连接失败，方便你区分“服务没开”和“账号密码错误”。
            </div>
          </n-space>
        </n-card>
      </n-grid-item>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive } from "vue";
import {
  NAlert,
  NButton,
  NCard,
  NForm,
  NFormItem,
  NGrid,
  NGridItem,
  NInput,
  NSpace,
  useMessage,
} from "naive-ui";
import { useRoute, useRouter } from "vue-router";

import { useAuthStore } from "../stores/auth";

const authStore = useAuthStore();
const message = useMessage();
const route = useRoute();
const router = useRouter();

const form = reactive({
  username: "admin",
  password: "admin123",
});

const redirectHint = computed(() => {
  if (typeof route.query.redirect === "string" && route.query.redirect !== "/books") {
    return "登录成功后会自动回到你刚才尝试访问的页面。";
  }

  return "输入账号后即可进入书架，继续后续业务操作。";
});

function clearError() {
  if (authStore.errorMessage) {
    authStore.setError(null);
  }
}

async function handleLogin() {
  clearError();

  if (!form.username.trim() || !form.password.trim()) {
    authStore.setError("请先输入用户名和密码。");
    return;
  }

  try {
    await authStore.login({
      username: form.username.trim(),
      password: form.password,
    });

    message.success("登录成功");

    const redirect = typeof route.query.redirect === "string" ? route.query.redirect : "/books";
    await router.push(redirect);
  } catch {}
}
</script>

<style scoped>
.login-page {
  width: min(1100px, 100%);
  margin: 0 auto;
  min-height: 100dvh;
  display: grid;
  align-items: center;
  padding: 24px 0;
}

.login-page__intro,
.login-page__card {
  height: 100%;
  border-radius: 28px;
}

.login-page__intro {
  display: grid;
  gap: 22px;
  padding: clamp(24px, 5vw, 40px);
  background:
    radial-gradient(circle at top right, rgba(184, 93, 54, 0.22), transparent 34%),
    color-mix(in srgb, var(--surface-color) 92%, white 8%);
  box-shadow: var(--surface-shadow);
}

.login-page__eyebrow {
  display: inline-flex;
  width: fit-content;
  padding: 6px 12px;
  border-radius: 999px;
  background: var(--primary-soft);
  color: var(--primary-color);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.login-page__title {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(34px, 5vw, 54px);
  line-height: 1.05;
}

.login-page__description,
.login-page__form-subtitle {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.login-page__form-title {
  margin: 0 0 8px;
  font-family: var(--font-display);
  font-size: 28px;
}

.login-page__card {
  background: color-mix(in srgb, var(--surface-color) 94%, white 6%);
  box-shadow: var(--surface-shadow);
}

.login-page__feature-list {
  display: grid;
  gap: 12px;
}

.login-page__feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--text-secondary);
  line-height: 1.7;
}

.login-page__feature-dot {
  width: 10px;
  height: 10px;
  flex: 0 0 auto;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
  box-shadow: 0 0 0 6px var(--primary-soft);
}

.login-page__error {
  border-radius: 16px;
}

.login-page__footnote {
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.7;
}

@media (max-width: 1023px) {
  .login-page {
    min-height: auto;
    padding: 24px 0 40px;
  }
}
</style>
