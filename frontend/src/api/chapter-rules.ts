import { apiClient } from "./client";
import type {
  ChapterRule,
  ChapterRulePayload,
  ChapterRuleTestPayload,
  ChapterRuleTestResponse,
} from "../types/api";

export const chapterRulesApi = {
  list() {
    return apiClient.get<ChapterRule[]>("/api/chapter-rules");
  },
  create(payload: ChapterRulePayload) {
    return apiClient.post<ChapterRule>("/api/chapter-rules", payload);
  },
  update(ruleId: number, payload: Partial<ChapterRulePayload> & { is_default?: boolean }) {
    return apiClient.put<ChapterRule>(`/api/chapter-rules/${ruleId}`, payload);
  },
  remove(ruleId: number) {
    return apiClient.delete<void>(`/api/chapter-rules/${ruleId}`);
  },
  test(payload: ChapterRuleTestPayload) {
    return apiClient.post<ChapterRuleTestResponse>("/api/chapter-rules/test", payload);
  },
};
