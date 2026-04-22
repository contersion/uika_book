<template>
  <SelectPortal>
    <SelectContent
      :class="cn(
        'relative z-50 max-h-96 min-w-[8rem] overflow-hidden rounded-md border border-[var(--select-content-border)] bg-[var(--select-content-bg)] text-[var(--select-content-text)] shadow-md data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2',
        $attrs.class ?? ''
      )"
      position="popper"
    >
      <SelectViewport class="h-full w-full p-1">
        <slot />
      </SelectViewport>
    </SelectContent>
  </SelectPortal>
</template>

<script setup lang="ts">
import { SelectContent, SelectPortal, SelectViewport } from "reka-ui";
import { cn } from "@/lib/utils";
</script>
