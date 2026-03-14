<template>
  <page-placeholder
    eyebrow="Chapter Rules"
    title="目录规则页骨架已准备好"
    description="这里后续会接规则列表、增删改、规则测试和默认规则设置。当前先把业务页入口和 API 模块骨架立起来。"
    :tips="['预留 chapter-rules API', '预留规则测试接口', '已纳入鉴权业务区']"
  >
    <n-space wrap>
      <router-link :to="{ name: 'books' }">
        <n-button secondary>返回书架</n-button>
      </router-link>
      <router-link :to="{ name: 'reader', params: { bookId: 1, chapterIndex: 0 } }">
        <n-button tertiary>打开占位阅读页</n-button>
      </router-link>
    </n-space>
  </page-placeholder>
</template>

<script setup lang="ts">
import { NButton, NSpace } from "naive-ui";
import { RouterLink } from "vue-router";

import PagePlaceholder from "../components/PagePlaceholder.vue";
</script>
