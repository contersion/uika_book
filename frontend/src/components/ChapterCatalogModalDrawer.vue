<template>
  <!-- Mobile: right drawer -->
  <transition name="catalog-drawer">
    <div
      v-if="isCompactViewport && show"
      class="catalog-drawer"
      @click="handleShowChange(false)"
    >
      <div
        class="catalog-drawer__panel"
        :style="{ width: drawerWidth + 'px' }"
        @click.stop
      >
        <section class="chapter-catalog-panel chapter-catalog-panel--drawer">
          <div class="chapter-catalog-panel__summary">
            <div class="chapter-catalog-panel__heading">
              <strong>目录</strong>
              <span class="chapter-catalog-panel__count">{{ chapterCountLabel }}</span>
            </div>
            <p v-if="bookTitle" class="chapter-catalog-panel__book">{{ bookTitle }}</p>
            <p class="chapter-catalog-panel__hint">
              点击任意章节后会直接跳转到阅读页，并自动关闭目录面板。
            </p>
          </div>

          <div class="chapter-catalog-panel__body">
            <div v-if="chapters.length === 0" class="chapter-catalog-panel__empty flex flex-col items-center justify-center py-8 text-gray-500">
              <p>当前还没有可展示的目录</p>
              <p class="text-sm">请稍后再试或重新解析目录。</p>
            </div>

            <div v-else class="chapter-catalog-list">
              <button
                v-for="chapter in chapters"
                :key="`drawer-${chapter.id}`"
                type="button"
                class="chapter-catalog-list__item"
                @click="handleChapterSelect(chapter.chapter_index)"
              >
                <span class="chapter-catalog-list__index">
                  {{ formatChapterOrdinal(chapter.chapter_index) }}
                </span>
                <strong class="chapter-catalog-list__title">{{ chapter.chapter_title }}</strong>
                <span class="chapter-catalog-list__meta">
                  范围 {{ formatNumber(chapter.start_offset) }} - {{ formatNumber(chapter.end_offset) }}
                </span>
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  </transition>

  <!-- Desktop: Dialog -->
  <Dialog :open="!isCompactViewport && show" @update:open="handleShowChange">
    <DialogContent class="max-w-2xl">
      <DialogHeader>
        <DialogTitle>
          <div class="chapter-catalog-panel__heading">
            <strong>目录</strong>
            <span class="chapter-catalog-panel__count">{{ chapterCountLabel }}</span>
          </div>
        </DialogTitle>
      </DialogHeader>

      <section class="chapter-catalog-panel chapter-catalog-panel--modal">
        <div class="chapter-catalog-panel__summary">
          <p v-if="bookTitle" class="chapter-catalog-panel__book">{{ bookTitle }}</p>
          <p class="chapter-catalog-panel__hint">
            点击任意章节后会直接跳转到阅读页，并自动关闭目录面板。
          </p>
        </div>

        <div class="chapter-catalog-panel__body">
          <div v-if="chapters.length === 0" class="chapter-catalog-panel__empty flex flex-col items-center justify-center py-8 text-gray-500">
            <p>当前还没有可展示的目录</p>
            <p class="text-sm">请稍后再试或重新解析目录。</p>
          </div>

          <div v-else class="chapter-catalog-list">
            <button
              v-for="chapter in chapters"
              :key="`modal-${chapter.id}`"
              type="button"
              class="chapter-catalog-list__item"
              @click="handleChapterSelect(chapter.chapter_index)"
            >
              <span class="chapter-catalog-list__index">
                {{ formatChapterOrdinal(chapter.chapter_index) }}
              </span>
              <strong class="chapter-catalog-list__title">{{ chapter.chapter_title }}</strong>
              <span class="chapter-catalog-list__meta">
                范围 {{ formatNumber(chapter.start_offset) }} - {{ formatNumber(chapter.end_offset) }}
              </span>
            </button>
          </div>
        </div>
      </section>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import type { BookChapter } from "../types/api";
import { formatNumber } from "../utils/format";

const MOBILE_BREAKPOINT = 720;

const props = defineProps<{
  show: boolean;
  bookTitle: string;
  chapterCount: number;
  chapters: BookChapter[];
}>();

const emit = defineEmits<{
  "update:show": [value: boolean];
  select: [chapterIndex: number];
}>();

const viewportWidth = ref(
  typeof window === "undefined" ? MOBILE_BREAKPOINT + 1 : window.innerWidth,
);

const isCompactViewport = computed(() => viewportWidth.value <= MOBILE_BREAKPOINT);
const drawerWidth = computed(() => Math.min(Math.max(viewportWidth.value, 320), 420));
const chapterCountLabel = computed(() => `共 ${formatNumber(props.chapterCount)} 章`);

onMounted(() => {
  syncViewportWidth();

  if (typeof window === "undefined") {
    return;
  }

  window.addEventListener("resize", handleWindowResize, { passive: true });
});

onUnmounted(() => {
  if (typeof window === "undefined") {
    return;
  }

  window.removeEventListener("resize", handleWindowResize);
});

function syncViewportWidth() {
  if (typeof window === "undefined") {
    return;
  }

  viewportWidth.value = window.innerWidth;
}

function handleWindowResize() {
  syncViewportWidth();
}

function handleShowChange(value: boolean) {
  emit("update:show", value);
}

function handleChapterSelect(chapterIndex: number) {
  emit("select", chapterIndex);
}

function formatChapterOrdinal(index: number) {
  return `第 ${formatNumber(index + 1)} 章`;
}
</script>

<style scoped>
.catalog-drawer {
  position: fixed;
  inset: 0;
  z-index: 100;
}

.catalog-drawer::before {
  content: "";
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
}

.catalog-drawer__panel {
  position: absolute;
  top: 0;
  right: 0;
  height: 100%;
  overflow-y: auto;
  background: var(--surface-color);
  padding: 20px;
  box-sizing: border-box;
}

.catalog-drawer-enter-active,
.catalog-drawer-leave-active {
  transition: opacity 280ms ease;
}

.catalog-drawer-enter-from,
.catalog-drawer-leave-to {
  opacity: 0;
}

.catalog-drawer-enter-active .catalog-drawer__panel,
.catalog-drawer-leave-active .catalog-drawer__panel {
  transition: transform 280ms ease;
}

.catalog-drawer-enter-from .catalog-drawer__panel,
.catalog-drawer-leave-to .catalog-drawer__panel {
  transform: translateX(100%);
}

.chapter-catalog-panel {
  display: grid;
  gap: 18px;
}

.chapter-catalog-panel__summary {
  display: grid;
  gap: 10px;
  padding: 18px 20px;
  border: 1px solid var(--border-color-soft);
  border-radius: 22px;
  background:
    radial-gradient(circle at top right, rgba(74, 159, 217, 0.16), transparent 34%),
    linear-gradient(135deg, var(--surface-raised), var(--surface-soft));
}

.chapter-catalog-panel__heading {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.chapter-catalog-panel__heading strong {
  font-size: 22px;
}

.chapter-catalog-panel__count {
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
}

.chapter-catalog-panel__book,
.chapter-catalog-panel__hint {
  margin: 0;
}

.chapter-catalog-panel__book {
  font-size: 16px;
  font-weight: 600;
  line-height: 1.6;
}

.chapter-catalog-panel__hint {
  color: var(--text-secondary);
  line-height: 1.7;
}

.chapter-catalog-panel__body {
  max-height: min(62vh, 560px);
  overflow: auto;
  padding-right: 12px;
  scrollbar-width: auto;
}

.chapter-catalog-panel__body::-webkit-scrollbar {
  width: 14px;
}

.chapter-catalog-panel__body::-webkit-scrollbar-thumb:vertical {
  min-height: 48px;
}

@media (hover: none) {
  .chapter-catalog-panel__body::-webkit-scrollbar {
    width: 16px;
  }
}

.chapter-catalog-panel__body::-webkit-scrollbar-track {
  background: transparent;
}

.chapter-catalog-panel__body::-webkit-scrollbar-thumb {
  background: rgba(74, 159, 217, 0.5);
  border-radius: 999px;
}

.chapter-catalog-panel__body::-webkit-scrollbar-thumb:hover {
  background: rgba(74, 159, 217, 0.7);
}

.chapter-catalog-panel--drawer .chapter-catalog-panel__body {
  max-height: calc(100vh - 220px);
}

.chapter-catalog-panel__empty {
  padding: 28px 0;
}

.chapter-catalog-list {
  display: grid;
  gap: 10px;
}

.chapter-catalog-list__item {
  width: 100%;
  display: grid;
  gap: 6px;
  padding: 16px 18px;
  border: 1px solid var(--border-color-soft);
  border-radius: 18px;
  background: var(--surface-panel-bg);
  text-align: left;
  cursor: pointer;
  transition:
    transform 160ms ease,
    box-shadow 160ms ease,
    border-color 160ms ease,
    background 160ms ease;
}

.chapter-catalog-list__item:hover {
  transform: translateY(-1px);
  border-color: var(--border-color);
  box-shadow: var(--shadow-soft);
  background: var(--surface-panel-soft-bg);
}

.chapter-catalog-list__item:focus-visible {
  outline: 2px solid color-mix(in srgb, var(--accent-color) 72%, white 28%);
  outline-offset: 2px;
}

.chapter-catalog-list__index,
.chapter-catalog-list__meta {
  color: var(--text-secondary);
  font-size: 13px;
}

.chapter-catalog-list__title {
  font-size: 16px;
  line-height: 1.65;
}

@media (max-width: 720px) {
  .chapter-catalog-panel__summary {
    padding: 16px 18px;
  }

  .chapter-catalog-panel__heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .chapter-catalog-panel__body {
    max-height: calc(100vh - 240px);
  }
}
</style>
