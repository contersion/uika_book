<template>
  <div class="book-detail-page">
    <section class="book-detail-page__topbar">
      <n-button tertiary @click="goBack">返回书架</n-button>
      <span class="book-detail-page__crumb">Book ID: {{ bookId }}</span>
    </section>

    <section v-if="loading" class="book-detail-page__loading">
      <n-card :bordered="false" class="book-detail-page__loading-card">
        <n-skeleton text :repeat="4" />
        <n-skeleton style="margin-top: 18px;" text :repeat="3" />
      </n-card>
      <n-card :bordered="false" class="book-detail-page__loading-card">
        <n-skeleton text :repeat="8" />
      </n-card>
    </section>

    <page-status-panel
      v-else-if="pageError"
      variant="error"
      title="书籍详情暂时无法加载"
      :description="pageError"
    >
      <template #action>
        <n-button type="primary" @click="reloadPage">重新加载</n-button>
      </template>
    </page-status-panel>

    <template v-else-if="book">
      <section class="detail-hero">
        <div class="detail-hero__cover">
          <div class="detail-hero__cover-badge">TXT</div>
          <div class="detail-hero__cover-letter">{{ getCoverLetter(book.title) }}</div>
        </div>

        <div class="detail-hero__body">
          <div class="detail-hero__eyebrow">Book Detail</div>
          <h1 class="detail-hero__title">{{ book.title }}</h1>
          <p class="detail-hero__author">{{ book.author || "作者未填写" }}</p>
          <p class="detail-hero__description">
            {{ book.description || "这本书还没有补充描述，当前可直接查看目录、继续阅读或切换目录规则后重新解析。" }}
          </p>

          <div class="detail-hero__tags">
            <n-tag round :bordered="false">总章节 {{ formatNumber(book.total_chapters) }}</n-tag>
            <n-tag round :bordered="false">总字数 {{ formatWordCount(book.total_words) }}</n-tag>
            <n-tag round :bordered="false">当前规则 {{ currentRuleName }}</n-tag>
            <n-tag round :bordered="false">{{ progressTagLabel }}</n-tag>
          </div>

          <div class="detail-hero__actions">
            <n-button type="primary" size="large" :loading="readingPending" @click="handleReadAction">
              {{ readActionLabel }}
            </n-button>
            <n-button secondary size="large" @click="goToChapter(0)">
              从第一章开始
            </n-button>
          </div>
        </div>
      </section>

      <section class="detail-grid">
        <n-card :bordered="false" class="detail-card">
          <template #header>
            <span class="detail-card__heading">文件信息</span>
          </template>

          <div class="detail-info-grid">
            <div class="detail-info-item">
              <span>文件名</span>
              <strong>{{ book.file_name }}</strong>
            </div>
            <div class="detail-info-item">
              <span>编码</span>
              <strong>{{ book.encoding }}</strong>
            </div>
            <div class="detail-info-item">
              <span>创建时间</span>
              <strong>{{ formatDate(book.created_at) }}</strong>
            </div>
            <div class="detail-info-item">
              <span>更新时间</span>
              <strong>{{ formatDate(book.updated_at) }}</strong>
            </div>
          </div>

          <div class="detail-file-path">
            <span class="detail-file-path__label">本地文件</span>
            <code>{{ book.file_name }}</code>
          </div>
        </n-card>

        <n-card :bordered="false" class="detail-card">
          <template #header>
            <span class="detail-card__heading">目录规则</span>
          </template>

          <div class="detail-rule-card">
            <div class="detail-rule-card__current">
              <span>当前使用</span>
              <strong>{{ currentRuleName }}</strong>
              <p>{{ currentRuleDescription }}</p>
            </div>

            <n-alert v-if="rulesError" type="warning" :show-icon="false" class="detail-rule-card__alert">
              {{ rulesError }}
            </n-alert>

            <div class="detail-rule-card__actions">
              <n-select
                v-model:value="selectedRuleId"
                :options="ruleOptions"
                :disabled="reparsePending || ruleOptions.length === 0"
                placeholder="选择目录规则"
              />
              <n-button
                secondary
                :loading="reparsePending"
                :disabled="!selectedRuleId"
                @click="handleReparse"
              >
                重新解析目录
              </n-button>
            </div>
          </div>
        </n-card>
      </section>

      <n-card :bordered="false" class="detail-card detail-card--chapters">
        <template #header>
          <span class="detail-card__heading">目录列表</span>
        </template>
        <template #header-extra>
          <span class="detail-card__subheading">共 {{ chapters.length }} 章</span>
        </template>

        <n-empty v-if="chapters.length === 0" description="当前没有可展示的章节目录。" />

        <div v-else class="chapter-list">
          <button
            v-for="chapter in chapters"
            :key="chapter.id"
            type="button"
            class="chapter-list__item"
            @click="goToChapter(chapter.chapter_index)"
          >
            <span class="chapter-list__index">第 {{ chapter.chapter_index + 1 }} 章</span>
            <strong class="chapter-list__title">{{ chapter.chapter_title }}</strong>
            <span class="chapter-list__meta">
              范围 {{ formatNumber(chapter.start_offset) }} - {{ formatNumber(chapter.end_offset) }}
            </span>
          </button>
        </div>
      </n-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import {
  NAlert,
  NButton,
  NCard,
  NEmpty,
  NSelect,
  NSkeleton,
  NTag,
  useMessage,
} from "naive-ui";
import { useRouter } from "vue-router";

import { booksApi } from "../api/books";
import { chapterRulesApi } from "../api/chapter-rules";
import { ApiError, getErrorMessage } from "../api/client";
import type { BookChapter, BookDetail, ChapterRule, ReadingProgress } from "../types/api";
import PageStatusPanel from "../components/PageStatusPanel.vue";
import { formatDateTime, formatNumber, formatWordCount } from "../utils/format";

const props = defineProps<{
  bookId: number;
}>();

const router = useRouter();
const message = useMessage();
const book = ref<BookDetail | null>(null);
const chapters = ref<BookChapter[]>([]);
const rules = ref<ChapterRule[]>([]);
const progress = ref<ReadingProgress | null>(null);
const selectedRuleId = ref<number | null>(null);
const loading = ref(true);
const pageError = ref<string | null>(null);
const rulesError = ref<string | null>(null);
const readingPending = ref(false);
const reparsePending = ref(false);

const ruleOptions = computed(() => {
  return rules.value.map((rule) => ({
    label: rule.is_builtin ? `${rule.rule_name}（内置）` : rule.rule_name,
    value: rule.id,
  }));
});

const currentRuleName = computed(() => {
  if (book.value?.chapter_rule?.rule_name) {
    return book.value.chapter_rule.rule_name;
  }

  const selectedRule = rules.value.find((rule) => rule.id === selectedRuleId.value);
  return selectedRule?.rule_name || "未指定";
});

const currentRuleDescription = computed(() => {
  if (book.value?.chapter_rule?.description) {
    return book.value.chapter_rule.description;
  }

  const selectedRule = rules.value.find((rule) => rule.id === selectedRuleId.value);
  return selectedRule?.description || "你可以在这里切换规则并重新解析目录。";
});

const readActionLabel = computed(() => {
  return progress.value ? "继续阅读" : "开始阅读";
});

const progressTagLabel = computed(() => {
  if (!progress.value) {
    return "尚未开始";
  }

  return `上次读到第 ${progress.value.chapter_index + 1} 章`;
});

function formatDate(value: string) {
  return formatDateTime(value, "时间未知");
}

function getCoverLetter(title: string) {
  const normalized = title.trim();
  return normalized ? normalized.slice(0, 1).toUpperCase() : "T";
}

async function loadBookAndChapters() {
  const [bookDetail, chapterList] = await Promise.all([
    booksApi.detail(props.bookId),
    booksApi.chapters(props.bookId),
  ]);

  book.value = bookDetail;
  chapters.value = chapterList;
  selectedRuleId.value = bookDetail.chapter_rule_id;
}

async function loadRules() {
  rulesError.value = null;

  try {
    rules.value = await chapterRulesApi.list();

    if (!selectedRuleId.value) {
      selectedRuleId.value =
        book.value?.chapter_rule_id ??
        rules.value.find((rule) => rule.is_default)?.id ??
        rules.value[0]?.id ??
        null;
    }
  } catch (error) {
    rules.value = [];
    rulesError.value = getErrorMessage(error);
  }
}

async function loadProgress() {
  try {
    progress.value = await booksApi.getProgress(props.bookId);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      progress.value = null;
      return;
    }

    progress.value = null;
  }
}

async function loadPage() {
  loading.value = true;
  pageError.value = null;

  try {
    await loadBookAndChapters();
    await Promise.all([loadRules(), loadProgress()]);
  } catch (error) {
    book.value = null;
    chapters.value = [];
    progress.value = null;
    pageError.value = getErrorMessage(error);
  } finally {
    loading.value = false;
  }
}

function reloadPage() {
  void loadPage();
}

function goBack() {
  void router.push({ name: "books" });
}

function goToChapter(chapterIndex: number) {
  void router.push({
    name: "reader",
    params: {
      bookId: props.bookId,
      chapterIndex,
    },
  });
}

async function handleReadAction() {
  readingPending.value = true;

  try {
    if (!progress.value) {
      goToChapter(0);
      return;
    }

    goToChapter(progress.value.chapter_index);
  } finally {
    readingPending.value = false;
  }
}

async function handleReparse() {
  if (!selectedRuleId.value) {
    message.warning("请先选择一个目录规则");
    return;
  }

  reparsePending.value = true;

  try {
    await booksApi.reparse(props.bookId, selectedRuleId.value);
    message.success("目录已重新解析");
    await loadBookAndChapters();
  } catch (error) {
    message.error(getErrorMessage(error));
  } finally {
    reparsePending.value = false;
  }
}

watch(
  () => props.bookId,
  () => {
    void loadPage();
  },
  { immediate: true },
);
</script>

<style scoped>
.book-detail-page {
  display: grid;
  gap: 24px;
}

.book-detail-page__topbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.book-detail-page__crumb {
  color: var(--text-secondary);
  font-size: 13px;
}

.book-detail-page__loading,
.book-detail-page__error-state {
  display: grid;
  gap: 18px;
}

.book-detail-page__loading-card {
  min-height: 220px;
}

.detail-hero {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  gap: 24px;
  padding: clamp(24px, 4vw, 32px);
  border-radius: 28px;
  background:
    radial-gradient(circle at top right, rgba(52, 107, 97, 0.18), transparent 26%),
    radial-gradient(circle at bottom left, rgba(184, 93, 54, 0.14), transparent 32%),
    color-mix(in srgb, var(--surface-color) 92%, white 8%);
  box-shadow: var(--surface-shadow);
}

.detail-hero__cover {
  position: relative;
  display: grid;
  place-items: center;
  min-height: 280px;
  border-radius: 24px;
  background:
    linear-gradient(155deg, rgba(184, 93, 54, 0.92), rgba(52, 107, 97, 0.92)),
    linear-gradient(180deg, rgba(255, 255, 255, 0.16), transparent);
  color: white;
  overflow: hidden;
}

.detail-hero__cover::after {
  content: "";
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.14), rgba(255, 255, 255, 0)),
    linear-gradient(0deg, rgba(0, 0, 0, 0.08), rgba(0, 0, 0, 0));
}

.detail-hero__cover-badge {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 1;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.2);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.detail-hero__cover-letter {
  position: relative;
  z-index: 1;
  font-family: var(--font-display);
  font-size: 72px;
  font-weight: 700;
}

.detail-hero__body {
  display: grid;
  gap: 18px;
  align-content: center;
}

.detail-hero__eyebrow {
  display: inline-flex;
  width: fit-content;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(52, 107, 97, 0.12);
  color: var(--accent-color);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.detail-hero__title {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(30px, 4vw, 46px);
  line-height: 1.08;
}

.detail-hero__author {
  margin: 0;
  color: var(--text-secondary);
  font-size: 18px;
}

.detail-hero__description {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.detail-hero__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.detail-hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.detail-card__heading {
  font-weight: 700;
}

.detail-card__subheading {
  color: var(--text-secondary);
  font-size: 13px;
}

.detail-info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.detail-info-item {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.55);
}

.detail-info-item span {
  display: block;
  color: var(--text-secondary);
  font-size: 12px;
}

.detail-info-item strong {
  display: block;
  margin-top: 6px;
  line-height: 1.6;
}

.detail-file-path {
  margin-top: 14px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.55);
}

.detail-file-path__label {
  display: block;
  margin-bottom: 8px;
  color: var(--text-secondary);
  font-size: 12px;
}

.detail-file-path code {
  white-space: pre-wrap;
  word-break: break-all;
  color: var(--text-primary);
}

.detail-rule-card {
  display: grid;
  gap: 16px;
}

.detail-rule-card__current span {
  display: block;
  color: var(--text-secondary);
  font-size: 12px;
}

.detail-rule-card__current strong {
  display: block;
  margin-top: 6px;
  font-size: 18px;
}

.detail-rule-card__current p {
  margin: 10px 0 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.detail-rule-card__alert {
  border-radius: 16px;
}

.detail-rule-card__actions {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
}

.detail-card--chapters :deep(.n-card__content) {
  display: grid;
  gap: 14px;
}

.chapter-list {
  display: grid;
  gap: 10px;
}

.chapter-list__item {
  width: 100%;
  display: grid;
  gap: 6px;
  padding: 16px 18px;
  border: 0;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.58);
  text-align: left;
  cursor: pointer;
  transition:
    transform 160ms ease,
    box-shadow 160ms ease,
    background 160ms ease;
}

.chapter-list__item:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 28px rgba(82, 55, 28, 0.08);
  background: rgba(255, 255, 255, 0.78);
}

.chapter-list__index,
.chapter-list__meta {
  color: var(--text-secondary);
  font-size: 13px;
}

.chapter-list__title {
  font-size: 16px;
  line-height: 1.6;
}

@media (max-width: 960px) {
  .detail-hero,
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .detail-hero__cover {
    min-height: 220px;
  }
}

@media (max-width: 720px) {
  .book-detail-page__topbar,
  .detail-hero__actions,
  .detail-rule-card__actions,
  .detail-info-grid {
    grid-template-columns: 1fr;
    display: grid;
  }
}
</style>
