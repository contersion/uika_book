import { apiClient } from "./client";
import type {
  BookChapter,
  BookChapterContent,
  BookDetail,
  BookGroupAssignmentPayload,
  BookGroupSummary,
  BookReparseResponse,
  BookShelfItem,
  ReadingProgress,
  ReadingProgressPayload,
} from "../types/api";

export const booksApi = {
  list(search?: string) {
    return apiClient.get<BookShelfItem[]>("/api/books", {
      query: { search },
    });
  },
  detail(bookId: number) {
    return apiClient.get<BookDetail>(`/api/books/${bookId}`);
  },
  chapters(bookId: number) {
    return apiClient.get<BookChapter[]>(`/api/books/${bookId}/chapters`);
  },
  chapterContent(bookId: number, chapterIndex: number) {
    return apiClient.get<BookChapterContent>(`/api/books/${bookId}/chapters/${chapterIndex}`);
  },
  getGroups(bookId: number) {
    return apiClient.get<BookGroupSummary[]>(`/api/books/${bookId}/groups`);
  },
  updateGroups(bookId: number, payload: BookGroupAssignmentPayload) {
    return apiClient.put<BookGroupSummary[]>(`/api/books/${bookId}/groups`, payload);
  },
  upload(file: File, chapterRuleId?: number) {
    const formData = new FormData();
    formData.append("file", file);

    if (chapterRuleId) {
      formData.append("chapter_rule_id", String(chapterRuleId));
    }

    return apiClient.post<BookDetail>("/api/books/upload", formData);
  },
  delete(bookId: number) {
    return apiClient.delete<void>(`/api/books/${bookId}`);
  },
  getProgress(bookId: number) {
    return apiClient.get<ReadingProgress>(`/api/books/${bookId}/progress`);
  },
  saveProgress(bookId: number, payload: ReadingProgressPayload) {
    return apiClient.put<ReadingProgress>(`/api/books/${bookId}/progress`, payload);
  },
  reparse(bookId: number, chapterRuleId: number) {
    return apiClient.post<BookReparseResponse>(`/api/books/${bookId}/reparse`, {
      chapter_rule_id: chapterRuleId,
    });
  },
};
