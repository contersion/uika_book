<template>
  <section class="page-status-panel" :class="`page-status-panel--${variant}`">
    <div class="page-status-panel__badge">{{ badgeLabel }}</div>
    <h2 class="page-status-panel__title">{{ title }}</h2>
    <p class="page-status-panel__description">{{ description }}</p>
    <div v-if="$slots.action" class="page-status-panel__actions">
      <slot name="action" />
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    variant?: "empty" | "error";
    title: string;
    description: string;
  }>(),
  {
    variant: "empty",
  },
);

const badgeLabel = computed(() => {
  return props.variant === "error" ? "Error State" : "Empty State";
});
</script>

<style scoped>
.page-status-panel {
  display: grid;
  justify-items: center;
  gap: 14px;
  padding: clamp(28px, 5vw, 44px);
  border: 1px solid var(--border-color);
  border-radius: 28px;
  text-align: center;
  background: color-mix(in srgb, var(--surface-color) 94%, white 6%);
  box-shadow: var(--surface-shadow);
}

.page-status-panel__badge {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.page-status-panel--empty .page-status-panel__badge {
  background: rgba(244, 164, 180, 0.16);
  color: var(--primary-color);
}

.page-status-panel--error .page-status-panel__badge {
  background: rgba(255, 107, 107, 0.12);
  color: #e05555;
}

.page-status-panel__title {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(26px, 4vw, 34px);
  line-height: 1.15;
}

.page-status-panel__description {
  max-width: 560px;
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.page-status-panel__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
}

@media (max-width: 640px) {
  .page-status-panel__actions {
    width: 100%;
    display: grid;
    grid-template-columns: 1fr;
  }
}
</style>