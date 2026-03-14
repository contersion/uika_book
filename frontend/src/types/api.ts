export interface ApiErrorResponse {
  success: false;
  detail: string;
  error: {
    code: string;
    message: string;
    details: unknown;
  };
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  id: number;
  username: string;
  created_at: string;
}

export interface ChapterRule {
  id: number;
  user_id: number | null;
  rule_name: string;
  regex_pattern: string;
  flags: string;
  description: string | null;
  is_builtin: boolean;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface ChapterRulePayload {
  rule_name: string;
  regex_pattern: string;
  flags: string;
  description: string | null;
  is_default: boolean;
}

export interface ChapterRuleTestPayload {
  book_id?: number;
  text?: string;
  regex_pattern: string;
  flags: string;
}

export interface ChapterRuleTestResponse {
  matched: boolean;
  count: number;
  items: Array<{
    text: string;
    start: number;
    end: number;
  }>;
}

export interface BookShelfItem {
  id: number;
  title: string;
  author: string | null;
  total_chapters: number;
  total_words: number;
  last_read_at: string | null;
  progress_percent: number | null;
  created_at: string;
  updated_at: string;
}

export interface BookDetail {
  id: number;
  user_id: number;
  title: string;
  author: string | null;
  description: string | null;
  encoding: string;
  total_words: number;
  total_chapters: number;
  chapter_rule_id: number | null;
  file_name: string;
  file_path: string;
  created_at: string;
  updated_at: string;
  chapter_rule?: ChapterRule | null;
}

export interface BookChapter {
  id: number;
  book_id: number;
  chapter_index: number;
  chapter_title: string;
  start_offset: number;
  end_offset: number;
  created_at: string;
}

export interface BookChapterContent {
  book_id: number;
  chapter_index: number;
  chapter_title: string;
  start_offset: number;
  end_offset: number;
  content: string;
}

export interface ReadingProgress {
  id: number;
  user_id: number;
  book_id: number;
  chapter_index: number;
  char_offset: number;
  percent: number;
  updated_at: string;
}

export interface ReadingProgressPayload {
  chapter_index: number;
  char_offset: number;
  percent: number;
  updated_at: string;
}

export interface BookReparseResponse {
  book_id: number;
  chapter_rule_id: number;
  total_chapters: number;
  chapters: Array<{
    chapter_index: number;
    chapter_title: string;
    start_offset: number;
    end_offset: number;
  }>;
}
