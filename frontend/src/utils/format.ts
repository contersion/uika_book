const numberFormatter = new Intl.NumberFormat("zh-CN");
const dateTimeFormatter = new Intl.DateTimeFormat("zh-CN", {
  dateStyle: "medium",
  timeStyle: "short",
});

export function clampPercentage(value: number | null | undefined) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return 0;
  }

  return Math.max(0, Math.min(100, value));
}

export function formatNumber(value: number | null | undefined) {
  return numberFormatter.format(value || 0);
}

export function formatWordCount(value: number | null | undefined) {
  return `${formatNumber(value)} 字`;
}

export function formatPercent(value: number | null | undefined, maximumFractionDigits = 0) {
  const normalized = clampPercentage(value);
  return `${normalized.toLocaleString("zh-CN", {
    minimumFractionDigits: 0,
    maximumFractionDigits,
  })}%`;
}

export function formatDateTime(value: string | null | undefined, fallback = "时间未知") {
  if (!value) {
    return fallback;
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return fallback;
  }

  return dateTimeFormatter.format(date);
}
