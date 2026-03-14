<template>
  <div class="login-page">
    <n-grid cols="1 l:2" responsive="screen" :x-gap="24" :y-gap="24">
      <n-grid-item>
        <div class="login-page__intro">
          <div class="login-page__eyebrow">Round 13 Skeleton</div>
          <h1 class="login-page__title">先把前端跑起来，再逐步长出业务能力</h1>
          <p class="login-page__description">
            这一轮我们先搭好登录、路由、状态管理和 API 基础层。你现在只需要知道：
            登录成功后，页面会自动进入业务区；刷新后会尝试恢复登录状态。
          </p>

          <n-space vertical :size="12">
            <n-alert type="info" :show-icon="false">
              后端默认账号：<strong>admin</strong> / <strong>admin123</strong>
            </n-alert>
            <n-alert type="success" :show-icon="false">
              路由守卫已启用：未登录时访问业务页会自动跳回登录页。
            </n-alert>
          </n-space>
        </div>
      </n-grid-item>

      <n-grid-item>
        <n-card class="login-page__card" :bordered="false">
          <n-space vertical :size="18">
            <div>
              <h2 class="login-page__form-title">登录</h2>
              <p class="login-page__form-subtitle">先验证后端认证链路已经连通。</p>
            </div>

            <n-form label-placement="top">
              <n-form-item label="用户名">
                <n-input v-model:value="form.username" placeholder="请输入用户名" />
              </n-form-item>

              <n-form-item label="密码">
                <n-input
                  v-model:value="form.password"
                  type="password"
                  show-password-on="click"
                  placeholder="请输入密码"
                  @keydown.enter.prevent="handleLogin"
                />
              </n-form-item>

              <n-button
                type="primary"
                size="large"
                block
                :loading="submitting"
                @click="handleLogin"
              >
                登录并进入书架
              </n-button>
            </n-form>
          </n-space>
        </n-card>
      </n-grid-item>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
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

import { getErrorMessage } from "../api/client";
import { useAuthStore } from "../stores/auth";

const authStore = useAuthStore();
const message = useMessage();
const route = useRoute();
const router = useRouter();

const submitting = ref(false);
const form = reactive({
  username: "admin",
  password: "admin123",
});

async function handleLogin() {
  if (!form.username.trim() || !form.password.trim()) {
    message.warning("请先输入用户名和密码");
    return;
  }

  submitting.value = true;

  try {
    await authStore.login({
      username: form.username.trim(),
      password: form.password,
    });

    message.success("登录成功");

    const redirect = typeof route.query.redirect === "string" ? route.query.redirect : "/books";
    await router.push(redirect);
  } catch (error) {
    message.error(getErrorMessage(error));
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.login-page {
  width: min(1100px, 100%);
  margin: 0 auto;
  padding: 24px 0;
}

.login-page__intro,
.login-page__card {
  height: 100%;
  border-radius: 28px;
}

.login-page__intro {
  padding: clamp(24px, 5vw, 40px);
  background:
    radial-gradient(circle at top right, rgba(184, 93, 54, 0.22), transparent 34%),
    color-mix(in srgb, var(--surface-color) 92%, white 8%);
  box-shadow: var(--surface-shadow);
}

.login-page__eyebrow {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  background: var(--primary-soft);
  color: var(--primary-color);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.login-page__title {
  margin: 20px 0 14px;
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
  font-size: 28px;
}

.login-page__card {
  background: color-mix(in srgb, var(--surface-color) 94%, white 6%);
  box-shadow: var(--surface-shadow);
}
</style>
