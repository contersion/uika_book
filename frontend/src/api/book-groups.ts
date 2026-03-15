import { apiClient } from "./client";
import type { BookGroup, BookGroupPayload } from "../types/api";

export const bookGroupsApi = {
  list() {
    return apiClient.get<BookGroup[]>("/api/book-groups");
  },
  create(payload: BookGroupPayload) {
    return apiClient.post<BookGroup>("/api/book-groups", payload);
  },
  update(groupId: number, payload: BookGroupPayload) {
    return apiClient.put<BookGroup>(`/api/book-groups/${groupId}`, payload);
  },
  remove(groupId: number) {
    return apiClient.delete<void>(`/api/book-groups/${groupId}`);
  },
};
