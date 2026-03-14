<template>
  <page-placeholder
    eyebrow="Bookshelf"
    title="书架页骨架已准备好"
    description="这一页后面会接书籍列表、搜索、上传和删除功能。当前先确认：登录后可以进入业务页，基础 layout 和路由已经生效。"
    :tips="['已接入路由守卫', '已接入 Pinia', 'API 层已预留 books 接口']"
  >
    <n-space wrap>
      <router-link :to="{ name: 'book-detail', params: { bookId: 1 } }">
        <n-button type="primary">打开占位详情页</n-button>
      </router-link>
      <router-link :to="{ name: 'rules' }">
        <n-button secondary>打开规则管理页</n-button>
      </router-link>
    </n-space>
  </page-placeholder>
</template>

<script setup lang="ts">
import { NButton, NSpace } from "naive-ui";
import { RouterLink } from "vue-router";

import PagePlaceholder from "../components/PagePlaceholder.vue";
</script>
