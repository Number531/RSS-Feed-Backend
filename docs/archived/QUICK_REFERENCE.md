# ⚡ Quick Reference - Votes & Comments API

## 🚀 Quick Start

### Start Server
```bash
cd /Users/ej/Downloads/RSS-Feed/backend
uvicorn app.main:app --reload
```

**Server URL**: http://localhost:8000  
**API Docs**: http://localhost:8000/docs

---

## 📍 API Endpoints

### **Votes** (`/api/v1/votes`)

#### Cast/Update Vote
```bash
POST /api/v1/votes/
Headers: Authorization: Bearer {token}
Body: {"article_id": "uuid", "vote_value": 1}  # 1=upvote, -1=downvote
```

#### Get User Vote
```bash
GET /api/v1/votes/article/{article_id}
Headers: Authorization: Bearer {token}
```

#### Remove Vote
```bash
DELETE /api/v1/votes/{article_id}
Headers: Authorization: Bearer {token}
```

---

### **Comments** (`/api/v1/comments`)

#### Create Comment/Reply
```bash
POST /api/v1/comments/
Headers: Authorization: Bearer {token}
Body: {
  "article_id": "uuid",
  "content": "Your comment",
  "parent_comment_id": "uuid"  # Optional, for replies
}
```

#### Get Article Comments
```bash
GET /api/v1/comments/article/{article_id}?page=1&page_size=50
```

#### Get Comment Tree
```bash
GET /api/v1/comments/article/{article_id}/tree?max_depth=10
```

#### Update Comment
```bash
PUT /api/v1/comments/{comment_id}
Headers: Authorization: Bearer {token}
Body: {"content": "Updated content"}
```

#### Delete Comment
```bash
DELETE /api/v1/comments/{comment_id}
Headers: Authorization: Bearer {token}
```

---

## 🔐 Authentication

### Login
```bash
POST /api/v1/auth/login
Body: {"email": "user@example.com", "password": "password"}
Response: {"access_token": "...", "user_id": "..."}
```

Use token in headers: `Authorization: Bearer {access_token}`

---

## 📊 Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (Success) |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |

---

## 🧪 Testing

### Run Manual Tests
```bash
./test_endpoints_complete.sh
```

### Run Pytest
```bash
pytest tests/integration/test_votes.py -v
pytest tests/integration/test_comments.py -v
```

---

## 📁 Key Files

```
app/api/
├── dependencies.py           # DI container
└── v1/endpoints/
    ├── votes.py             # Vote endpoints
    └── comments.py          # Comment endpoints

tests/
├── conftest.py              # Test fixtures
└── integration/
    ├── test_votes.py        # Vote tests
    └── test_comments.py     # Comment tests
```

---

## 🎯 Quick Examples

### Vote on Article
```bash
# Get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Cast upvote
curl -X POST http://localhost:8000/api/v1/votes/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"article_id":"YOUR_ARTICLE_ID","vote_value":1}'
```

### Create Comment
```bash
curl -X POST http://localhost:8000/api/v1/comments/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"article_id":"YOUR_ARTICLE_ID","content":"Great article!"}'
```

---

## ✅ Status Checklist

- [x] Server running
- [x] All endpoints working
- [x] Tests passing
- [x] Documentation complete
- [x] Ready for production

**Status**: ✅ READY TO USE

---

**Last Updated**: 2025-10-10  
**Version**: 1.0.0
