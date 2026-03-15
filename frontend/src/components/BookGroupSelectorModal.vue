<template>
  <n-modal
    :show="show"
    preset="card"
    :mask-closable="!submitting"
    :closable="!submitting"
    :style="{ width: 'min(680px, calc(100vw - 24px))' }"
    @update:show="handleShowChange"
  >
    <template #header>
      <span>管理分组</span>
    </template>

    <section class="group-selector__intro">
      <strong>{{ bookTitle || '当前书籍' }}</strong>
      <p>一本书可以同时属于多个分组，但必须至少保留一个真实分组。</p>
    </section>

    <n-alert
      v-if="draftGroupIds.length === 0"
      type="warning"
      :show-icon="false"
      class="group-selector__alert"
    >
      至少选择一个分组后才能保存。
    </n-alert>

    <n-empty v-if="groups.length === 0" description="当前还没有可选分组，请先去创建分组。" />

    <n-checkbox-group v-else v-model:value="draftGroupIds" class="group-selector__group">
      <div class="group-selector__options">
        <label v-for="group in groups" :key="group.id" class="group-selector__option">
          <div>
            <strong>{{ group.name }}</strong>
            <p>当前包含 {{ group.book_count }} 本书</p>
          </div>
          <n-checkbox :value="group.id" />
        </label>
      </div>
    </n-checkbox-group>

    <template #footer>
      <div class="group-selector__footer">
        <n-button :disabled="submitting" @click="handleShowChange(false)">取消</n-button>
        <n-button
          type="primary"
          :loading="submitting"
          :disabled="draftGroupIds.length === 0 || groups.length === 0"
          @click="handleSubmit"
        >
          保存分组
        </n-button>
      </div>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { NAlert, NButton, NCheckbox, NCheckboxGroup, NEmpty, NModal } from "naive-ui";

import type { BookGroup } from "../types/api";

const props = defineProps<{
  show: boolean;
  bookTitle: string;
  groups: BookGroup[];
  selectedGroupIds: number[];
  submitting: boolean;
}>();

const emit = defineEmits<{
  "update:show": [value: boolean];
  submit: [groupIds: number[]];
}>();

const draftGroupIds = ref<number[]>([]);

watch(
  () => [props.show, props.selectedGroupIds],
  () => {
    draftGroupIds.value = [...props.selectedGroupIds];
  },
  { immediate: true, deep: true },
);

function handleShowChange(value: boolean) {
  emit("update:show", value);
}

function handleSubmit() {
  if (draftGroupIds.value.length === 0) {
    return;
  }

  emit("submit", [...draftGroupIds.value]);
}
</script>

<style scoped>
.group-selector__intro {
  margin-bottom: 16px;
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.58);
}

.group-selector__intro p {
  margin: 6px 0 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.group-selector__alert {
  margin-bottom: 16px;
  border-radius: 16px;
}

.group-selector__group {
  width: 100%;
}

.group-selector__options {
  display: grid;
  gap: 12px;
}

.group-selector__option {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  padding: 16px 18px;
  border: 1px solid rgba(109, 90, 74, 0.1);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.64);
  cursor: pointer;
}

.group-selector__option p {
  margin: 6px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.group-selector__footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 720px) {
  .group-selector__option,
  .group-selector__footer {
    display: grid;
    grid-template-columns: 1fr;
  }
}
</style>
