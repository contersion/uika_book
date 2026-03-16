import { apiClient } from "./client";
import type {
  BookChapter,
  BookChapterContent,
  BookDetail,
  BookGroupAssignmentPayload,
  BookGroupSummary,
  BookMetadataPayload,
  BookReparseResponse,
  BookShelfItem,
  BookSortKey,
  ReadingProgress,
  ReadingProgressPayload,
} from "../types/api";

interface BookListParams {
  search?: string;
  groupId?: number | null;
  sort?: BookSortKey;
}

export const booksApi = {
  list(params: BookListParams = {}) {
    return apiClient.get<BookShelfItem[]>("/api/books", {
      query: {
        search: params.search,
        group_id: params.groupId,
        sort: params.sort,
      },
    });
  },
  detail(bookId: number) {
    return apiClient.get<BookDetail>(`/api/books/${bookId}`);
  },
  updateMetadata(bookId: number, payload: BookMetadataPayload) {
    return apiClient.patch<BookDetail>(`/api/books/${bookId}`, payload);
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
  uploadCover(bookId: number, file: File) {
    const formData = new FormData();
    formData.append("file", file);
    return apiClient.post<BookDetail>(`/api/books/${bookId}/cover`, formData);
  },
  deleteCover(bookId: number) {
    return apiClient.delete<void>(`/api/books/${bookId}/cover`);
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
