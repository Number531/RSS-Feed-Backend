# TypeScript Types & Interfaces

> **Complete TypeScript definitions for RSS Feed Backend API**  
> Copy these into your frontend project for type safety

---

## 📦 Installation & Setup

### Option 1: Copy to your project
```typescript
// Copy this file to: src/types/api.ts
```

### Option 2: Generate from OpenAPI (recommended)
```bash
npm install -D openapi-typescript
npx openapi-typescript http://localhost:8000/openapi.json -o src/types/api.ts
```

---

## 🔐 Authentication Types

```typescript
// ============================================================================
// Authentication
// ============================================================================

export interface UserRegister {
  email: string;
  username: string;
  password: string;
  full_name?: string;
  avatar_url?: string;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in: number; // seconds
}

export interface TokenRefresh {
  refresh_token: string;
}
```

---

## 👤 User Types

```typescript
// ============================================================================
// User Management
// ============================================================================

export interface User {
  id: string; // UUID
  email: string;
  username: string;
  full_name: string | null;
  avatar_url: string | null;
  is_active: boolean;
  is_verified: boolean;
  oauth_provider: string | null;
  created_at: string; // ISO 8601
  last_login_at: string | null; // ISO 8601
}

export interface UserUpdate {
  email?: string;
  username?: string;
  full_name?: string;
  avatar_url?: string;
  password?: string;
}

export interface UserStats {
  total_votes_cast: number;
  total_comments_made: number;
  account_age_days: number;
  karma_score: number;
}
```

---

## 📰 Article Types

```typescript
// ============================================================================
// Articles
// ============================================================================

export interface Article {
  id: string; // UUID
  rss_source_id: string; // UUID
  title: string;
  url: string;
  description: string | null;
  author: string | null;
  thumbnail_url: string | null;
  category: ArticleCategory;
  published_date: string; // ISO 8601
  created_at: string; // ISO 8601
  vote_score: number;
  vote_count: number;
  comment_count: number;
  tags: string[];
  user_vote?: VoteValue | null; // Only present if authenticated
}

export type ArticleCategory = 'general' | 'politics' | 'us' | 'world' | 'science';

export type SortBy = 'hot' | 'new' | 'top';

export type TimeRange = 'hour' | 'day' | 'week' | 'month' | 'year' | 'all';

export interface ArticlesFeedParams {
  category?: ArticleCategory;
  sort_by?: SortBy;
  time_range?: TimeRange;
  page?: number;
  page_size?: number;
}

export interface ArticlesFeedResponse {
  articles: Article[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ArticleSearchParams {
  q: string; // 1-200 characters
  page?: number;
  page_size?: number;
}

export interface ArticleSearchResponse {
  articles: Article[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_prev: boolean;
}
```

---

## ⬆️⬇️ Vote Types

```typescript
// ============================================================================
// Votes
// ============================================================================

export type VoteValue = 1 | -1 | 0; // upvote | downvote | remove

export interface VoteCreate {
  article_id: string; // UUID
  vote_value: VoteValue;
}

export interface Vote {
  id: string; // UUID
  user_id: string; // UUID
  article_id: string; // UUID
  vote_value: VoteValue;
  created_at: string; // ISO 8601
  updated_at: string; // ISO 8601
}
```

---

## 💬 Comment Types

```typescript
// ============================================================================
// Comments
// ============================================================================

export interface Comment {
  id: string; // UUID
  article_id: string; // UUID
  user_id: string; // UUID
  parent_comment_id: string | null; // UUID
  content: string;
  vote_score: number;
  vote_count: number;
  is_deleted: boolean;
  created_at: string; // ISO 8601
  updated_at: string; // ISO 8601
}

export interface CommentTree extends Comment {
  replies: CommentTree[];
}

export interface CommentCreate {
  article_id: string; // UUID
  content: string; // 1-10,000 characters
  parent_comment_id?: string; // UUID, optional for replies
}

export interface CommentUpdate {
  content: string; // 1-10,000 characters
}

export type CommentVoteType = 'upvote' | 'downvote';

export interface CommentVoteResponse {
  voted: boolean;
  vote_type: CommentVoteType | null;
  vote_score: number;
  vote_count: number;
}

export interface CommentVoteStatus {
  voted: boolean;
  vote_type: CommentVoteType | null;
  vote_value: VoteValue;
}

export interface CommentVoteSummary {
  comment_id: string; // UUID
  vote_score: number;
  vote_count: number;
}
```

---

## 🔖 Bookmark Types

```typescript
// ============================================================================
// Bookmarks
// ============================================================================

export interface Bookmark {
  id: string; // UUID
  user_id: string; // UUID
  article_id: string; // UUID
  collection: string;
  notes: string | null;
  created_at: string; // ISO 8601
  updated_at: string; // ISO 8601
}

export interface BookmarkCreate {
  article_id: string; // UUID
  collection?: string;
  notes?: string;
}

export interface BookmarkUpdate {
  collection?: string;
  notes?: string;
}

export interface BookmarkListResponse {
  items: Bookmark[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface BookmarkCollectionsResponse {
  collections: string[];
  total: number;
}

export interface BookmarkStatusResponse {
  article_id: string; // UUID
  is_bookmarked: boolean;
}
```

---

## 📖 Reading History Types

```typescript
// ============================================================================
// Reading History
// ============================================================================

export interface ReadingHistory {
  id: string; // UUID
  user_id: string; // UUID
  article_id: string; // UUID
  viewed_at: string; // ISO 8601
  duration_seconds: number | null;
  scroll_percentage: number | null; // 0-100
}

export interface ReadingHistoryWithArticle extends ReadingHistory {
  article: {
    id: string; // UUID
    title: string;
    url: string;
    thumbnail_url: string | null;
  };
}

export interface ReadingHistoryCreate {
  article_id: string; // UUID
  duration_seconds?: number;
  scroll_percentage?: number; // 0-100
}

export interface ReadingHistoryListResponse {
  items: ReadingHistoryWithArticle[];
  total: number;
  skip: number;
  limit: number;
}

export interface ReadingStats {
  total_articles_read: number;
  total_reading_time_seconds: number;
  average_reading_time_seconds: number;
  average_scroll_percentage: number;
  articles_read_today: number;
  articles_read_this_week: number;
  articles_read_this_month: number;
  most_read_category: ArticleCategory | null;
  reading_streak_days: number;
}

export interface ClearHistoryRequest {
  before_date?: string; // ISO 8601
}

export interface ClearHistoryResponse {
  deleted_count: number;
  message: string;
}

export interface ReadingPreferences {
  id: string; // UUID
  user_id: string; // UUID
  track_reading_history: boolean;
  track_reading_time: boolean;
  track_scroll_depth: boolean;
  created_at: string; // ISO 8601
  updated_at: string; // ISO 8601
}

export interface ReadingPreferencesUpdate {
  track_reading_history?: boolean;
  track_reading_time?: boolean;
  track_scroll_depth?: boolean;
}
```

---

## 🔔 Notification Types

```typescript
// ============================================================================
// Notifications
// ============================================================================

export type NotificationType = 'vote' | 'reply' | 'mention';

export type RelatedEntityType = 'article' | 'comment';

export interface Notification {
  id: string; // UUID
  user_id: string; // UUID
  type: NotificationType;
  title: string;
  message: string;
  related_entity_type: RelatedEntityType;
  related_entity_id: string; // UUID
  actor_id: string | null; // UUID
  actor_username: string | null;
  is_read: boolean;
  read_at: string | null; // ISO 8601
  created_at: string; // ISO 8601
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  unread_count: number;
  page: number;
  page_size: number;
}

export interface NotificationStats {
  total_count: number;
  unread_count: number;
  vote_count: number;
  reply_count: number;
  mention_count: number;
}

export interface NotificationUnreadCount {
  unread_count: number;
}

export interface NotificationMarkRead {
  notification_ids: string[]; // UUIDs
}

export interface NotificationMarkReadResponse {
  marked_count: number;
  message: string;
}

export interface NotificationPreferences {
  id: string; // UUID
  user_id: string; // UUID
  vote_notifications: boolean;
  reply_notifications: boolean;
  mention_notifications: boolean;
  email_notifications: boolean;
  created_at: string; // ISO 8601
  updated_at: string; // ISO 8601
}

export interface NotificationPreferencesUpdate {
  vote_notifications?: boolean;
  reply_notifications?: boolean;
  mention_notifications?: boolean;
  email_notifications?: boolean;
}
```

---

## 🚨 Error Types

```typescript
// ============================================================================
// Error Handling
// ============================================================================

export interface ApiError {
  detail: string;
}

export interface ValidationError {
  detail: Array<{
    loc: (string | number)[];
    msg: string;
    type: string;
  }>;
}

export type HttpStatus =
  | 200 // OK
  | 201 // Created
  | 204 // No Content
  | 400 // Bad Request
  | 401 // Unauthorized
  | 403 // Forbidden
  | 404 // Not Found
  | 409 // Conflict
  | 422 // Unprocessable Entity
  | 429 // Too Many Requests
  | 500 // Internal Server Error
  | 501; // Not Implemented
```

---

## 🔄 Pagination Types

```typescript
// ============================================================================
// Common Patterns
// ============================================================================

export interface PaginationParams {
  page?: number; // 1-indexed
  page_size?: number; // 1-100
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface SkipLimitParams {
  skip?: number;
  limit?: number;
}

export interface SkipLimitResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}
```

---

## 🔧 API Client Types

```typescript
// ============================================================================
// API Client Configuration
// ============================================================================

export interface ApiConfig {
  baseUrl: string;
  timeout?: number;
  headers?: Record<string, string>;
}

export interface ApiClientOptions {
  accessToken?: string;
  refreshToken?: string;
  onTokenRefresh?: (tokens: TokenResponse) => void;
  onAuthError?: () => void;
}

export interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
  requiresAuth?: boolean;
}
```

---

## 🎯 Usage Examples

### Type-Safe API Client

```typescript
// src/api/client.ts
import type {
  Article,
  ArticlesFeedParams,
  ArticlesFeedResponse,
  User,
  TokenResponse,
} from './types/api';

class ApiClient {
  private baseUrl: string;
  private accessToken?: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  setAccessToken(token: string) {
    this.accessToken = token;
  }

  private async request<T>(
    endpoint: string,
    options?: RequestOptions
  ): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options?.headers,
    };

    if (this.accessToken && options?.requiresAuth !== false) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail);
    }

    return response.json();
  }

  // Auth endpoints
  async login(credentials: UserLogin): Promise<TokenResponse> {
    return this.request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
      requiresAuth: false,
    });
  }

  // User endpoints
  async getCurrentUser(): Promise<User> {
    return this.request<User>('/users/me');
  }

  // Article endpoints
  async getArticlesFeed(
    params?: ArticlesFeedParams
  ): Promise<ArticlesFeedResponse> {
    const queryString = new URLSearchParams(
      params as Record<string, string>
    ).toString();
    return this.request<ArticlesFeedResponse>(
      `/articles?${queryString}`,
      { requiresAuth: false }
    );
  }

  async getArticle(articleId: string): Promise<Article> {
    return this.request<Article>(`/articles/${articleId}`, {
      requiresAuth: false,
    });
  }
}

export const apiClient = new ApiClient('/api/v1');
```

### React Hook Example

```typescript
// src/hooks/useArticles.ts
import { useState, useEffect } from 'react';
import type { Article, ArticlesFeedParams } from '../types/api';
import { apiClient } from '../api/client';

export function useArticles(params?: ArticlesFeedParams) {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchArticles = async () => {
      try {
        setLoading(true);
        const response = await apiClient.getArticlesFeed(params);
        setArticles(response.articles);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchArticles();
  }, [params]);

  return { articles, loading, error };
}
```

### Zod Schema Validation (Optional)

```typescript
// src/schemas/api.ts
import { z } from 'zod';

export const UserSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  username: z.string().min(3).max(50),
  full_name: z.string().nullable(),
  avatar_url: z.string().url().nullable(),
  is_active: z.boolean(),
  is_verified: z.boolean(),
  oauth_provider: z.string().nullable(),
  created_at: z.string().datetime(),
  last_login_at: z.string().datetime().nullable(),
});

export const ArticleSchema = z.object({
  id: z.string().uuid(),
  rss_source_id: z.string().uuid(),
  title: z.string(),
  url: z.string().url(),
  description: z.string().nullable(),
  author: z.string().nullable(),
  thumbnail_url: z.string().url().nullable(),
  category: z.enum(['general', 'politics', 'us', 'world', 'science']),
  published_date: z.string().datetime(),
  created_at: z.string().datetime(),
  vote_score: z.number(),
  vote_count: z.number(),
  comment_count: z.number(),
  tags: z.array(z.string()),
  user_vote: z.union([z.literal(1), z.literal(-1), z.null()]).optional(),
});

// Use for runtime validation
export type ValidatedUser = z.infer<typeof UserSchema>;
export type ValidatedArticle = z.infer<typeof ArticleSchema>;
```

---

## 📝 Type Guards

```typescript
// src/utils/typeGuards.ts

export function isApiError(error: unknown): error is ApiError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'detail' in error &&
    typeof (error as ApiError).detail === 'string'
  );
}

export function isValidationError(error: unknown): error is ValidationError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'detail' in error &&
    Array.isArray((error as ValidationError).detail)
  );
}

export function isArticleCategory(value: string): value is ArticleCategory {
  return ['general', 'politics', 'us', 'world', 'science'].includes(value);
}

export function isVoteValue(value: number): value is VoteValue {
  return [1, -1, 0].includes(value);
}
```

---

## 🎨 Frontend State Management

### Redux Toolkit Example

```typescript
// src/store/slices/articlesSlice.ts
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { Article, ArticlesFeedParams } from '../../types/api';
import { apiClient } from '../../api/client';

interface ArticlesState {
  items: Article[];
  loading: boolean;
  error: string | null;
  page: number;
  hasMore: boolean;
}

const initialState: ArticlesState = {
  items: [],
  loading: false,
  error: null,
  page: 1,
  hasMore: true,
};

export const fetchArticles = createAsyncThunk(
  'articles/fetchArticles',
  async (params: ArticlesFeedParams) => {
    const response = await apiClient.getArticlesFeed(params);
    return response;
  }
);

const articlesSlice = createSlice({
  name: 'articles',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchArticles.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchArticles.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload.articles;
        state.page = action.payload.page;
        state.hasMore = action.payload.has_next;
      })
      .addCase(fetchArticles.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch articles';
      });
  },
});

export default articlesSlice.reducer;
```

---

## 📦 Export All Types

```typescript
// src/types/api.ts - Main export file
export * from './auth';
export * from './user';
export * from './article';
export * from './vote';
export * from './comment';
export * from './bookmark';
export * from './reading-history';
export * from './notification';
export * from './common';
export * from './error';
```

---

**Version:** 1.0  
**Last Updated:** 2025-01-27  
**TypeScript Version:** 5.0+
