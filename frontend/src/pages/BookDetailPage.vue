<template>
  <page-placeholder
    eyebrow="Book Detail"
    :title="`书籍详情页占位（ID: ${bookId}）`"
    description="后面这里会展示书籍信息、目录列表、重新解析按钮和跳转阅读页入口。现在先把路由参数和页面框架固定下来。"
    :tips="['支持动态路由参数', '预留目录接口', '后续接 /api/books/{id} 与 chapters']"
  >
    <n-space wrap>
      <router-link :to="{ name: 'reader', params: { bookId, chapterIndex: 0 } }">
        <n-button type="primary">去阅读页</n-button>
      </router-link>
      <router-link :to="{ name: 'books' }">
        <n-button secondary>返回书架</n-button>
      </router-link>
    </n-space>
  </page-placeholder>
</template>

<script setup lang="ts">
import { NButton, NSpace } from "naive-ui";
import { RouterLink } from "vue-router";

import PagePlaceholder from "../components/PagePlaceholder.vue";

defineProps<{
  bookId: number;
}>();
</script>
