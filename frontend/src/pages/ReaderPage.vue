<template>
    <div
      class="reader-page"
      :class="[
        readerThemeClass,
        { 'reader-page--compact': isCompactViewport },
      ]"
      :style="readerStyleVars"
    >
    <div v-if="loading" class="reader-loading">
      <section class="reader-glass reader-loading__panel reader-loading__panel--rail">
        <div class="space-y-2">
          <Skeleton v-for="i in 7" :key="i" class="h-4 w-full" />
        </div>
      </section>
      <section class="reader-loading__main">
        <section class="reader-glass reader-loading__panel">
          <div class="space-y-2">
            <Skeleton v-for="i in 5" :key="i" class="h-4 w-full" />
          </div>
        </section>
        <section class="reader-paper reader-loading__paper">
          <div class="space-y-2">
            <Skeleton v-for="i in 14" :key="i" class="h-4 w-full" />
          </div>
        </section>
      </section>
      <section class="reader-glass reader-loading__panel reader-loading__panel--float">
        <div class="space-y-2">
          <Skeleton v-for="i in 4" :key="i" class="h-4 w-full" />
        </div>
      </section>
    </div>

    <page-status-panel
      v-else-if="pageError"
      variant="error"
      title="阅读页暂时无法打开"
      :description="pageError"
    >
      <template #action>
        <Button @click="loadReader">重新加载</Button>
        <Button variant="ghost" @click="goBack">返回详情</Button>
      </template>
    </page-status-panel>

    <page-status-panel
      v-else-if="chapters.length === 0"
      title="这本书暂时没有可展示的目录"
      description="可以先回到书籍详情页重新解析目录，或稍后再刷新一次。"
    >
      <template #action>
        <Button variant="outline" @click="loadReader">重新加载</Button>
        <Button variant="ghost" @click="goBack">返回详情</Button>
      </template>
    </page-status-panel>

    <div v-else class="reader-shell">
      <aside class="reader-rail" :class="{ 'reader-rail--active': shouldShowChrome }">
        <div class="reader-glass reader-rail__panel" @click.stop>
          <div class="reader-rail__brand">
            <span class="reader-eyebrow">Immersive Reader</span>
            <strong class="reader-rail__chapter">{{ currentChapterPositionLabel }}</strong>
            <span class="reader-rail__sync">{{ syncStatusTagLabel }}</span>
          </div>

          <div class="reader-rail__actions">
            <button type="button" class="reader-rail__action" @click.stop="goToBookshelf">
              <strong>返回书架</strong>
              <span>回到我的书架</span>
            </button>
            <button type="button" class="reader-rail__action" @click.stop="goBack">
              <strong>返回详情</strong>
              <span>回到书籍信息与目录入口</span>
            </button>
            <button type="button" class="reader-rail__action" @click.stop="openDrawer('catalog')">
              <strong>目录</strong>
              <span>从左侧抽屉浏览章节</span>
            </button>
            <button type="button" class="reader-rail__action" @click.stop="openDrawer('settings')">
              <strong>设置</strong>
              <span>字体、行高与主题</span>
            </button>
          </div>
        </div>
      </aside>

      <main class="reader-stage" @click="handleReadingSurfaceTap">
        <section class="reader-stage__hero">
          <span class="reader-eyebrow">Scroll Reading</span>

          <div class="reader-stage__header">
            <div>
              <p v-if="bookTitle" class="reader-stage__book">{{ bookTitle }}</p>
              <p class="reader-stage__chapter">{{ currentChapterPositionLabel }}</p>
              <h1 class="reader-stage__title">{{ currentChapterTitle }}</h1>
            </div>

            <div class="reader-stage__stat">
              <span>当前进度</span>
              <strong>{{ progressPercentLabel }}</strong>
              <small>{{ syncStatusTagLabel }}</small>
            </div>
          </div>

        </section>

        <section class="reader-paper">
          <Alert v-if="chapterError" variant="destructive" class="reader-page__alert">
            {{ chapterError }}
          </Alert>

          <div v-if="!currentChapter && chapterLoading" class="reader-content reader-content--loading">
            <div class="space-y-2">
              <Skeleton v-for="i in 10" :key="i" class="h-4 w-full" />
            </div>
          </div>

          <article
            v-else
            ref="contentRef"
            class="reader-content"
            :class="{ 'reader-content--dimmed': chapterLoading }"
          >
            <template v-if="currentChapter">
              <template
                v-for="(block, index) in currentChapterBlocks"
                :key="`block-${currentChapterIndex}-${index}`"
              >
                <p
                  v-if="block.type === 'paragraph'"
                  class="reader-content__paragraph"
                >
                  {{ block.content }}
                </p>
                <figure v-else class="reader-content__image-block">
                  <img
                    class="reader-content__image"
                    :src="block.src"
                    :alt="block.alt"
                    loading="lazy"
                  />
                </figure>
              </template>
            </template>
            <template v-else>正文载入中...</template>
          </article>
          <section v-if="isCompactViewport" class="reader-paper__chapter-nav" @click.stop>
            <div class="reader-paper__chapter-actions">
              <Button
                class="w-full"
                size="lg"
                variant="outline"
                :disabled="!canGoPrev || chapterLoading"
                @click="handlePrevChapter"
              >
                上一章
              </Button>
              <Button
                class="w-full"
                size="lg"
                :disabled="!canGoNext || chapterLoading"
                @click="handleNextChapter"
              >
                下一章
              </Button>
            </div>
          </section>
        </section>
      </main>

      <aside class="reader-float">
        <div class="reader-glass reader-float__panel" @click.stop>
          <div class="reader-float__stat">
            <span>已读进度</span>
            <strong>{{ progressPercentLabel }}</strong>
          </div>

          <div class="reader-progress-bar">
            <div
              class="reader-progress-bar__fill"
              :style="{ width: currentProgressPercent + '%' }"
            ></div>
          </div>

          <div class="reader-float__summary">
            <span>{{ currentChapterPositionLabel }}</span>
            <span>{{ syncStatusTagLabel }}</span>
          </div>

          <div class="reader-float__actions">
            <Button variant="outline" :disabled="!canGoPrev || chapterLoading" @click="handlePrevChapter">
              上一章
            </Button>
            <Button :disabled="!canGoNext || chapterLoading" @click="handleNextChapter">
              下一章
            </Button>
          </div>
        </div>
      </aside>
    </div>

    <transition name="reader-drawer">
      <div v-if="isDrawerOpen" class="reader-drawer">
        <div class="reader-drawer__backdrop" @click="activeDrawer = null"></div>
        <div class="reader-drawer__panel" :style="{ width: drawerWidth + 'px' }">
        <template v-if="activeDrawer === 'catalog'">
          <div class="reader-drawer__surface" :class="readerThemeClass">
            <div class="reader-drawer__header">
              <span class="reader-drawer__title">{{ drawerTitle }}</span>
              <button type="button" class="reader-drawer__close" @click="activeDrawer = null">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
            </div>
            <div class="reader-drawer__summary">
            <div>
              <span>{{ currentChapterPositionLabel }}</span>
              <strong>{{ progressPercentLabel }}</strong>
            </div>
            <p>{{ syncedProgressLabel }}</p>
          </div>

          <div class="reader-progress-bar reader-drawer__progress">
            <div
              class="reader-progress-bar__fill"
              :style="{ width: currentProgressPercent + '%' }"
            ></div>
          </div>

            <div
              ref="catalogListRef"
              class="reader-catalog__list reader-catalog__list--drawer"
              @scroll="handleCatalogScroll"
            >
              <div
                v-if="chapters.length > 200"
                :style="{ height: catalogTopPadding + 'px' }"
              />
              <button
                v-for="chapter in catalogVisibleChapters"
                :key="`drawer-${chapter.id}`"
                type="button"
                class="reader-catalog__item"
                :ref="(element) => setCatalogItemRef(chapter.chapter_index, element)"
                :class="{
                  'reader-catalog__item--active': chapter.chapter_index === currentChapterIndex,
                }"
                @click="handleChapterSelect(chapter.chapter_index)"
              >
                <span class="reader-catalog__index">{{ formatChapterOrdinal(chapter.chapter_index) }}</span>
                <strong class="reader-catalog__title">{{ chapter.chapter_title }}</strong>
              </button>
              <div
                v-if="chapters.length > 200"
                :style="{ height: catalogBottomPadding + 'px' }"
              />
            </div>
          </div>
        </template>

        <template v-else>
          <div class="reader-drawer__surface" :class="readerThemeClass">
            <div class="reader-drawer__header">
              <span class="reader-drawer__title">{{ drawerTitle }}</span>
              <button type="button" class="reader-drawer__close" @click="activeDrawer = null">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
            </div>
            <div class="reader-settings">
            <section class="reader-settings__group">
              <div class="reader-settings__label-row">
                <span>字体大小</span>
                <strong>{{ preferences.fontSize }}px</strong>
              </div>
              <Slider v-model="preferences.fontSize" :min="15" :max="28" :step="1" />
            </section>

            <section class="reader-settings__group">
              <div class="reader-settings__label-row">
                <span>行高</span>
                <strong>{{ preferences.lineHeight.toFixed(2) }}</strong>
              </div>
              <Slider v-model="preferences.lineHeight" :min="1.45" :max="2.5" :step="0.05" />
            </section>

            <section class="reader-settings__group">
              <div class="reader-settings__label-row">
                <span>阅读主题</span>
                <strong>{{ preferences.theme === 'dark' ? '深色' : '浅色' }}</strong>
              </div>
              <div class="reader-settings__theme-mode">{{ readerThemeLabel }}</div>
              <div class="flex flex-wrap gap-2">
                <label
                  class="reader-radio"
                  :class="{ 'reader-radio--active': preferences.theme === 'light' }"
                >
                  <input v-model="preferences.theme" type="radio" value="light" class="sr-only" />
                  <span>浅色</span>
                </label>
                <label
                  class="reader-radio"
                  :class="{ 'reader-radio--active': preferences.theme === 'dark' }"
                >
                  <input v-model="preferences.theme" type="radio" value="dark" class="sr-only" />
                  <span>深色</span>
                </label>
              </div>
            </section>

            <section class="reader-settings__group">
              <div class="reader-settings__label-row">
                <span>字间距</span>
                <strong>{{ preferences.letterSpacing.toFixed(2) }}px</strong>
              </div>
              <Slider v-model="preferences.letterSpacing" :min="0" :max="2" :step="0.05" />
            </section>

            <section class="reader-settings__group">
              <div class="reader-settings__label-row">
                <span>段间距</span>
                <strong>{{ preferences.paragraphSpacing.toFixed(2) }}x</strong>
              </div>
              <Slider v-model="preferences.paragraphSpacing" :min="0" :max="2.5" :step="0.05" />
            </section>

            <section class="reader-settings__group">
              <div class="reader-settings__label-row">
                <span>阅读宽度</span>
                <strong>{{ preferences.contentWidth }}ch</strong>
              </div>
              <Slider v-model="preferences.contentWidth" :min="56" :max="96" :step="1" />
            </section>
            </div>
          </div>
        </template>
        </div>
      </div>
    </transition>
    </div>
</template>
<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import type { ComponentPublicInstance } from "vue";
import { Button } from "@/components/ui/button";
import { Alert } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Slider } from "@/components/ui/slider";
import { useRoute, useRouter } from "vue-router";

import { booksApi } from "../api/books";
import { ApiError, buildApiUrl, getErrorMessage, resolveApiAssetUrl } from "../api/client";
import { usePreferencesStore } from "../stores/preferences";
import { useBooksCacheStore } from "../stores/booksCache";
import type {
  BookChapter,
  BookChapterContent,
  ReadingProgress,
  ReadingProgressPayload,
} from "../types/api";
import PageStatusPanel from "../components/PageStatusPanel.vue";
import { formatPercent } from "../utils/format";
import { authTokenStorage } from "../utils/token";

const PROGRESS_THROTTLE_MS = 5000;
const READER_SCROLL_ANCHOR = 120;
const COMPACT_BREAKPOINT = 980;
const MOBILE_CONTENT_WIDTH_MIN_PERCENT = 84;
const MOBILE_CONTENT_WIDTH_MAX_PERCENT = 100;
const CATALOG_ITEM_ESTIMATED_HEIGHT = 82;
const CATALOG_OVERSCAN = 8;

type ProgressSnapshot = ReadingProgressPayload;
type ReaderDrawerView = "catalog" | "settings";

interface RouteChapterState {
  provided: boolean;
  valid: boolean;
  value: number;
}

interface ReaderChapterContentView {
  body: string;
  trimmedPrefixLength: number;
}

interface ReaderParagraphBlock {
  type: "paragraph";
  content: string;
}

interface ReaderImageBlock {
  type: "image";
  src: string;
  alt: string;
}

type ReaderContentBlock = ReaderParagraphBlock | ReaderImageBlock;

const READER_IMAGE_TAG_PATTERN = /<img\b[^>]*>/giu;

const props = withDefaults(
  defineProps<{
    bookId: number;
    chapterIndex?: number;
  }>(),
  {
    chapterIndex: 0,
  },
);

const route = useRoute();
const router = useRouter();
const preferencesStore = usePreferencesStore();
const booksCacheStore = useBooksCacheStore();
const chapters = ref<BookChapter[]>([]);
const bookTitle = ref("");
const progress = ref<ProgressSnapshot | null>(null);
const sessionProgress = ref<ProgressSnapshot | null>(null);
const currentChapter = ref<BookChapterContent | null>(null);
const currentChapterIndex = ref(0);
const hasMeaningfulReadingActivity = ref(false);
const loading = ref(true);
const chapterLoading = ref(false);
const pageError = ref<string | null>(null);
const chapterError = ref<string | null>(null);
const syncState = ref<"idle" | "pending" | "syncing" | "error">("idle");
const preferences = reactive({
  ...preferencesStore.reader,
});
const contentRef = ref<HTMLElement | null>(null);
const catalogListRef = ref<HTMLElement | null>(null);
const activeDrawer = ref<ReaderDrawerView | null>(null);
const mobileChromeVisible = ref(false);
const viewportWidth = ref(COMPACT_BREAKPOINT + 200);
const catalogItemRefs = new Map<number, HTMLElement>();
const catalogScrollTop = ref(0);
const catalogListHeight = ref(0);

let progressSaveTimer: ReturnType<typeof setTimeout> | null = null;
let saveInFlight = false;
let queuedSnapshot: ProgressSnapshot | null = null;
let lastSavedProgressKey = "";
let suppressScrollTrackingUntil = 0;
let catalogScrollToken = 0;

const isCompactViewport = computed(() => viewportWidth.value <= COMPACT_BREAKPOINT);
const shouldShowChrome = computed(() => !isCompactViewport.value || mobileChromeVisible.value);
const progressPercentLabel = computed(() => formatPercent(currentProgressPercent.value));
const readerThemeClass = computed(() => `reader-page--${preferences.theme}`);
const readerThemeLabel = computed(() => (preferences.theme === "dark" ? "黑夜模式" : "白天模式"));
const drawerTitle = computed(() => (activeDrawer.value === "settings" ? "阅读设置" : "章节目录"));
const drawerWidth = computed(() => Math.min(Math.max(viewportWidth.value - 24, 280), 380));
const isDrawerOpen = computed({
  get: () => activeDrawer.value !== null,
  set: (value: boolean) => {
    if (!value) {
      activeDrawer.value = null;
    }
  },
});
const currentChapterTitle = computed(() => {
  return (
    currentChapter.value?.chapter_title ||
    chapters.value.find((chapter) => chapter.chapter_index === currentChapterIndex.value)?.chapter_title ||
    "正在载入章节"
  );
});
const currentChapterContentView = computed<ReaderChapterContentView>(() => {
  if (!currentChapter.value) {
    return {
      body: "",
      trimmedPrefixLength: 0,
    };
  }

  return buildReaderChapterContentView(
    currentChapter.value.content,
    currentChapter.value.chapter_title || currentChapterTitle.value,
  );
});
const currentChapterBody = computed(() => currentChapterContentView.value.body);
const currentChapterBlocks = computed(() => buildReaderContentBlocks(currentChapterBody.value));
const currentChapterTrimmedPrefixLength = computed(() => currentChapterContentView.value.trimmedPrefixLength);
const currentChapterPositionLabel = computed(() => {
  if (chapters.value.length === 0) {
    return "暂无目录";
  }

  return `第 ${currentChapterIndex.value + 1} / ${chapters.value.length} 章`;
});
const currentProgressPercent = computed(() => {
  if (sessionProgress.value) {
    return sessionProgress.value.percent;
  }

  if (progress.value) {
    return progress.value.percent;
  }

  if (chapters.value.length === 0) {
    return 0;
  }

  return roundPercent(((currentChapterIndex.value + 1) / chapters.value.length) * 100);
});
const syncStatusTagLabel = computed(() => {
  if (syncState.value === "syncing") {
    return "同步中";
  }

  if (syncState.value === "pending") {
    return "待同步";
  }

  if (syncState.value === "error") {
    return "同步待重试";
  }

  return progress.value ? "已同步" : "未同步";
});
const syncedProgressLabel = computed(() => {
  const displayPercent = formatPercent(currentProgressPercent.value);

  if (!progress.value && !sessionProgress.value) {
    return "还没有云端阅读进度";
  }

  if (syncState.value === "syncing") {
    return `正在同步阅读进度 · ${displayPercent}`;
  }

  if (syncState.value === "pending") {
    return `本地阅读到 ${displayPercent}，将于 15 秒内自动同步`;
  }

  if (syncState.value === "error") {
    return `同步失败，后续会继续重试 · ${displayPercent}`;
  }

  if (progress.value) {
    return `已同步到云端 ${formatPercent(progress.value.percent)} · 第 ${progress.value.chapter_index + 1} 章`;
  }

  return `当前进度 ${displayPercent}`;
});
const canGoPrev = computed(() => currentChapterIndex.value > 0);
const canGoNext = computed(() => currentChapterIndex.value < chapters.value.length - 1);
const readerStyleVars = computed(() => ({
  "--reader-font-size": `${preferences.fontSize}px`,
  "--reader-line-height": String(preferences.lineHeight),
  "--reader-letter-spacing": `${preferences.letterSpacing}px`,
  "--reader-paragraph-spacing": String(preferences.paragraphSpacing),
  "--reader-content-width": `${preferences.contentWidth}ch`,
  "--reader-content-width-mobile": `${mapReaderContentWidthForMobile(preferences.contentWidth)}%`,
}));

const catalogVirtualStart = computed(() => {
  const start = Math.floor(catalogScrollTop.value / CATALOG_ITEM_ESTIMATED_HEIGHT);
  return Math.max(0, start - CATALOG_OVERSCAN);
});

const catalogVirtualEnd = computed(() => {
  if (catalogListHeight.value <= 0) {
    return chapters.value.length;
  }
  const visibleCount = Math.ceil(catalogListHeight.value / CATALOG_ITEM_ESTIMATED_HEIGHT);
  const end = catalogVirtualStart.value + visibleCount + CATALOG_OVERSCAN * 2;
  return Math.min(chapters.value.length, end);
});

const catalogVisibleChapters = computed(() => {
  if (chapters.value.length <= 200) {
    return chapters.value;
  }
  return chapters.value.slice(catalogVirtualStart.value, catalogVirtualEnd.value);
});

const catalogTopPadding = computed(() => catalogVirtualStart.value * CATALOG_ITEM_ESTIMATED_HEIGHT);

const catalogBottomPadding = computed(() =>
  Math.max(0, (chapters.value.length - catalogVirtualEnd.value) * CATALOG_ITEM_ESTIMATED_HEIGHT)
);

watch(
  preferences,
  (value) => {
    preferencesStore.patchReader(value);
  },
  { deep: true },
);

watch(
  () => props.bookId,
  () => {
    void loadReader();
  },
  { immediate: true },
);

watch(
  () => route.params.chapterIndex,
  (value, previousValue) => {
    if (value === previousValue || loading.value || chapterLoading.value || chapters.value.length === 0) {
      return;
    }

    const state = getRouteChapterState();
    if (!state.provided) {
      return;
    }

    const normalizedIndex = normalizeChapterIndex(state.value);
    if (normalizedIndex === currentChapterIndex.value) {
      return;
    }

    void openChapter(normalizedIndex, {
      syncRoute: !state.valid || normalizedIndex !== state.value,
      replace: true,
      smoothScroll: false,
      restoreCharOffset: 0,
    });
  },
);

watch(
  () => activeDrawer.value,
  (value, previousValue) => {
    if (value === previousValue || value !== "catalog") {
      return;
    }

    void scheduleCatalogAutoScroll();
  },
);

watch(
  () => catalogVirtualStart.value,
  () => {
    catalogItemRefs.clear();
  },
);

watch(
  currentChapterIndex,
  (value, previousValue) => {
    if (value === previousValue || activeDrawer.value !== "catalog") {
      return;
    }

    void scheduleCatalogAutoScroll();
  },
);

onMounted(() => {
  if (typeof window === "undefined") {
    return;
  }

  syncViewportState();
  window.addEventListener("resize", handleWindowResize, { passive: true });
  window.addEventListener("scroll", handleWindowScroll, { passive: true });
  window.addEventListener("pagehide", handlePageHide);
  window.addEventListener("beforeunload", handleBeforeUnload);
  document.addEventListener("visibilitychange", handleVisibilityChange);
});

onUnmounted(() => {
  clearScheduledProgressSync();
  catalogScrollToken += 1;
  catalogItemRefs.clear();

  if (typeof window === "undefined") {
    return;
  }

  window.removeEventListener("resize", handleWindowResize);
  window.removeEventListener("scroll", handleWindowScroll);
  window.removeEventListener("pagehide", handlePageHide);
  window.removeEventListener("beforeunload", handleBeforeUnload);
  document.removeEventListener("visibilitychange", handleVisibilityChange);

  // 卸载前同步备份到本地，防止导航后刷新丢失进度
  const snapshot = captureCurrentProgressSnapshot();
  if (snapshot) {
    saveProgressToLocal(props.bookId, snapshot);
  }

  void preferencesStore.flushPendingPatch();
});

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

function roundPercent(value: number) {
  return Number(value.toFixed(2));
}

function getLocalProgressKey(bookId: number): string {
  return `reader:progress:${bookId}`;
}

function saveProgressToLocal(bookId: number, snapshot: ProgressSnapshot) {
  if (typeof window === "undefined") return;
  try {
    const payload = JSON.stringify(snapshot);
    localStorage.setItem(getLocalProgressKey(bookId), payload);
    sessionStorage.setItem(getLocalProgressKey(bookId), payload);
  } catch {
    // ignore
  }
}

function loadProgressFromLocal(bookId: number): ProgressSnapshot | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(getLocalProgressKey(bookId))
      || localStorage.getItem(getLocalProgressKey(bookId));
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<ProgressSnapshot>;
    if (
      typeof parsed.chapter_index !== "number" ||
      typeof parsed.char_offset !== "number" ||
      typeof parsed.percent !== "number" ||
      typeof parsed.updated_at !== "string"
    ) {
      return null;
    }
    return parsed as ProgressSnapshot;
  } catch {
    return null;
  }
}

function clearProgressLocal(bookId: number) {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem(getLocalProgressKey(bookId));
    sessionStorage.removeItem(getLocalProgressKey(bookId));
  } catch {
    // ignore
  }
}

function mapReaderContentWidthForMobile(contentWidth: number) {
  const ratio = clamp((contentWidth - 56) / (96 - 56), 0, 1);
  const percent = MOBILE_CONTENT_WIDTH_MIN_PERCENT
    + (MOBILE_CONTENT_WIDTH_MAX_PERCENT - MOBILE_CONTENT_WIDTH_MIN_PERCENT) * ratio;
  return Number(percent.toFixed(2));
}

function getRouteChapterState(): RouteChapterState {
  const raw = Array.isArray(route.params.chapterIndex)
    ? route.params.chapterIndex[0]
    : route.params.chapterIndex;

  if (raw === undefined) {
    return {
      provided: false,
      valid: true,
      value: 0,
    };
  }

  const parsed = Number(raw);
  return {
    provided: true,
    valid: Number.isFinite(parsed),
    value: Number.isFinite(parsed) ? parsed : 0,
  };
}

function normalizeChapterIndex(index: number) {
  if (chapters.value.length === 0) {
    return 0;
  }

  return clamp(index, 0, chapters.value.length - 1);
}

function formatChapterOrdinal(index: number) {
  return `第 ${index + 1} 章`;
}

function buildReaderChapterContentView(content: string, chapterTitle: string): ReaderChapterContentView {
  const normalizedContent = content || "";
  const normalizedTitle = chapterTitle.trim();

  if (!normalizedContent || !normalizedTitle) {
    return {
      body: normalizedContent,
      trimmedPrefixLength: 0,
    };
  }

  let cursor = 0;
  while (cursor < normalizedContent.length && isReaderChapterWhitespace(normalizedContent[cursor])) {
    cursor += 1;
  }

  if (!normalizedContent.startsWith(normalizedTitle, cursor)) {
    return {
      body: normalizedContent,
      trimmedPrefixLength: 0,
    };
  }

  const bodyOffset = cursor + normalizedTitle.length;
  if (bodyOffset < normalizedContent.length && !isReaderChapterWhitespace(normalizedContent[bodyOffset])) {
    return {
      body: normalizedContent,
      trimmedPrefixLength: 0,
    };
  }

  let bodyStart = bodyOffset;
  while (bodyStart < normalizedContent.length && isReaderChapterWhitespace(normalizedContent[bodyStart])) {
    bodyStart += 1;
  }

  return {
    body: normalizedContent.slice(bodyStart),
    trimmedPrefixLength: bodyStart,
  };
}

function buildReaderParagraphs(content: string) {
  if (!content) {
    return [];
  }

  const paragraphs = content
    .replace(/\r\n?/g, "\n")
    .split(/\n+/)
    .map((paragraph) => paragraph.replace(/^[\s\u3000]+/u, "").trim())
    .filter((paragraph) => paragraph.length > 0);

  return paragraphs.length > 0 ? paragraphs : [content.trim()];
}

function buildReaderContentBlocks(content: string): ReaderContentBlock[] {
  if (!content) {
    return [];
  }

  const blocks: ReaderContentBlock[] = [];
  let segmentStart = 0;

  for (const match of content.matchAll(READER_IMAGE_TAG_PATTERN)) {
    const imageTag = match[0];
    const imageIndex = match.index ?? -1;

    if (imageIndex < 0) {
      continue;
    }

    appendReaderParagraphBlocks(blocks, content.slice(segmentStart, imageIndex));

    const imageBlock = buildReaderImageBlock(imageTag);
    if (imageBlock) {
      blocks.push(imageBlock);
    } else {
      appendReaderParagraphBlocks(blocks, imageTag);
    }

    segmentStart = imageIndex + imageTag.length;
  }

  appendReaderParagraphBlocks(blocks, content.slice(segmentStart));
  return blocks;
}

function appendReaderParagraphBlocks(blocks: ReaderContentBlock[], content: string) {
  for (const paragraph of buildReaderParagraphs(content)) {
    blocks.push({
      type: "paragraph",
      content: paragraph,
    });
  }
}

function buildReaderImageBlock(tag: string): ReaderImageBlock | null {
  const rawSrc = extractReaderHtmlAttribute(tag, "src")?.trim() || "";
  if (!rawSrc) {
    return null;
  }

  return {
    type: "image",
    src: resolveApiAssetUrl(rawSrc) ?? rawSrc,
    alt: extractReaderHtmlAttribute(tag, "alt")?.trim() || "",
  };
}

function extractReaderHtmlAttribute(tag: string, attributeName: string) {
  const attributePattern = new RegExp(
    `${attributeName}\\s*=\\s*(?:"([^"]*)"|'([^']*)'|([^\\s>]+))`,
    "iu",
  );
  const match = attributePattern.exec(tag);

  return match?.[1] ?? match?.[2] ?? match?.[3] ?? null;
}

function isReaderChapterWhitespace(character: string) {
  return /\s/.test(character) || character === "\uFEFF";
}

function syncViewportState() {
  if (typeof window === "undefined") {
    return;
  }

  viewportWidth.value = window.innerWidth;

  if (!isCompactViewport.value) {
    mobileChromeVisible.value = true;
    return;
  }

  if (!activeDrawer.value) {
    mobileChromeVisible.value = false;
  }
}

function handleCatalogScroll(event: Event) {
  const target = event.target as HTMLElement;
  catalogScrollTop.value = target.scrollTop;
  catalogListHeight.value = target.clientHeight;
}

function handleWindowResize() {
  syncViewportState();
}

function openDrawer(view: ReaderDrawerView) {
  activeDrawer.value = view;
  mobileChromeVisible.value = true;

  if (view === "catalog") {
    // 在下个 tick 主动测量目录列表高度，帮助虚拟列表第一次就正确计算窗口
    void nextTick().then(() => {
      const catalogList = catalogListRef.value;
      if (catalogList && catalogListHeight.value <= 0) {
        catalogListHeight.value = catalogList.clientHeight;
      }
    });
  }
}

function setCatalogItemRef(chapterIndex: number, element: Element | ComponentPublicInstance | null) {
  const resolvedElement = element instanceof HTMLElement
    ? element
    : element && "$el" in element && element.$el instanceof HTMLElement
      ? element.$el
      : null;

  if (resolvedElement) {
    catalogItemRefs.set(chapterIndex, resolvedElement);
    return;
  }

  catalogItemRefs.delete(chapterIndex);
}

function waitForNextPaint() {
  if (typeof window === "undefined") {
    return Promise.resolve();
  }

  return new Promise<void>((resolve) => {
    window.requestAnimationFrame(() => resolve());
  });
}

async function scheduleCatalogAutoScroll() {
  const taskToken = ++catalogScrollToken;

  // 等抽屉动画完成（CSS transition 280ms）
  await new Promise((resolve) => setTimeout(resolve, 350));
  await nextTick();
  await waitForNextPaint();

  if (taskToken !== catalogScrollToken || activeDrawer.value !== "catalog") {
    return;
  }

  await scrollCatalogToCurrentChapter();
}

async function scrollCatalogToCurrentChapter() {
  const catalogList = catalogListRef.value;
  if (!catalogList) {
    return;
  }

  const targetIndex = currentChapterIndex.value;
  const targetTop = targetIndex * CATALOG_ITEM_ESTIMATED_HEIGHT;

  // 获取列表可视高度：优先用实际测量值，兜底用估计值
  let listHeight = catalogList.clientHeight;
  if (!listHeight) {
    const drawerPanel = catalogList.closest(".reader-drawer__panel") as HTMLElement | null;
    if (drawerPanel) {
      listHeight = Math.max(0, drawerPanel.clientHeight - 240);
    }
  }
  listHeight = listHeight || catalogListHeight.value || 400;

  const desiredScrollTop = Math.max(
    0,
    targetTop - listHeight / 2 + CATALOG_ITEM_ESTIMATED_HEIGHT / 2,
  );

  // 第一步：直接设置 scrollTop，触发虚拟列表渲染正确窗口
  // 不依赖 catalogItemRefs，因为第一次打开时 ref callback 可能还没执行完
  catalogList.scrollTop = desiredScrollTop;

  // 第二步：等待 DOM 稳定 + Vue ref callback 填充 catalogItemRefs
  await nextTick();
  await waitForNextPaint();
  await new Promise((resolve) => setTimeout(resolve, 80));

  let element = catalogItemRefs.get(targetIndex);
  if (element) {
    element.scrollIntoView({ block: "center", inline: "nearest", behavior: "auto" });
    return;
  }

  // 第三步：如果还没找到，再等待并重试（虚拟列表可能刚完成重渲染）
  await new Promise((resolve) => setTimeout(resolve, 120));
  element = catalogItemRefs.get(targetIndex);
  if (element) {
    element.scrollIntoView({ block: "center", inline: "nearest", behavior: "auto" });
    return;
  }

  // 第四步：最终兜底——直接 scrollTop 微调，确保目标章节在可视区域内
  catalogList.scrollTop = Math.max(0, targetTop - listHeight / 3);
}

function handleReadingSurfaceTap() {
  if (!isCompactViewport.value || activeDrawer.value) {
    return;
  }

  mobileChromeVisible.value = !mobileChromeVisible.value;
}

function toProgressSnapshot(source: Pick<ReadingProgress, "chapter_index" | "char_offset" | "percent" | "updated_at">): ProgressSnapshot {
  return {
    chapter_index: source.chapter_index,
    char_offset: source.char_offset,
    percent: source.percent,
    updated_at: source.updated_at,
  };
}

function getProgressKey(snapshot: Pick<ProgressSnapshot, "chapter_index" | "char_offset">) {
  return `${props.bookId}:${snapshot.chapter_index}:${snapshot.char_offset}`;
}

function buildProgressSnapshotForPosition(
  chapterIndex: number,
  charOffset: number,
  chapterLength = currentChapter.value?.content.length || 0,
): ProgressSnapshot {
  const normalizedChapterIndex = normalizeChapterIndex(chapterIndex);
  const normalizedCharOffset = chapterLength > 0 ? clamp(charOffset, 0, chapterLength) : 0;
  const chapterRatio = chapterLength > 0 ? normalizedCharOffset / chapterLength : 0;
  const percent = chapters.value.length > 0
    ? roundPercent(((normalizedChapterIndex + chapterRatio) / chapters.value.length) * 100)
    : 0;

  return {
    chapter_index: normalizedChapterIndex,
    char_offset: normalizedCharOffset,
    percent,
    updated_at: new Date().toISOString(),
  };
}

function clearScheduledProgressSync() {
  if (!progressSaveTimer) {
    return;
  }

  clearTimeout(progressSaveTimer);
  progressSaveTimer = null;
}

function scheduleProgressSync() {
  if (typeof window === "undefined" || !currentChapter.value) {
    return;
  }

  if (syncState.value !== "syncing") {
    syncState.value = "pending";
  }

  if (progressSaveTimer) {
    return;
  }

  progressSaveTimer = window.setTimeout(() => {
    progressSaveTimer = null;
    void flushProgress("throttled");
  }, PROGRESS_THROTTLE_MS);
}

function getViewportCharOffset() {
  if (typeof window === "undefined" || !contentRef.value || !currentChapter.value) {
    return 0;
  }

  const chapterLength = currentChapter.value.content.length;
  if (chapterLength <= 0) {
    return 0;
  }

  const renderedLength = currentChapterBody.value.length;
  if (renderedLength <= 0) {
    return clamp(currentChapterTrimmedPrefixLength.value, 0, chapterLength);
  }

  const rect = contentRef.value.getBoundingClientRect();
  const elementTop = rect.top + window.scrollY;
  const scrollableHeight = Math.max(contentRef.value.scrollHeight - window.innerHeight * 0.58, 1);
  const focusY = window.scrollY + Math.min(window.innerHeight * 0.32, 220);
  const ratio = clamp((focusY - elementTop) / scrollableHeight, 0, 1);
  const renderedOffset = Math.round(renderedLength * ratio);

  return clamp(currentChapterTrimmedPrefixLength.value + renderedOffset, 0, chapterLength);
}

function captureCurrentProgressSnapshot() {
  if (!currentChapter.value) {
    return null;
  }

  return buildProgressSnapshotForPosition(
    currentChapterIndex.value,
    getViewportCharOffset(),
    currentChapter.value.content.length,
  );
}

function syncSessionProgressFromViewport() {
  const snapshot = captureCurrentProgressSnapshot();
  if (!snapshot) {
    return;
  }

  hasMeaningfulReadingActivity.value = true;
  sessionProgress.value = snapshot;
  saveProgressToLocal(props.bookId, snapshot);
  scheduleProgressSync();
}

async function restoreScrollForCharOffset(charOffset: number, smoothScroll = false) {
  // 多轮重试，确保 DOM 和字体渲染完成后再计算 scroll 位置
  let attempts = 0;
  const maxAttempts = 5;

  while (attempts < maxAttempts) {
    await nextTick();

    if (!contentRef.value) {
      await new Promise((resolve) => requestAnimationFrame(resolve));
      attempts++;
      continue;
    }

    if (typeof window === "undefined" || !currentChapter.value) {
      return;
    }

    const renderedLength = currentChapterBody.value.length;
    if (renderedLength <= 0) {
      await new Promise((resolve) => setTimeout(resolve, 50));
      attempts++;
      continue;
    }

    const adjustedCharOffset = clamp(
      charOffset - currentChapterTrimmedPrefixLength.value,
      0,
      renderedLength,
    );
    const ratio = clamp(adjustedCharOffset / renderedLength, 0, 1);
    const rect = contentRef.value.getBoundingClientRect();
    const elementTop = rect.top + window.scrollY;
    const scrollableHeight = Math.max(
      contentRef.value.scrollHeight - window.innerHeight * 0.58,
      0,
    );
    const targetTop = Math.max(0, elementTop - READER_SCROLL_ANCHOR + scrollableHeight * ratio);

    suppressScrollTrackingUntil = Date.now() + (smoothScroll ? 900 : 420);
    window.scrollTo({
      top: targetTop,
      behavior: smoothScroll ? "smooth" : "auto",
    });
    return;
  }
}

async function loadProgressSafely(bookId: number) {
  try {
    return await booksApi.getProgress(bookId);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }

    throw error;
  }
}

async function loadBookDetailSafely(bookId: number) {
  try {
    return await booksApi.detail(bookId);
  } catch {
    return null;
  }
}

async function loadReader() {
  loading.value = true;
  pageError.value = null;
  chapterError.value = null;
  activeDrawer.value = null;
  mobileChromeVisible.value = !isCompactViewport.value;
  bookTitle.value = "";
  sessionProgress.value = null;
  hasMeaningfulReadingActivity.value = false;
  syncState.value = "idle";
  clearScheduledProgressSync();

  try {
    // 优先从缓存读取章节列表，避免网络慢时重复等待
    const cachedChapters = booksCacheStore.getChapters(props.bookId);
    const cachedBookDetail = booksCacheStore.getBookDetail(props.bookId);

    const bookDetailPromise = loadBookDetailSafely(props.bookId);
    const progressPromise = loadProgressSafely(props.bookId);
    const chaptersPromise = cachedChapters
      ? Promise.resolve(cachedChapters)
      : booksApi.chapters(props.bookId);

    const [bookDetail, chapterList, latestProgress] = await Promise.all([
      bookDetailPromise,
      chaptersPromise,
      progressPromise,
    ]);

    bookTitle.value = bookDetail?.title || cachedBookDetail?.title || "";
    chapters.value = chapterList;

    // 合并后端进度和本地备份
    const localProgress = loadProgressFromLocal(props.bookId);

    // 智能选择最优进度：
    // 1. 如果 URL 带 chapterIndex（从书架/详情页跳转过来），优先信任后端进度，
    //    因为后端是持久化源，localStorage 可能因竞态或 contentRef 不可用时保存了 0
    // 2. 如果是直接打开阅读页（无 chapterIndex），优先用 localStorage（最新设备状态）
    const routeState = getRouteChapterState();
    const shouldUseRouteChapter = routeState.provided && routeState.valid;

    let mergedProgress: ProgressSnapshot | null = null;
    if (shouldUseRouteChapter && latestProgress) {
      // 从书架/详情页跳转：后端优先，但 local 若更新则兜底
      const serverSnapshot = toProgressSnapshot(latestProgress);
      if (localProgress && localProgress.chapter_index === serverSnapshot.chapter_index) {
        // 同一章节：如果 local 的 char_offset 为 0 但 server 有值，说明 local 可能是在
        // 导航瞬间 contentRef 不可用时保存的，此时应信任 server
        mergedProgress =
          localProgress.char_offset === 0 && serverSnapshot.char_offset > 0
            ? serverSnapshot
            : localProgress;
      } else {
        mergedProgress = serverSnapshot;
      }
    } else {
      mergedProgress = localProgress || (latestProgress ? toProgressSnapshot(latestProgress) : null);
    }

    progress.value = mergedProgress;
    lastSavedProgressKey = mergedProgress ? getProgressKey(mergedProgress) : "";

    // 如果使用了缓存，后台静默刷新最新数据
    if (cachedChapters) {
      void booksApi.chapters(props.bookId).then((fresh) => {
        chapters.value = fresh;
        booksCacheStore.set(props.bookId, { chapters: fresh });
      }).catch(() => {
        // 静默失败，保持缓存数据
      });
    }

    if (chapterList.length === 0) {
      currentChapter.value = null;
      currentChapterIndex.value = 0;
      return;
    }

    const requestedIndex = shouldUseRouteChapter
      ? routeState.value
      : mergedProgress?.chapter_index ?? 0;
    const normalizedIndex = normalizeChapterIndex(requestedIndex);
    const restoreCharOffset = shouldUseRouteChapter
      ? (mergedProgress?.chapter_index === routeState.value ? mergedProgress.char_offset : 0)
      : mergedProgress?.chapter_index === normalizedIndex
        ? mergedProgress.char_offset
        : 0;
    const shouldSyncRoute = routeState.provided
      ? !routeState.valid || normalizedIndex !== routeState.value
      : normalizedIndex !== 0;

    // 先结束页面 loading，让 DOM 渲染出来，再恢复滚动位置
    loading.value = false;

    await openChapter(normalizedIndex, {
      syncRoute: shouldSyncRoute,
      replace: true,
      smoothScroll: false,
      restoreCharOffset,
    });
  } catch (error) {
    bookTitle.value = "";
    chapters.value = [];
    progress.value = null;
    sessionProgress.value = null;
    currentChapter.value = null;
    pageError.value = getErrorMessage(error);
  } finally {
    if (loading.value) {
      loading.value = false;
    }
  }
}

async function flushProgress(
  _reason: string,
  options: {
    snapshot?: ProgressSnapshot | null;
    keepalive?: boolean;
    force?: boolean;
  } = {},
) {
  const snapshot = options.snapshot ?? sessionProgress.value ?? captureCurrentProgressSnapshot();
  if (!snapshot) {
    return;
  }

  sessionProgress.value = snapshot;
  const snapshotKey = getProgressKey(snapshot);

  if (!options.force && snapshotKey === lastSavedProgressKey) {
    if (syncState.value !== "error") {
      syncState.value = "idle";
    }
    return;
  }

  clearScheduledProgressSync();

  if (options.keepalive) {
    attemptKeepaliveProgressSave(snapshot);
    return;
  }

  if (saveInFlight) {
    queuedSnapshot = snapshot;
    return;
  }

  saveInFlight = true;
  syncState.value = "syncing";

  try {
    const saved = await booksApi.saveProgress(props.bookId, snapshot);
    progress.value = saved;
    sessionProgress.value = toProgressSnapshot(saved);
    lastSavedProgressKey = getProgressKey(saved);
    syncState.value = "idle";
    clearProgressLocal(props.bookId);
  } catch {
    syncState.value = "error";
  } finally {
    saveInFlight = false;

    if (queuedSnapshot) {
      const nextSnapshot = queuedSnapshot;
      queuedSnapshot = null;

      if (getProgressKey(nextSnapshot) !== lastSavedProgressKey) {
        void flushProgress("queued", {
          snapshot: nextSnapshot,
          force: true,
        });
      }
    }
  }
}

function attemptKeepaliveProgressSave(snapshot: ProgressSnapshot) {
  if (typeof window === "undefined") {
    return;
  }

  const snapshotKey = getProgressKey(snapshot);
  if (snapshotKey === lastSavedProgressKey) {
    return;
  }

  const token = authTokenStorage.get();
  const headers = new Headers({
    "Content-Type": "application/json",
  });

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  void fetch(buildApiUrl(`/api/books/${props.bookId}/progress`), {
    method: "PUT",
    headers,
    body: JSON.stringify(snapshot),
    keepalive: true,
  });
}

async function openChapter(
  chapterIndex: number,
  options: {
    syncRoute?: boolean;
    replace?: boolean;
    smoothScroll?: boolean;
    restoreCharOffset?: number;
    saveAfterOpen?: boolean;
  } = {},
) {
  if (chapters.value.length === 0) {
    return;
  }

  const normalizedIndex = normalizeChapterIndex(chapterIndex);
  chapterLoading.value = true;
  chapterError.value = null;

  try {
    const content = await booksApi.chapterContent(props.bookId, normalizedIndex);
    const restoreCharOffset = clamp(
      options.restoreCharOffset ?? 0,
      0,
      content.content.length,
    );

    currentChapter.value = content;
    currentChapterIndex.value = normalizedIndex;
    sessionProgress.value = buildProgressSnapshotForPosition(
      normalizedIndex,
      restoreCharOffset,
      content.content.length,
    );

    if (options.syncRoute) {
      await router[options.replace ? "replace" : "push"]({
        name: "reader",
        params: {
          bookId: props.bookId,
          chapterIndex: normalizedIndex,
        },
      });
    }

    await restoreScrollForCharOffset(restoreCharOffset, !!options.smoothScroll);

    if (options.saveAfterOpen && sessionProgress.value) {
      hasMeaningfulReadingActivity.value = true;
      await flushProgress("chapter-change", {
        snapshot: sessionProgress.value,
        force: true,
      });
    }
  } catch (error) {
    const message = getErrorMessage(error);

    if (!currentChapter.value) {
      pageError.value = message;
    } else {
      chapterError.value = message;
    }
  } finally {
    chapterLoading.value = false;
  }
}

function handleWindowScroll() {
  if (
    typeof window === "undefined" ||
    loading.value ||
    chapterLoading.value ||
    !currentChapter.value ||
    Date.now() < suppressScrollTrackingUntil
  ) {
    return;
  }

  syncSessionProgressFromViewport();

  if (isCompactViewport.value && mobileChromeVisible.value && !activeDrawer.value) {
    mobileChromeVisible.value = false;
  }
}

function handlePageHide() {
  void preferencesStore.flushPendingPatch();

  if (!hasMeaningfulReadingActivity.value) {
    return;
  }

  void flushProgress("pagehide", {
    keepalive: true,
    force: true,
  });
}

function handleBeforeUnload() {
  const snapshot = captureCurrentProgressSnapshot();
  if (snapshot) {
    saveProgressToLocal(props.bookId, snapshot);
    attemptKeepaliveProgressSave(snapshot);
  }
}

function handleVisibilityChange() {
  if (document.visibilityState !== "hidden") {
    return;
  }

  if (!hasMeaningfulReadingActivity.value) {
    return;
  }

  // 不覆盖 localStorage，避免与 saveSnapshotBeforeNavigate 竞态
  // keepalive flushProgress 成功后会自动 clearProgressLocal
  void flushProgress("visibilitychange", {
    keepalive: true,
    force: true,
  });
}

function handleChapterSelect(chapterIndex: number) {
  activeDrawer.value = null;

  if (isCompactViewport.value) {
    mobileChromeVisible.value = false;
  }

  void openChapter(chapterIndex, {
    syncRoute: true,
    smoothScroll: false,
    restoreCharOffset: 0,
    saveAfterOpen: true,
  });
}

function handlePrevChapter() {
  if (!canGoPrev.value) {
    return;
  }

  handleChapterSelect(currentChapterIndex.value - 1);
}

function handleNextChapter() {
  if (!canGoNext.value) {
    return;
  }

  handleChapterSelect(currentChapterIndex.value + 1);
}

function saveSnapshotBeforeNavigate(reason: string) {
  // 强制同步最新视口进度，确保 snapshot 不是旧的
  syncSessionProgressFromViewport();
  let snapshot = sessionProgress.value ?? captureCurrentProgressSnapshot();

  // 防御性处理：如果当前 snapshot 的 char_offset 为 0，但 sessionProgress 之前记录过
  // 非零值，说明可能是 contentRef 不可用或视口计算异常导致的，应保留历史最大值
  if (
    snapshot &&
    snapshot.char_offset === 0 &&
    sessionProgress.value &&
    sessionProgress.value.char_offset > 0 &&
    snapshot.chapter_index === sessionProgress.value.chapter_index
  ) {
    snapshot = sessionProgress.value;
  }

  if (snapshot) {
    saveProgressToLocal(props.bookId, snapshot);
    void flushProgress(reason, { snapshot, force: true, keepalive: true });
  }
}

function goBack() {
  saveSnapshotBeforeNavigate("navigate-back");
  void router.push({
    name: "book-detail",
    params: { bookId: props.bookId },
  });
}

function goToBookshelf() {
  saveSnapshotBeforeNavigate("navigate-bookshelf");
  void router.push({ name: "books" });
}
</script>

<style scoped>
.reader-page {
  --reader-font-size: 19px;
  --reader-line-height: 1.95;
   --reader-letter-spacing: 0px;
   --reader-paragraph-spacing: 1;
   --reader-content-width: 72ch;
  --reader-column-max: 960px;
  --reader-side-width: 192px;
  --reader-side-gap: clamp(18px, 2vw, 24px);
  --reader-page-gutter: clamp(18px, 2.2vw, 30px);
  --reader-column-width: min(
    var(--reader-column-max),
    calc(
      100vw - (var(--reader-page-gutter) * 2) - (var(--reader-side-width) * 2) - (var(--reader-side-gap) * 2)
    )
  );
  min-height: 100dvh;
  padding: var(--reader-page-gutter);
  /* 二次元阅读页背景：淡蓝粉光晕叠加 */
  background:
    radial-gradient(circle at 14% 10%, rgba(74, 159, 217, 0.14), transparent 22%),
    radial-gradient(circle at 86% 16%, rgba(244, 164, 180, 0.12), transparent 24%),
    radial-gradient(circle at 50% 100%, rgba(255, 255, 255, 0.2), transparent 32%),
    var(--reader-page-bg);
  color: var(--reader-body);
}

.reader-page--light {
  color-scheme: light;
  /* 二次元蓝粉配色：天空蓝到樱花粉渐变背景 */
  --reader-page-bg: linear-gradient(180deg, #D6ECFA 0%, #F0DEE8 100%);
  --reader-panel-bg: rgba(255, 255, 255, 0.74);
  --reader-panel-border: rgba(74, 159, 217, 0.18);
  --reader-panel-shadow: 0 24px 60px rgba(74, 159, 217, 0.12);
  --reader-paper-bg:
    linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(232, 244, 252, 0.92)),
    linear-gradient(135deg, rgba(255, 255, 255, 0.3), rgba(255, 255, 255, 0));
  --reader-paper-border: rgba(74, 159, 217, 0.14);
  --reader-paper-shadow: 0 30px 80px rgba(74, 159, 217, 0.12);
  --reader-heading: #2D3A4A;
  --reader-body: #3D4A5A;
  --reader-muted: #7A8A9A;
  --reader-accent: #F4A4B4;
  --reader-progress-rail: rgba(74, 159, 217, 0.2);
  --reader-action-bg: rgba(255, 255, 255, 0.58);
  --reader-action-hover: rgba(255, 255, 255, 0.86);
  --reader-settings-bg: rgba(232, 244, 252, 0.56);
  --reader-settings-border: rgba(74, 159, 217, 0.12);
}

.reader-page--dark {
  color-scheme: dark;
  /* 纯色背景兜底，彻底消除渐变 banding 和跨设备渲染差异 */
  background-color: #141426;
  background: var(--reader-page-bg);
  /* 深夜花町配色：深蓝紫纯色背景，避免渐变带来的边缘渲染差异 */
  --reader-page-bg: #1A1A2E;
  --reader-panel-bg: rgba(37, 37, 64, 0.94);
  /* 夜间模式下边框改为透明，彻底杜绝白线/粉线 */
  --reader-panel-border: transparent;
  --reader-panel-shadow: 0 24px 64px rgba(0, 0, 0, 0.38);
  --reader-paper-bg: #1E1E32;
  --reader-paper-border: transparent;
  --reader-paper-shadow: 0 34px 88px rgba(0, 0, 0, 0.42);
  --reader-heading: #FFF0F3;
  --reader-body: #D8D8E8;
  --reader-muted: #A0A0C0;
  --reader-accent: #FF8FAB;
  --reader-progress-rail: rgba(255, 255, 255, 0.12);
  --reader-action-bg: rgba(255, 255, 255, 0.04);
  --reader-action-hover: rgba(255, 255, 255, 0.08);
  --reader-settings-bg: rgba(255, 143, 171, 0.04);
  --reader-settings-border: transparent;
}

.reader-page--dark .reader-progress-bar {
  background: rgba(255, 255, 255, 0.12);
}

.reader-page--dark .reader-progress-bar__fill {
  background: #ffffff;
}

.reader-page--dark .reader-glass {
  backdrop-filter: none;
}

.reader-shell {
  position: relative;
}

.reader-loading {
  display: grid;
  grid-template-columns: var(--reader-side-width) minmax(0, var(--reader-column-width)) var(--reader-side-width);
  justify-content: center;
  gap: var(--reader-side-gap);
  align-items: start;
}

.reader-loading__main {
  display: grid;
  gap: 20px;
}

.reader-loading__panel,
.reader-loading__paper {
  padding: 20px;
}

.reader-glass {
  border: 1px solid var(--reader-panel-border);
  border-radius: 28px;
  background: var(--reader-panel-bg);
  box-shadow: var(--reader-panel-shadow);
  backdrop-filter: blur(18px);
  /* 消除 WebKit border-radius 抗锯齿亮边 */
  -webkit-mask-image: -webkit-radial-gradient(white, black);
}

.reader-paper {
  position: relative;
  overflow: hidden;
  width: min(100%, var(--reader-column-width));
  max-width: var(--reader-column-width);
  margin: 0 auto;
  padding: clamp(28px, 4vw, 54px);
  border: 1px solid var(--reader-paper-border);
  border-radius: 34px;
  background: var(--reader-paper-bg);
  background-clip: padding-box;
  box-shadow: var(--reader-paper-shadow);
  /* 强制 GPU 层，消除移动端 border-radius 边缘抗锯齿产生的亮线 */
  transform: translateZ(0);
  -webkit-transform: translateZ(0);
}

/* 只在日间模式下显示纸张顶部高光，避免夜间模式白线 */
.reader-page--light .reader-paper::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.12), transparent 18%),
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.12), transparent 28%);
  pointer-events: none;
  /* 确保伪元素也应用 GPU 层，避免合成差异 */
  transform: translateZ(0);
}

.reader-page__alert {
  margin-bottom: 22px;
  border-radius: 18px;
}

.reader-rail,
.reader-float {
  position: fixed;
  top: 50%;
  z-index: 24;
  transform: translateY(-50%);
}

.reader-rail {
  left: calc(50% - (var(--reader-column-width) / 2) - var(--reader-side-width) - var(--reader-side-gap));
  width: var(--reader-side-width);
}

.reader-float {
  left: calc(50% + (var(--reader-column-width) / 2) + var(--reader-side-gap));
  width: var(--reader-side-width);
}

.reader-rail__panel,
.reader-float__panel {
  width: 100%;
  max-height: calc(100dvh - 48px);
  padding: 16px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-x: hidden;
  overflow-y: auto;
}

.reader-rail__panel,
.reader-rail__brand,
.reader-rail__actions,
.reader-rail__action,
.reader-float__panel,
.reader-float__actions {
  min-width: 0;
}

.reader-rail__brand {
  display: grid;
  gap: 6px;
}

.reader-eyebrow {
  display: inline-flex;
  width: fit-content;
  max-width: 100%;
  padding: 6px 12px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--reader-accent) 16%, transparent);
  color: var(--reader-accent);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.reader-rail__chapter {
  color: var(--reader-heading);
  font-size: 16px;
  line-height: 1.5;
}

.reader-rail__sync {
  color: var(--reader-muted);
  font-size: 12px;
}

.reader-rail__actions,
.reader-float__actions {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.reader-rail__action {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  padding: 12px 14px;
  border: 1px solid transparent;
  border-radius: 18px;
  background: var(--reader-action-bg);
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition:
    transform 180ms ease,
    background 180ms ease,
    border-color 180ms ease;
}

.reader-rail__action:hover {
  transform: translateY(-1px);
  background: var(--reader-action-hover);
  border-color: color-mix(in srgb, var(--reader-accent) 22%, transparent);
}

.reader-rail__action strong,
.reader-rail__action span {
  width: 100%;
  max-width: 100%;
  overflow-wrap: anywhere;
}

.reader-rail__action strong {
  color: var(--reader-heading);
  font-size: 15px;
}

.reader-rail__action span {
  color: var(--reader-muted);
  font-size: 12px;
  line-height: 1.5;
}

.reader-stage {
  width: 100%;
  min-width: 0;
  display: grid;
  gap: 24px;
}

.reader-stage__hero {
  width: min(100%, var(--reader-column-width));
  max-width: var(--reader-column-width);
  margin: 0 auto;
  display: grid;
  gap: 14px;
  padding-top: 20px;
}

.reader-stage__header {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: end;
}

.reader-stage__chapter {
  margin: 0;
  color: var(--reader-muted);
  font-size: 14px;
}

.reader-stage__book {
  margin: 0 0 8px;
  color: var(--reader-muted);
  font-size: 13px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.reader-stage__title {
  margin: 10px 0 0;
  color: var(--reader-heading);
  font-family: var(--font-display);
  font-size: clamp(34px, 5vw, 62px);
  line-height: 1.02;
}

.reader-stage__stat {
  min-width: 160px;
  display: grid;
  gap: 4px;
  justify-items: end;
}

.reader-stage__stat span,
.reader-stage__stat small,
.reader-drawer__summary p,
.reader-float__summary {
  color: var(--reader-muted);
}

.reader-stage__stat strong {
  color: var(--reader-heading);
  font-size: clamp(28px, 4vw, 40px);
  line-height: 1;
}

.reader-drawer__summary {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: baseline;
}

.reader-drawer__summary span,
.reader-float__stat span {
  color: var(--reader-muted);
  font-size: 13px;
}

.reader-drawer__summary strong,
.reader-float__stat strong {
  color: var(--reader-heading);
  font-size: 28px;
  line-height: 1;
}

.reader-content {
  position: relative;
  width: min(100%, var(--reader-content-width));
  max-width: 100%;
  margin: 0 auto;
  color: var(--reader-body);
  font-size: var(--reader-font-size);
  line-height: var(--reader-line-height);
  letter-spacing: var(--reader-letter-spacing);
  word-break: break-word;
  transition: opacity 180ms ease;
}

.reader-content__paragraph {
  margin: 0;
  text-indent: 2em;
  white-space: pre-wrap;
  word-break: break-word;
}

.reader-content__paragraph + .reader-content__paragraph {
  margin-top: calc(var(--reader-font-size) * var(--reader-line-height) * var(--reader-paragraph-spacing));
}

.reader-content__paragraph + .reader-content__image-block,
.reader-content__image-block + .reader-content__paragraph,
.reader-content__image-block + .reader-content__image-block {
  margin-top: calc(var(--reader-font-size) * var(--reader-line-height) * var(--reader-paragraph-spacing));
}

.reader-content__image-block {
  margin: 0;
}

.reader-content__image {
  display: block;
  width: auto;
  max-width: 100%;
  max-height: min(72dvh, 960px);
  margin: 0 auto;
  border-radius: 22px;
  object-fit: contain;
  box-shadow: 0 20px 48px rgba(0, 0, 0, 0.18);
}

.reader-content--dimmed {
  opacity: 0.56;
}

.reader-content--loading {
  display: grid;
  gap: 12px;
}

.reader-paper__chapter-nav {
  margin-top: 28px;
  padding-top: 18px;
  border-top: 1px solid color-mix(in srgb, var(--reader-paper-border) 88%, transparent);
}

.reader-paper__chapter-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.reader-float__panel {
  gap: 16px;
}

.reader-float__stat {
  display: grid;
  gap: 6px;
}

.reader-float__summary {
  display: grid;
  gap: 4px;
  font-size: 13px;
  line-height: 1.7;
}

.reader-drawer__summary {
  display: grid;
  gap: 8px;
}

.reader-drawer__surface {
  color: var(--reader-body);
  background: var(--reader-panel-bg);
  padding: 20px;
  min-height: 100%;
  box-sizing: border-box;
}

.reader-drawer__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 18px;
}

.reader-drawer__title {
  color: var(--reader-heading);
  font-size: 18px;
  font-weight: 600;
}

.reader-drawer__close {
  display: inline-flex;
  padding: 4px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--reader-muted);
  cursor: pointer;
  transition: background 180ms ease, color 180ms ease;
}

.reader-drawer__close:hover {
  background: var(--reader-action-bg);
  color: var(--reader-heading);
}

.reader-drawer__progress {
  margin-top: 18px;
}

.reader-catalog__list {
  display: grid;
  gap: 10px;
  min-height: 0;
  overflow-y: auto;
  padding-right: 4px;
}

.reader-catalog__list--drawer {
  max-height: calc(100dvh - 240px);
  margin-top: 18px;
}

.reader-catalog__list {
  scrollbar-width: thin;
}

.reader-page--light .reader-catalog__list {
  scrollbar-color: rgba(74, 159, 217, 0.5) transparent;
}

.reader-page--dark .reader-catalog__list {
  scrollbar-color: rgba(255, 255, 255, 0.35) transparent;
}

.reader-catalog__list::-webkit-scrollbar {
  width: 6px;
}

.reader-catalog__list::-webkit-scrollbar-track {
  background: transparent;
}

.reader-page--light .reader-catalog__list::-webkit-scrollbar-thumb {
  background: rgba(74, 159, 217, 0.5);
  border-radius: 999px;
}

.reader-page--light .reader-catalog__list::-webkit-scrollbar-thumb:hover {
  background: rgba(74, 159, 217, 0.7);
}

.reader-page--dark .reader-catalog__list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.35);
  border-radius: 999px;
}

.reader-page--dark .reader-catalog__list::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.55);
}

.reader-catalog__item {
  display: grid;
  gap: 6px;
  padding: 14px 16px;
  border: 1px solid var(--reader-panel-border);
  border-radius: 18px;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition:
    transform 180ms ease,
    border-color 180ms ease,
    background 180ms ease;
}

.reader-catalog__item:hover {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--reader-accent) 24%, transparent);
  background: color-mix(in srgb, var(--reader-accent) 8%, transparent);
}

.reader-catalog__item--active {
  border-color: color-mix(in srgb, var(--reader-accent) 28%, transparent);
  background: color-mix(in srgb, var(--reader-accent) 12%, transparent);
}

.reader-catalog__index {
  color: var(--reader-muted);
  font-size: 12px;
}

.reader-catalog__title {
  color: var(--reader-heading);
  line-height: 1.6;
}

.reader-settings {
  display: grid;
  gap: 16px;
}

.reader-settings__group {
  display: grid;
  gap: 14px;
  padding: 18px;
  border: 1px solid var(--reader-panel-border);
  border-radius: 22px;
  background: transparent;
}

.reader-settings__label-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: baseline;
}

.reader-settings__theme-mode {
  color: var(--reader-muted);
  font-size: 13px;
}

.reader-settings__label-row span {
  color: var(--reader-muted);
  font-size: 13px;
}

.reader-settings__label-row strong {
  color: var(--reader-heading);
  font-size: 16px;
}

@media (max-width: 1320px) {
  .reader-page {
    --reader-side-width: 184px;
    --reader-side-gap: 18px;
  }
}

@media (max-width: 1120px) {
  .reader-page {
    --reader-side-width: 168px;
  }

  .reader-rail__panel,
  .reader-float__panel {
    padding: 14px;
  }

  .reader-rail__action {
    padding: 11px 12px;
  }
}

@media (max-width: 980px) {
  .reader-page {
    --reader-column-width: 100%;
    padding: 0;
  }

  .reader-shell,
  .reader-loading {
    grid-template-columns: 1fr;
    gap: 0;
  }

  .reader-loading__panel--rail,
  .reader-loading__panel--float {
    display: none;
  }

  .reader-loading__main {
    padding: 18px;
  }

  .reader-stage {
    min-height: 100dvh;
    gap: 18px;
  }

  .reader-stage__hero,
  .reader-paper {
    width: auto;
    max-width: none;
  }

  .reader-stage__hero {
    padding: 26px 18px 0;
  }

  .reader-stage__header {
    flex-direction: column;
    align-items: stretch;
  }

  .reader-stage__stat {
    display: none;
  }

  .reader-paper {
    margin: 0 10px;
    padding: 26px 20px 30px;
    border-radius: 30px;
  }

  .reader-float {
    display: none;
  }

  .reader-rail {
    position: fixed;
    top: 14px;
    left: 14px;
    z-index: 30;
    width: min(260px, calc(100vw - 28px));
    opacity: 0;
    pointer-events: none;
    transform: translateY(-10px);
    transition:
      opacity 180ms ease,
      transform 180ms ease;
  }

  .reader-rail--active {
    opacity: 1;
    pointer-events: auto;
    transform: translateY(0);
  }
}

@media (max-width: 720px) {
  .reader-stage__title {
    font-size: clamp(30px, 8vw, 42px);
  }

  .reader-content {
    width: var(--reader-content-width-mobile);
  }

  .reader-drawer__summary {
    display: grid;
    gap: 8px;
  }
}

.reader-drawer {
  position: fixed;
  inset: 0;
  z-index: 100;
}

.reader-drawer__backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
}

.reader-drawer__panel {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  overflow-y: auto;
  background: var(--reader-panel-bg);
}

.reader-drawer-enter-active,
.reader-drawer-leave-active {
  transition: opacity 280ms ease;
}

.reader-drawer-enter-from,
.reader-drawer-leave-to {
  opacity: 0;
}

.reader-drawer-enter-active .reader-drawer__panel,
.reader-drawer-leave-active .reader-drawer__panel {
  transition: transform 280ms ease;
}

.reader-drawer-enter-from .reader-drawer__panel,
.reader-drawer-leave-to .reader-drawer__panel {
  transform: translateX(-100%);
}

.reader-progress-bar {
  width: 100%;
  height: 6px;
  border-radius: 999px;
  background: var(--reader-progress-rail);
  overflow: hidden;
}

.reader-progress-bar__fill {
  height: 100%;
  border-radius: 999px;
  background: var(--reader-accent);
  transition: width 300ms ease;
}

.reader-radio {
  display: inline-flex;
  align-items: center;
  padding: 8px 14px;
  border: 1px solid var(--reader-panel-border);
  border-radius: 14px;
  background: var(--reader-action-bg);
  color: var(--reader-muted);
  font-size: 13px;
  cursor: pointer;
  transition: all 180ms ease;
}

.reader-radio:hover {
  background: var(--reader-action-hover);
}

.reader-radio--active {
  border-color: color-mix(in srgb, var(--reader-accent) 40%, transparent);
  background: color-mix(in srgb, var(--reader-accent) 14%, transparent);
  color: var(--reader-accent);
  font-weight: 600;
}

.reader-radio input {
  position: absolute;
  opacity: 0;
}

</style>
