<template>
  <n-card class="page-placeholder" :bordered="false">
    <n-space vertical :size="18">
      <div v-if="eyebrow" class="page-placeholder__eyebrow">{{ eyebrow }}</div>
      <div class="page-placeholder__header">
        <h1 class="page-placeholder__title">{{ title }}</h1>
        <p class="page-placeholder__description">{{ description }}</p>
      </div>

      <n-space v-if="tips.length" wrap size="small">
        <n-tag v-for="tip in tips" :key="tip" round :bordered="false" type="success">
          {{ tip }}
        </n-tag>
      </n-space>

      <div class="page-placeholder__content">
        <slot />
      </div>
    </n-space>
  </n-card>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { NCard, NSpace, NTag } from "naive-ui";

const props = withDefaults(
  defineProps<{
    title: string;
    description: string;
    eyebrow?: string;
    tips?: string[];
  }>(),
  {
    eyebrow: "",
    tips: () => [],
  },
);

const tips = computed(() => props.tips);
</script>

<style scoped>
.page-placeholder {
  border-radius: 28px;
  background: color-mix(in srgb, var(--surface-color) 94%, white 6%);
  box-shadow: var(--surface-shadow);
}

.page-placeholder__eyebrow {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--primary-color);
  background: var(--primary-soft);
}

.page-placeholder__header {
  display: grid;
  gap: 10px;
}

.page-placeholder__title {
  margin: 0;
  font-size: clamp(28px, 4vw, 38px);
  line-height: 1.1;
}

.page-placeholder__description {
  margin: 0;
  max-width: 760px;
  font-size: 16px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.page-placeholder__content {
  display: grid;
  gap: 18px;
  margin-top: 12px;
}
</style>
