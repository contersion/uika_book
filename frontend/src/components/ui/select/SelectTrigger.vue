<template>
  <SelectTrigger
    v-bind="$attrs"
    :class="cn(
      'flex h-9 w-full items-center justify-between rounded-md border border-[var(--select-trigger-border)] bg-transparent px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-gray-400 disabled:cursor-not-allowed disabled:opacity-50',
      $attrs.class ?? ''
    )"
  >
    <slot />
    <ChevronDown class="h-4 w-4 opacity-50" />
  </SelectTrigger>
</template>

<script setup lang="ts">
import { SelectTrigger } from "reka-ui";
import { ChevronDown } from "lucide-vue-next";
import { cn } from "@/lib/utils";
</script>
