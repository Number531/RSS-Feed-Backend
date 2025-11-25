# Frontend Email Verification Page Specification

## Overview
The backend email verification system is fully operational and sending verification emails from `welcome@psqrd.ai`. However, users encounter a **404 error** when clicking the verification link because the frontend lacks the `/verify-email` page component.

This document provides complete specifications for the frontend team to implement the email verification page.

---

## 🎯 Required Component

**Path**: `/verify-email`  
**Purpose**: Handle email verification link clicks from user inboxes  
**Current Issue**: Returns 404 - route does not exist

---

## 📧 Email Link Format

Users receive an email with a verification link:
```
http://localhost:3000/verify-email?token=FduAghSQwGsDydLMqgVE0lBTx0Bgnqx80o0Otz84I3s
```

Production URL will be:
```
https://psqrd.ai/verify-email?token=FduAghSQwGsDydLMqgVE0lBTx0Bgnqx80o0Otz84I3s
```

**Token Characteristics**:
- 43 characters long
- URL-safe base64 string
- Expires in 1 hour (stored in Redis with 3600s TTL)
- Single-use (deleted after successful verification)

---

## 🔌 Backend API Endpoint

### Verify Email
**Endpoint**: `POST /api/v1/auth/verify-email`  
**Content-Type**: `application/json`

**Request Body**:
```json
{
  "token": "FduAghSQwGsDydLMqgVE0lBTx0Bgnqx80o0Otz84I3s"
}
```

**Success Response** (200 OK):
```json
{
  "message": "Email verified successfully",
  "status": "success"
}
```

**Already Verified** (200 OK):
```json
{
  "message": "Email already verified",
  "status": "success"
}
```

**Error Responses**:
- **400 Bad Request** - Invalid or expired token
  ```json
  {
    "detail": "Invalid or expired verification token"
  }
  ```
- **404 Not Found** - User not found
  ```json
  {
    "detail": "User not found"
  }
  ```

---

## 🎨 Page Design Requirements

### Page States

#### 1. Loading State
Display while API call is in progress:
```
┌────────────────────────────────┐
│       [Spinner/Loading]        │
│                                │
│   Verifying your email...     │
└────────────────────────────────┘
```

#### 2. Success State
Display after successful verification:
```
┌────────────────────────────────┐
│         [✓ Check Icon]         │
│                                │
│   Email Verified!              │
│                                │
│   Your account is now active.  │
│   You can log in to continue.  │
│                                │
│   [Go to Login →]              │
└────────────────────────────────┘
```

#### 3. Already Verified State
Display if email was already verified:
```
┌────────────────────────────────┐
│         [✓ Check Icon]         │
│                                │
│   Email Already Verified       │
│                                │
│   Your account is active.      │
│                                │
│   [Go to Login →]              │
└────────────────────────────────┘
```

#### 4. Error State
Display for invalid/expired tokens:
```
┌────────────────────────────────┐
│         [✗ Error Icon]         │
│                                │
│   Verification Failed          │
│                                │
│   The verification link is     │
│   invalid or has expired.      │
│                                │
│   [Request New Link →]         │
└────────────────────────────────┘
```

### Design Guidelines
- **Theme**: Match existing PSQRD dark theme
- **Colors**: 
  - Primary: `#648EFC` (blue from email template)
  - Background: `#0E1113` (dark background)
  - Card: `#181C1F` (card background)
- **Typography**: Same fonts as main app
- **Spacing**: Generous padding, centered layout
- **Mobile**: Fully responsive design

---

## 💻 Implementation Example (React/TypeScript)

```typescript
import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

type VerificationStatus = 'loading' | 'success' | 'already-verified' | 'error';

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<VerificationStatus>('loading');
  const [errorMessage, setErrorMessage] = useState<string>('');

  useEffect(() => {
    const token = searchParams.get('token');
    
    if (!token) {
      setStatus('error');
      setErrorMessage('No verification token provided');
      return;
    }

    verifyEmail(token);
  }, [searchParams]);

  const verifyEmail = async (token: string) => {
    try {
      const response = await axios.post(
        `${process.env.REACT_APP_API_URL}/api/v1/auth/verify-email`,
        { token },
        {
          headers: { 'Content-Type': 'application/json' }
        }
      );

      if (response.data.message.includes('already verified')) {
        setStatus('already-verified');
      } else {
        setStatus('success');
      }
    } catch (error) {
      setStatus('error');
      if (axios.isAxiosError(error)) {
        setErrorMessage(error.response?.data?.detail || 'Verification failed');
      } else {
        setErrorMessage('An unexpected error occurred');
      }
    }
  };

  return (
    <div className="verify-email-container">
      {status === 'loading' && (
        <div className="loading-state">
          <div className="spinner" />
          <h2>Verifying your email...</h2>
        </div>
      )}

      {status === 'success' && (
        <div className="success-state">
          <div className="check-icon">✓</div>
          <h2>Email Verified!</h2>
          <p>Your account is now active. You can log in to continue.</p>
          <button onClick={() => navigate('/login')}>
            Go to Login →
          </button>
        </div>
      )}

      {status === 'already-verified' && (
        <div className="already-verified-state">
          <div className="check-icon">✓</div>
          <h2>Email Already Verified</h2>
          <p>Your account is active.</p>
          <button onClick={() => navigate('/login')}>
            Go to Login →
          </button>
        </div>
      )}

      {status === 'error' && (
        <div className="error-state">
          <div className="error-icon">✗</div>
          <h2>Verification Failed</h2>
          <p>{errorMessage || 'The verification link is invalid or has expired.'}</p>
          <button onClick={() => navigate('/resend-verification')}>
            Request New Link →
          </button>
        </div>
      )}
    </div>
  );
}
```

---

## 🔄 Related Endpoint (Optional)

### Resend Verification Email
**Endpoint**: `POST /api/v1/auth/resend-verification`  
**Rate Limit**: 3 requests per hour per IP  
**Content-Type**: `application/json`

**Request Body**:
```json
{
  "email": "user@example.com"
}
```

**Success Response** (200 OK):
```json
{
  "message": "If the email exists, a verification link has been sent",
  "status": "success"
}
```

**Error Response** (400 Bad Request):
```json
{
  "detail": "Email already verified"
}
```

**Note**: The API intentionally does not reveal if an email exists (security best practice).

---

## 🧪 Testing Checklist

### Functional Tests
- [ ] Page loads when visiting `/verify-email?token=valid_token`
- [ ] Shows loading spinner immediately
- [ ] Calls backend API with correct token
- [ ] Displays success message on valid token
- [ ] Displays "already verified" message for verified accounts
- [ ] Shows error for invalid/expired tokens
- [ ] Shows error when token parameter is missing
- [ ] "Go to Login" button redirects to `/login`
- [ ] "Request New Link" button redirects to resend page

### UI/UX Tests
- [ ] Responsive design works on mobile (320px+)
- [ ] Matches PSQRD dark theme
- [ ] Icons render correctly
- [ ] Text is readable with proper contrast
- [ ] Buttons have hover/active states
- [ ] Loading spinner animates smoothly
- [ ] No horizontal scroll on mobile

### Error Handling
- [ ] Network errors display user-friendly message
- [ ] API errors show appropriate error text
- [ ] Token missing from URL shows error
- [ ] 429 rate limit errors handled gracefully

---

## 🚀 Deployment Notes

### Environment Variables
```bash
# Development
REACT_APP_API_URL=http://localhost:8000

# Production
REACT_APP_API_URL=https://api.psqrd.ai
```

### Backend Configuration
The backend `FRONTEND_URL` setting determines the verification link:
```bash
# Current (development)
FRONTEND_URL=http://localhost:3000

# Production
FRONTEND_URL=https://psqrd.ai
```

---

## 📋 Current Status

✅ **Backend**:
- Email sending functional (Microsoft Graph API)
- Verification tokens stored in Redis (1-hour expiry)
- API endpoint `/api/v1/auth/verify-email` working
- Login protection enforced (HTTP 403 for unverified users)
- Emails sent from `welcome@psqrd.ai` with Reddit-inspired template

❌ **Frontend**:
- `/verify-email` route missing (404 error)
- No verification page component
- Users cannot complete verification flow

---

## 🤝 Integration Flow

```
User Registration → Email Sent → User Clicks Link → Frontend Page → API Call → Database Update → Success Page
     (Backend)      (Graph API)   (User Inbox)     (MISSING)      (Backend)    (PostgreSQL)    (MISSING)
        ✅              ✅             ✅               ❌              ✅             ✅            ❌
```

**Blocker**: Frontend verification page component

---

## 📞 Support

**Backend Repository**: `/Users/ej/Downloads/RSS-Feed/backend`  
**Documentation**:
- `docs/GRAPH_API_SETUP.md` - Email configuration
- `docs/GRAPH_API_IMPLEMENTATION_SUMMARY.md` - Technical details
- `docs/EMAIL_CUSTOMIZATION_GUIDE.md` - Template customization

**Email Template**: `app/templates/email_verification.html`  
**API Endpoint Code**: `app/api/v1/endpoints/auth.py` (lines 232-294)

For backend questions, contact the backend team via the project repository.
