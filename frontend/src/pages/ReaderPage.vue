<template>
  <page-placeholder
    eyebrow="Reader"
    :title="`阅读页占位（书籍 ${bookId} / 章节 ${chapterIndex}）`"
    description="阅读器正文、目录抽屉、字号设置、主题切换和阅读进度同步会在后续轮次接进来。当前先保证阅读路由结构已经正确。"
    :tips="['支持动态章节参数', '后续接 progress 同步', '后续接章节正文接口']"
  >
    <n-space wrap>
      <router-link :to="{ name: 'book-detail', params: { bookId } }">
        <n-button secondary>返回详情</n-button>
      </router-link>
      <router-link :to="{ name: 'rules' }">
        <n-button tertiary>去规则页</n-button>
      </router-link>
    </n-space>
  </page-placeholder>
</template>

<script setup lang="ts">
import { NButton, NSpace } from "naive-ui";
import { RouterLink } from "vue-router";

import PagePlaceholder from "../components/PagePlaceholder.vue";

withDefaults(
  defineProps<{
    bookId: number;
    chapterIndex?: number;
  }>(),
  {
    chapterIndex: 0,
  },
);
</script>
