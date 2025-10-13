# OpenAPI 3.0 Specification

> **RSS Feed Backend API - OpenAPI Specification**  
> Use this specification with tools like Swagger UI, Postman, or code generators

---

## 📋 How to Use This Spec

### Option 1: View in Swagger UI (Interactive)
Your backend already serves this at:
- **Development:** http://localhost:8000/docs
- **Production:** https://your-domain.com/docs

### Option 2: Import to Postman
1. Copy the YAML spec below
2. Open Postman → Import → Paste Raw Text
3. Start testing!

### Option 3: Generate Client Code
```bash
# Generate TypeScript client
npm install -g @openapitools/openapi-generator-cli
openapi-generator-cli generate -i openapi.yaml -g typescript-axios -o src/api

# Generate Python client
openapi-generator-cli generate -i openapi.yaml -g python -o python-client
```

---

## 📄 OpenAPI Specification (YAML)

```yaml
openapi: 3.0.3
info:
  title: RSS Feed Backend API
  description: |
    Complete REST API for RSS Feed aggregation platform with user management,
    articles, voting, comments, bookmarks, and notifications.
    
    ## Features
    - JWT authentication with refresh tokens
    - Reddit-style voting system
    - Threaded comments
    - Bookmark collections
    - Reading history tracking
    - Real-time notifications
    
    ## Authentication
    Most endpoints require JWT authentication. Include the access token in the
    Authorization header:
    ```
    Authorization: Bearer <access_token>
    ```
    
    Tokens expire after 30 minutes. Use the `/auth/refresh` endpoint to obtain
    a new access token using your refresh token.
    
  version: 1.0.0
  contact:
    email: support@yourdomain.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: http://localhost:8000/api/v1
    description: Development server
  - url: https://your-domain.com/api/v1
    description: Production server

tags:
  - name: Authentication
    description: User authentication and token management
  - name: Users
    description: User profile management
  - name: Articles
    description: News articles from RSS feeds
  - name: Votes
    description: Voting on articles
  - name: Comments
    description: Article comments and discussions
  - name: Bookmarks
    description: Save articles for later
  - name: Reading History
    description: Track article views and reading metrics
  - name: Notifications
    description: User notifications and preferences

paths:
  # ============================================================================
  # Authentication Endpoints
  # ============================================================================
  
  /auth/register:
    post:
      tags:
        - Authentication
      summary: Register new user
      description: Create a new user account with email and password
      operationId: registerUser
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserRegister'
            example:
              email: user@example.com
              username: johndoe
              password: SecurePass123!
              full_name: John Doe
              avatar_url: https://example.com/avatar.jpg
      responses:
        '201':
          description: User created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '400':
          $ref: '#/components/responses/BadRequest'
        '422':
          $ref: '#/components/responses/ValidationError'

  /auth/login:
    post:
      tags:
        - Authentication
      summary: Login user
      description: Authenticate user and receive JWT tokens
      operationId: loginUser
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserLogin'
            example:
              email: user@example.com
              password: SecurePass123!
      responses:
        '200':
          description: Login successful
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TokenResponse'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'

  /auth/refresh:
    post:
      tags:
        - Authentication
      summary: Refresh access token
      description: Get new access token using refresh token
      operationId: refreshToken
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TokenRefresh'
      responses:
        '200':
          description: Token refreshed successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TokenResponse'
        '401':
          $ref: '#/components/responses/Unauthorized'

  # ============================================================================
  # User Endpoints
  # ============================================================================
  
  /users/me:
    get:
      tags:
        - Users
      summary: Get current user profile
      description: Get authenticated user's profile information
      operationId: getCurrentUser
      security:
        - BearerAuth: []
      responses:
        '200':
          description: User profile retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '401':
          $ref: '#/components/responses/Unauthorized'
    
    patch:
      tags:
        - Users
      summary: Update user profile
      description: Update current user's profile (all fields optional)
      operationId: updateUser
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserUpdate'
      responses:
        '200':
          description: Profile updated successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '409':
          $ref: '#/components/responses/Conflict'
        '422':
          $ref: '#/components/responses/ValidationError'
    
    delete:
      tags:
        - Users
      summary: Delete user account
      description: Soft delete current user's account
      operationId: deleteUser
      security:
        - BearerAuth: []
      responses:
        '204':
          description: Account deleted successfully
        '401':
          $ref: '#/components/responses/Unauthorized'

  # ============================================================================
  # Article Endpoints
  # ============================================================================
  
  /articles:
    get:
      tags:
        - Articles
      summary: Get articles feed
      description: Get paginated articles with filtering and sorting
      operationId: getArticlesFeed
      security:
        - BearerAuth: []
        - {}
      parameters:
        - name: category
          in: query
          schema:
            $ref: '#/components/schemas/ArticleCategory'
        - name: sort_by
          in: query
          schema:
            $ref: '#/components/schemas/SortBy'
          example: hot
        - name: time_range
          in: query
          schema:
            $ref: '#/components/schemas/TimeRange'
        - $ref: '#/components/parameters/Page'
        - $ref: '#/components/parameters/PageSize'
      responses:
        '200':
          description: Articles retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ArticlesFeedResponse'

  /articles/search:
    get:
      tags:
        - Articles
      summary: Search articles
      description: Full-text search through articles
      operationId: searchArticles
      parameters:
        - name: q
          in: query
          required: true
          schema:
            type: string
            minLength: 1
            maxLength: 200
          description: Search query
        - $ref: '#/components/parameters/Page'
        - $ref: '#/components/parameters/PageSize'
      responses:
        '200':
          description: Search results retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ArticleSearchResponse'

  /articles/{article_id}:
    get:
      tags:
        - Articles
      summary: Get single article
      description: Get detailed information about a specific article
      operationId: getArticle
      security:
        - BearerAuth: []
        - {}
      parameters:
        - $ref: '#/components/parameters/ArticleId'
      responses:
        '200':
          description: Article retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Article'
        '404':
          $ref: '#/components/responses/NotFound'

  # ============================================================================
  # Vote Endpoints
  # ============================================================================
  
  /votes:
    post:
      tags:
        - Votes
      summary: Cast vote on article
      description: Create, update, or remove vote on an article
      operationId: castVote
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/VoteCreate'
      responses:
        '201':
          description: Vote cast successfully
          content:
            application/json:
              schema:
                oneOf:
                  - $ref: '#/components/schemas/Vote'
                  - type: 'null'
        '401':
          $ref: '#/components/responses/Unauthorized'

  /votes/{article_id}:
    delete:
      tags:
        - Votes
      summary: Remove vote from article
      description: Remove user's vote from an article
      operationId: removeVote
      security:
        - BearerAuth: []
      parameters:
        - $ref: '#/components/parameters/ArticleId'
      responses:
        '204':
          description: Vote removed successfully
        '404':
          $ref: '#/components/responses/NotFound'

  /votes/article/{article_id}:
    get:
      tags:
        - Votes
      summary: Get user's vote on article
      description: Get current user's vote on an article
      operationId: getUserVote
      security:
        - BearerAuth: []
      parameters:
        - $ref: '#/components/parameters/ArticleId'
      responses:
        '200':
          description: Vote retrieved successfully
          content:
            application/json:
              schema:
                oneOf:
                  - $ref: '#/components/schemas/Vote'
                  - type: 'null'

  # ============================================================================
  # Comment Endpoints
  # ============================================================================
  
  /comments:
    post:
      tags:
        - Comments
      summary: Create comment
      description: Create new comment or reply to existing comment
      operationId: createComment
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CommentCreate'
      responses:
        '201':
          description: Comment created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Comment'

  /comments/article/{article_id}:
    get:
      tags:
        - Comments
      summary: Get article comments
      description: Get top-level comments for an article (paginated)
      operationId: getArticleComments
      parameters:
        - $ref: '#/components/parameters/ArticleId'
        - $ref: '#/components/parameters/Page'
        - $ref: '#/components/parameters/PageSize'
      responses:
        '200':
          description: Comments retrieved successfully
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Comment'

  /comments/article/{article_id}/tree:
    get:
      tags:
        - Comments
      summary: Get comment tree
      description: Get nested comment tree for an article
      operationId: getCommentTree
      parameters:
        - $ref: '#/components/parameters/ArticleId'
        - name: max_depth
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 20
            default: 10
      responses:
        '200':
          description: Comment tree retrieved successfully
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/CommentTree'

  /comments/{comment_id}:
    get:
      tags:
        - Comments
      summary: Get single comment
      description: Get a specific comment by ID
      operationId: getComment
      parameters:
        - $ref: '#/components/parameters/CommentId'
      responses:
        '200':
          description: Comment retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Comment'
        '404':
          $ref: '#/components/responses/NotFound'
    
    put:
      tags:
        - Comments
      summary: Update comment
      description: Update comment content (author only)
      operationId: updateComment
      security:
        - BearerAuth: []
      parameters:
        - $ref: '#/components/parameters/CommentId'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CommentUpdate'
      responses:
        '200':
          description: Comment updated successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Comment'
        '403':
          $ref: '#/components/responses/Forbidden'
    
    delete:
      tags:
        - Comments
      summary: Delete comment
      description: Soft delete comment (author only)
      operationId: deleteComment
      security:
        - BearerAuth: []
      parameters:
        - $ref: '#/components/parameters/CommentId'
      responses:
        '204':
          description: Comment deleted successfully
        '403':
          $ref: '#/components/responses/Forbidden'

  /comments/{comment_id}/vote:
    post:
      tags:
        - Comments
      summary: Vote on comment
      description: Cast or toggle vote on a comment
      operationId: voteOnComment
      security:
        - BearerAuth: []
      parameters:
        - $ref: '#/components/parameters/CommentId'
        - name: vote_type
          in: query
          required: true
          schema:
            $ref: '#/components/schemas/CommentVoteType'
      responses:
        '200':
          description: Vote cast successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CommentVoteResponse'

  # ============================================================================
  # Bookmark Endpoints
  # ============================================================================
  
  /bookmarks:
    post:
      tags:
        - Bookmarks
      summary: Create bookmark
      description: Save an article for later reading
      operationId: createBookmark
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/BookmarkCreate'
      responses:
        '201':
          description: Bookmark created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Bookmark'
    
    get:
      tags:
        - Bookmarks
      summary: List bookmarks
      description: Get all bookmarks for current user
      operationId: listBookmarks
      security:
        - BearerAuth: []
      parameters:
        - name: collection
          in: query
          schema:
            type: string
        - $ref: '#/components/parameters/Page'
        - $ref: '#/components/parameters/PageSize'
      responses:
        '200':
          description: Bookmarks retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BookmarkListResponse'

  # ============================================================================
  # Reading History Endpoints
  # ============================================================================
  
  /reading-history:
    post:
      tags:
        - Reading History
      summary: Record article view
      description: Track article view with optional engagement metrics
      operationId: recordArticleView
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ReadingHistoryCreate'
      responses:
        '201':
          description: View recorded successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ReadingHistory'

  # ============================================================================
  # Notification Endpoints
  # ============================================================================
  
  /notifications:
    get:
      tags:
        - Notifications
      summary: Get notifications
      description: Get paginated list of notifications
      operationId: getNotifications
      security:
        - BearerAuth: []
      parameters:
        - $ref: '#/components/parameters/Page'
        - $ref: '#/components/parameters/PageSize'
        - name: unread_only
          in: query
          schema:
            type: boolean
            default: false
        - name: notification_type
          in: query
          schema:
            $ref: '#/components/schemas/NotificationType'
      responses:
        '200':
          description: Notifications retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/NotificationListResponse'

  /notifications/unread-count:
    get:
      tags:
        - Notifications
      summary: Get unread count
      description: Get count of unread notifications (lightweight)
      operationId: getUnreadCount
      security:
        - BearerAuth: []
      responses:
        '200':
          description: Count retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/NotificationUnreadCount'

# ============================================================================
# Components (Schemas, Parameters, Responses, Security)
# ============================================================================

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: JWT access token

  parameters:
    Page:
      name: page
      in: query
      schema:
        type: integer
        minimum: 1
        default: 1
      description: Page number (1-indexed)
    
    PageSize:
      name: page_size
      in: query
      schema:
        type: integer
        minimum: 1
        maximum: 100
        default: 25
      description: Items per page
    
    ArticleId:
      name: article_id
      in: path
      required: true
      schema:
        type: string
        format: uuid
      description: Article UUID
    
    CommentId:
      name: comment_id
      in: path
      required: true
      schema:
        type: string
        format: uuid
      description: Comment UUID

  responses:
    BadRequest:
      description: Bad request - invalid input
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ApiError'
    
    Unauthorized:
      description: Unauthorized - invalid or missing token
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ApiError'
    
    Forbidden:
      description: Forbidden - insufficient permissions
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ApiError'
    
    NotFound:
      description: Resource not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ApiError'
    
    Conflict:
      description: Conflict - resource already exists
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ApiError'
    
    ValidationError:
      description: Validation error
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ValidationError'

  schemas:
    # Authentication Schemas
    UserRegister:
      type: object
      required:
        - email
        - username
        - password
      properties:
        email:
          type: string
          format: email
        username:
          type: string
          minLength: 3
          maxLength: 50
        password:
          type: string
          minLength: 8
        full_name:
          type: string
          nullable: true
        avatar_url:
          type: string
          format: uri
          nullable: true

    UserLogin:
      type: object
      required:
        - email
        - password
      properties:
        email:
          type: string
          format: email
        password:
          type: string

    TokenResponse:
      type: object
      properties:
        access_token:
          type: string
        refresh_token:
          type: string
        token_type:
          type: string
          enum: [bearer]
        expires_in:
          type: integer
          description: Token expiry in seconds

    TokenRefresh:
      type: object
      required:
        - refresh_token
      properties:
        refresh_token:
          type: string

    # User Schemas
    User:
      type: object
      properties:
        id:
          type: string
          format: uuid
        email:
          type: string
          format: email
        username:
          type: string
        full_name:
          type: string
          nullable: true
        avatar_url:
          type: string
          format: uri
          nullable: true
        is_active:
          type: boolean
        is_verified:
          type: boolean
        oauth_provider:
          type: string
          nullable: true
        created_at:
          type: string
          format: date-time
        last_login_at:
          type: string
          format: date-time
          nullable: true

    UserUpdate:
      type: object
      properties:
        email:
          type: string
          format: email
        username:
          type: string
          minLength: 3
          maxLength: 50
        full_name:
          type: string
        avatar_url:
          type: string
          format: uri
        password:
          type: string
          minLength: 8

    # Article Schemas
    Article:
      type: object
      properties:
        id:
          type: string
          format: uuid
        rss_source_id:
          type: string
          format: uuid
        title:
          type: string
        url:
          type: string
          format: uri
        description:
          type: string
          nullable: true
        author:
          type: string
          nullable: true
        thumbnail_url:
          type: string
          format: uri
          nullable: true
        category:
          $ref: '#/components/schemas/ArticleCategory'
        published_date:
          type: string
          format: date-time
        created_at:
          type: string
          format: date-time
        vote_score:
          type: integer
        vote_count:
          type: integer
        comment_count:
          type: integer
        tags:
          type: array
          items:
            type: string
        user_vote:
          type: integer
          enum: [1, -1]
          nullable: true

    ArticleCategory:
      type: string
      enum:
        - general
        - politics
        - us
        - world
        - science

    SortBy:
      type: string
      enum:
        - hot
        - new
        - top
      default: hot

    TimeRange:
      type: string
      enum:
        - hour
        - day
        - week
        - month
        - year
        - all

    ArticlesFeedResponse:
      type: object
      properties:
        articles:
          type: array
          items:
            $ref: '#/components/schemas/Article'
        total:
          type: integer
        page:
          type: integer
        page_size:
          type: integer
        has_next:
          type: boolean
        has_prev:
          type: boolean

    ArticleSearchResponse:
      type: object
      properties:
        articles:
          type: array
          items:
            $ref: '#/components/schemas/Article'
        total:
          type: integer
        page:
          type: integer
        page_size:
          type: integer
        has_next:
          type: boolean
        has_prev:
          type: boolean

    # Vote Schemas
    VoteCreate:
      type: object
      required:
        - article_id
        - vote_value
      properties:
        article_id:
          type: string
          format: uuid
        vote_value:
          type: integer
          enum: [1, -1, 0]
          description: 1=upvote, -1=downvote, 0=remove

    Vote:
      type: object
      properties:
        id:
          type: string
          format: uuid
        user_id:
          type: string
          format: uuid
        article_id:
          type: string
          format: uuid
        vote_value:
          type: integer
          enum: [1, -1]
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    # Comment Schemas
    Comment:
      type: object
      properties:
        id:
          type: string
          format: uuid
        article_id:
          type: string
          format: uuid
        user_id:
          type: string
          format: uuid
        parent_comment_id:
          type: string
          format: uuid
          nullable: true
        content:
          type: string
        vote_score:
          type: integer
        vote_count:
          type: integer
        is_deleted:
          type: boolean
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    CommentTree:
      allOf:
        - $ref: '#/components/schemas/Comment'
        - type: object
          properties:
            replies:
              type: array
              items:
                $ref: '#/components/schemas/CommentTree'

    CommentCreate:
      type: object
      required:
        - article_id
        - content
      properties:
        article_id:
          type: string
          format: uuid
        content:
          type: string
          minLength: 1
          maxLength: 10000
        parent_comment_id:
          type: string
          format: uuid
          nullable: true

    CommentUpdate:
      type: object
      required:
        - content
      properties:
        content:
          type: string
          minLength: 1
          maxLength: 10000

    CommentVoteType:
      type: string
      enum:
        - upvote
        - downvote

    CommentVoteResponse:
      type: object
      properties:
        voted:
          type: boolean
        vote_type:
          $ref: '#/components/schemas/CommentVoteType'
          nullable: true
        vote_score:
          type: integer
        vote_count:
          type: integer

    # Bookmark Schemas
    Bookmark:
      type: object
      properties:
        id:
          type: string
          format: uuid
        user_id:
          type: string
          format: uuid
        article_id:
          type: string
          format: uuid
        collection:
          type: string
        notes:
          type: string
          nullable: true
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    BookmarkCreate:
      type: object
      required:
        - article_id
      properties:
        article_id:
          type: string
          format: uuid
        collection:
          type: string
        notes:
          type: string

    BookmarkListResponse:
      type: object
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/Bookmark'
        total:
          type: integer
        page:
          type: integer
        page_size:
          type: integer
        has_more:
          type: boolean

    # Reading History Schemas
    ReadingHistory:
      type: object
      properties:
        id:
          type: string
          format: uuid
        user_id:
          type: string
          format: uuid
        article_id:
          type: string
          format: uuid
        viewed_at:
          type: string
          format: date-time
        duration_seconds:
          type: integer
          nullable: true
        scroll_percentage:
          type: number
          minimum: 0
          maximum: 100
          nullable: true

    ReadingHistoryCreate:
      type: object
      required:
        - article_id
      properties:
        article_id:
          type: string
          format: uuid
        duration_seconds:
          type: integer
        scroll_percentage:
          type: number
          minimum: 0
          maximum: 100

    # Notification Schemas
    Notification:
      type: object
      properties:
        id:
          type: string
          format: uuid
        user_id:
          type: string
          format: uuid
        type:
          $ref: '#/components/schemas/NotificationType'
        title:
          type: string
        message:
          type: string
        related_entity_type:
          type: string
          enum: [article, comment]
        related_entity_id:
          type: string
          format: uuid
        actor_id:
          type: string
          format: uuid
          nullable: true
        actor_username:
          type: string
          nullable: true
        is_read:
          type: boolean
        read_at:
          type: string
          format: date-time
          nullable: true
        created_at:
          type: string
          format: date-time

    NotificationType:
      type: string
      enum:
        - vote
        - reply
        - mention

    NotificationListResponse:
      type: object
      properties:
        notifications:
          type: array
          items:
            $ref: '#/components/schemas/Notification'
        total:
          type: integer
        unread_count:
          type: integer
        page:
          type: integer
        page_size:
          type: integer

    NotificationUnreadCount:
      type: object
      properties:
        unread_count:
          type: integer

    # Error Schemas
    ApiError:
      type: object
      properties:
        detail:
          type: string

    ValidationError:
      type: object
      properties:
        detail:
          type: array
          items:
            type: object
            properties:
              loc:
                type: array
                items:
                  oneOf:
                    - type: string
                    - type: integer
              msg:
                type: string
              type:
                type: string
```

---

## 🔧 Tool Integration Examples

### Swagger UI (Local Testing)
```bash
# Your backend already serves this!
# Just visit: http://localhost:8000/docs
```

### Postman Collection Generation
1. Copy the YAML spec above
2. Save as `openapi.yaml`
3. Postman → Import → Select File → `openapi.yaml`
4. Set environment variable `baseUrl` to `http://localhost:8000/api/v1`

### Generate SDK/Client Library

#### TypeScript/Axios Client
```bash
npm install -g @openapitools/openapi-generator-cli

openapi-generator-cli generate \
  -i openapi.yaml \
  -g typescript-axios \
  -o src/generated-api \
  --additional-properties=npmName=rss-feed-api,supportsES6=true
```

#### Python Client
```bash
openapi-generator-cli generate \
  -i openapi.yaml \
  -g python \
  -o python-client \
  --additional-properties=packageName=rss_feed_api
```

#### React Query Hooks
```bash
npm install -D @rtk-query/codegen-openapi

npx @rtk-query/codegen-openapi \
  openapi.yaml \
  --output src/api/generated.ts
```

### Mock Server (Testing)
```bash
# Install Prism
npm install -g @stoplight/prism-cli

# Run mock server
prism mock openapi.yaml
# Now available at: http://127.0.0.1:4010
```

---

## 📝 Validation Tools

### Validate OpenAPI Spec
```bash
# Using Swagger CLI
npm install -g @apidevtools/swagger-cli
swagger-cli validate openapi.yaml

# Using Spectral (advanced linting)
npm install -g @stoplight/spectral-cli
spectral lint openapi.yaml
```

### Test API Against Spec
```bash
# Using Dredd
npm install -g dredd
dredd openapi.yaml http://localhost:8000
```

---

## 🎨 Documentation Generators

### ReDoc (Beautiful Static Docs)
```bash
npm install -g redoc-cli
redoc-cli bundle openapi.yaml -o api-docs.html
```

### Docusaurus (Full Documentation Site)
```bash
npx create-docusaurus@latest my-api-docs classic
cd my-api-docs
npm install docusaurus-plugin-openapi-docs
# Configure and build
```

---

## 🔍 Additional Resources

- **OpenAPI Specification:** https://spec.openapis.org/oas/v3.0.3
- **Swagger Tools:** https://swagger.io/tools/
- **OpenAPI Generator:** https://openapi-generator.tech/
- **Postman Learning Center:** https://learning.postman.com/

---

**Specification Version:** OpenAPI 3.0.3  
**API Version:** 1.0.0  
**Last Updated:** 2025-01-27
