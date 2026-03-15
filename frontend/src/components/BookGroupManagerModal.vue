<template>
  <n-modal
    :show="show"
    preset="card"
    :mask-closable="!busy"
    :closable="!busy"
    :style="{ width: 'min(760px, calc(100vw - 24px))' }"
    @update:show="handleShowChange"
  >
    <template #header>
      <span>分组管理</span>
    </template>

    <section class="group-manager__create">
      <div>
        <strong>创建新分组</strong>
        <p>分组名不能为空，且同一用户下不能重复。</p>
      </div>

      <div class="group-manager__create-form">
        <n-input
          v-model:value="newGroupName"
          maxlength="100"
          placeholder="例如：科幻 / 已读 / 收藏"
          :disabled="busy"
          @keydown.enter.prevent="emitCreate"
        />
        <n-button type="primary" :disabled="busy || !newGroupName.trim()" @click="emitCreate">
          创建分组
        </n-button>
      </div>
    </section>

    <n-empty v-if="groups.length === 0" description="还没有真实分组，可以先创建一个。" />

    <section v-else class="group-manager__list">
      <article v-for="group in groups" :key="group.id" class="group-manager__item">
        <template v-if="editingGroupId === group.id">
          <div class="group-manager__edit-row">
            <n-input
              v-model:value="editingName"
              maxlength="100"
              :disabled="busy"
              @keydown.enter.prevent="emitRename(group.id)"
            />
            <n-button tertiary :disabled="busy" @click="cancelEdit">取消</n-button>
            <n-button type="primary" :disabled="busy || !editingName.trim()" @click="emitRename(group.id)">
              保存
            </n-button>
          </div>
        </template>

        <template v-else>
          <div class="group-manager__meta">
            <div>
              <strong>{{ group.name }}</strong>
              <p>当前包含 {{ group.book_count }} 本书</p>
            </div>
            <n-tag round :bordered="false">{{ group.book_count }} 本</n-tag>
          </div>

          <div class="group-manager__actions">
            <n-button tertiary size="small" :disabled="busy" @click="startEdit(group)">
              重命名
            </n-button>
            <n-popconfirm @positive-click="() => emitDelete(group.id)">
              <template #trigger>
                <n-button tertiary size="small" type="error" :disabled="busy">
                  删除
                </n-button>
              </template>
              删除前会做安全校验，确认继续吗？
            </n-popconfirm>
          </div>
        </template>
      </article>
    </section>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { NButton, NEmpty, NInput, NModal, NPopconfirm, NTag } from "naive-ui";

import type { BookGroup } from "../types/api";

const props = defineProps<{
  show: boolean;
  groups: BookGroup[];
  busy: boolean;
}>();

const emit = defineEmits<{
  "update:show": [value: boolean];
  create: [name: string];
  rename: [payload: { groupId: number; name: string }];
  delete: [groupId: number];
}>();

const newGroupName = ref("");
const editingGroupId = ref<number | null>(null);
const editingName = ref("");

watch(
  () => props.show,
  (show) => {
    if (!show) {
      newGroupName.value = "";
      editingGroupId.value = null;
      editingName.value = "";
    }
  },
);

function handleShowChange(value: boolean) {
  emit("update:show", value);
}

function emitCreate() {
  const name = newGroupName.value.trim();
  if (!name) {
    return;
  }

  emit("create", name);
  newGroupName.value = "";
}

function startEdit(group: BookGroup) {
  editingGroupId.value = group.id;
  editingName.value = group.name;
}

function cancelEdit() {
  editingGroupId.value = null;
  editingName.value = "";
}

function emitRename(groupId: number) {
  const name = editingName.value.trim();
  if (!name) {
    return;
  }

  emit("rename", { groupId, name });
  cancelEdit();
}

function emitDelete(groupId: number) {
  emit("delete", groupId);
}
</script>

<style scoped>
.group-manager__create {
  display: grid;
  gap: 14px;
  margin-bottom: 20px;
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.55);
}

.group-manager__create p {
  margin: 6px 0 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.group-manager__create-form,
.group-manager__edit-row,
.group-manager__actions {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.group-manager__create-form :deep(.n-input),
.group-manager__edit-row :deep(.n-input) {
  flex: 1;
}

.group-manager__list {
  display: grid;
  gap: 12px;
}

.group-manager__item {
  display: grid;
  gap: 14px;
  padding: 16px 18px;
  border: 1px solid rgba(109, 90, 74, 0.1);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.64);
}

.group-manager__meta {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.group-manager__meta p {
  margin: 6px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
}

@media (max-width: 720px) {
  .group-manager__meta,
  .group-manager__create-form,
  .group-manager__edit-row,
  .group-manager__actions {
    display: grid;
    grid-template-columns: 1fr;
  }
}
</style>
