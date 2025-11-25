# Microsoft Graph API Email Setup Guide

**Complete guide for integrating Microsoft Graph API for secure, scalable email delivery in the RSS News Aggregator backend.**

## Table of Contents

- [Why Graph API?](#why-graph-api)
- [Prerequisites](#prerequisites)
- [Azure AD App Registration](#azure-ad-app-registration)
- [Configuration](#configuration)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)

---

## Why Graph API?

Microsoft Graph API is **strongly preferred** over SMTP for production deployments, especially for App Store applications:

| Feature | Microsoft Graph API | SMTP |
|---------|-------------------|------|
| **Authentication** | ✅ OAuth 2.0 (secure, no password storage) | ❌ Username/password in environment |
| **Security** | ✅ Token-based with automatic refresh | ❌ Plaintext credentials |
| **Rate Limits** | ✅ 10,000 emails/day per app | ❌ 30 emails/min (Gmail/Outlook) |
| **App Store** | ✅ Preferred by reviewers | ⚠️ May be rejected |
| **Scalability** | ✅ Enterprise-grade | ❌ Limited |
| **Monitoring** | ✅ Azure portal insights | ❌ Limited visibility |
| **Cost** | ✅ Free with Office 365 | ✅ Free (but limited) |

---

## Prerequisites

### Required

1. **Azure AD Account** (Office 365 or Microsoft 365)
   - Personal, work, or school account
   - Must have permission to register applications

2. **Python Dependencies**
   ```bash
   pip install msal>=1.32.0
   ```

3. **Email Account** (Outlook or Office 365)
   - Used as the "From" address for emails
   - Must be in the same Azure AD tenant as your app

### Optional

4. **Azure Portal Access** (for monitoring and configuration)

---

## Azure AD App Registration

### Step 1: Register Application

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**
4. Fill in:
   - **Name**: `RSS News Aggregator` (or your app name)
   - **Supported account types**: "Accounts in this organizational directory only"
   - **Redirect URI**: Leave blank (not needed for service-to-service)
5. Click **Register**

### Step 2: Get Application Credentials

After registration, copy these values:

```
Application (client) ID: cd54bdd1-062a-4838-a27b-a89902ae112e
Directory (tenant) ID: 09c43c16-90f6-4e5f-be39-684cff80debf
```

### Step 3: Create Client Secret

1. In your app registration, go to **Certificates & secrets**
2. Click **New client secret**
3. Set:
   - **Description**: `RSS Backend Email Service`
   - **Expires**: 24 months (or custom)
4. Click **Add**
5. **IMMEDIATELY COPY** the secret value:
   ```
   Value: your-client-secret-here
   Secret ID: b8a5e441-e00a-4b45-b59d-8acb9e063e0a
   ```
   ⚠️ **This value is only shown ONCE!** Save it securely.

### Step 4: Configure API Permissions

1. Go to **API permissions** in your app
2. Click **Add a permission**
3. Select **Microsoft Graph** → **Application permissions**
4. Search for and select **`Mail.Send`**
5. Click **Add permissions**
6. ⚠️ **CRITICAL**: Click **Grant admin consent** (requires admin)
   - If you don't see this button, ask your tenant admin
   - The permission WILL NOT WORK without admin consent

### Step 5: Verify Permissions

Ensure you see:
- ✅ **Mail.Send** - Application - Granted for [Your Tenant]

---

## Configuration

### 1. Copy Graph API Settings

Copy the settings from `.env.graph-api` to your main `.env` file:

```bash
# Microsoft Graph API Settings
MICROSOFT_CLIENT_ID=cd54bdd1-062a-4838-a27b-a89902ae112e
MICROSOFT_CLIENT_SECRET=your-client-secret-here
MICROSOFT_TENANT_ID=09c43c16-90f6-4e5f-be39-684cff80debf
MICROSOFT_SENDER_EMAIL=your-actual-email@outlook.com  # CHANGE THIS!
MICROSOFT_SENDER_NAME=RSS News Aggregator
USE_GRAPH_API=true

# Email Verification Settings
EMAIL_VERIFICATION_REQUIRED=false  # Set to true to require verification
FRONTEND_URL=http://localhost:3000
VERIFICATION_TOKEN_EXPIRE_HOURS=1
```

### 2. Update Sender Email

Replace `MICROSOFT_SENDER_EMAIL` with your **actual Outlook/Office 365 email address**:

```bash
# ❌ Wrong (placeholder)
MICROSOFT_SENDER_EMAIL=your-outlook-email@outlook.com

# ✅ Correct (your email)
MICROSOFT_SENDER_EMAIL=john.smith@contoso.com
```

**Important**: The sender email MUST be:
- A valid mailbox in your Azure AD tenant
- The same account used to register the app (or another account in the tenant)

### 3. Enable Graph API

```bash
USE_GRAPH_API=true
```

When `USE_GRAPH_API=true`, the backend will:
- Use Microsoft Graph API for ALL email delivery
- Fall back to SMTP ONLY if Graph API fails
- Log which service is being used

---

## Testing

### Method 1: Test Script (Recommended)

Run the comprehensive test suite:

```bash
python scripts/testing/test_graph_email.py
```

This tests:
1. ✅ OAuth 2.0 authentication
2. ✅ Verification email sending
3. ✅ Custom email sending

**Expected output:**

```
================================================================================
Microsoft Graph API Email Delivery Test Suite
================================================================================

Configuration:
   USE_GRAPH_API: True
   CLIENT_ID: cd54bdd1-062a-4838-a27b-a89902ae112e
   TENANT_ID: 09c43c16-90f6-4e5f-be39-684cff80debf
   SENDER_EMAIL: john.smith@contoso.com
   SENDER_NAME: RSS News Aggregator

================================================================================
TEST 1: Microsoft Graph API Authentication
================================================================================
✅ Authentication successful!
   Token type: Bearer
   Expires in: 3599 seconds
   Token prefix: eyJ0eXAiOiJKV1QiLCJub25jZSI6...

================================================================================
TEST 2: Send Verification Email
================================================================================
Enter recipient email address (or press Enter for ehgj1996@gmail.com): 

Sending verification email to: ehgj1996@gmail.com
Username: TestUser
Verification token: test-token-12345

✅ Email sent successfully!
   Recipient: ehgj1996@gmail.com
   From: john.smith@contoso.com
   Subject: Verify Your Email Address

   Verification link:
   http://localhost:3000/verify-email?token=test-token-12345

================================================================================
Test Summary
================================================================================
   Authentication             ✅ PASSED
   Verification Email         ✅ PASSED
   Custom Email               ✅ PASSED

Total: 3/3 tests passed

🎉 All tests passed! Microsoft Graph API email delivery is working.
```

### Method 2: Test Registration Endpoint

1. Start the backend server:
   ```bash
   make run
   # or: uvicorn app.main:app --reload
   ```

2. Register a test user:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "username": "testuser",
       "password": "SecurePass123!"
     }'
   ```

3. Check the logs:
   ```
   INFO: Using Microsoft Graph API for email delivery
   INFO: Verification email sent to test@example.com
   ```

4. Check your inbox at `test@example.com` for the verification email.

### Method 3: Python REPL

```python
import asyncio
from app.services.graph_email_service import graph_email_service

async def test():
    await graph_email_service.send_verification_email(
        to_email="recipient@example.com",
        username="TestUser",
        verification_token="test-token-123"
    )
    print("Email sent!")

asyncio.run(test())
```

---

## Deployment

### Docker Deployment

1. Add environment variables to your `docker-compose.yml`:

```yaml
services:
  backend:
    environment:
      - MICROSOFT_CLIENT_ID=${MICROSOFT_CLIENT_ID}
      - MICROSOFT_CLIENT_SECRET=${MICROSOFT_CLIENT_SECRET}
      - MICROSOFT_TENANT_ID=${MICROSOFT_TENANT_ID}
      - MICROSOFT_SENDER_EMAIL=${MICROSOFT_SENDER_EMAIL}
      - USE_GRAPH_API=true
```

2. Create a `.env` file with your credentials (NOT committed to git):

```bash
MICROSOFT_CLIENT_ID=cd54bdd1-062a-4838-a27b-a89902ae112e
MICROSOFT_CLIENT_SECRET=your-client-secret-here
MICROSOFT_TENANT_ID=09c43c16-90f6-4e5f-be39-684cff80debf
MICROSOFT_SENDER_EMAIL=noreply@yourcompany.com
```

3. Deploy:

```bash
docker-compose up -d
```

### Cloud Deployment (Railway, Heroku, Azure, etc.)

Add these environment variables to your cloud platform:

```
MICROSOFT_CLIENT_ID=cd54bdd1-062a-4838-a27b-a89902ae112e
MICROSOFT_CLIENT_SECRET=your-client-secret-here
MICROSOFT_TENANT_ID=09c43c16-90f6-4e5f-be39-684cff80debf
MICROSOFT_SENDER_EMAIL=noreply@yourcompany.com
USE_GRAPH_API=true
```

---

## Troubleshooting

### Error: "AADSTS700016: Application with identifier ... was not found"

**Cause**: Invalid Client ID or Tenant ID

**Solution**:
1. Verify `MICROSOFT_CLIENT_ID` and `MICROSOFT_TENANT_ID` in Azure Portal
2. Ensure you're using the correct tenant (check **Directory (tenant) ID**)
3. Wait 5 minutes after app registration (propagation delay)

---

### Error: "AADSTS7000215: Invalid client secret provided"

**Cause**: Incorrect or expired client secret

**Solution**:
1. Go to Azure Portal → Your App → **Certificates & secrets**
2. Create a NEW client secret
3. Copy the VALUE (not the Secret ID)
4. Update `MICROSOFT_CLIENT_SECRET` in `.env`

---

### Error: "ErrorAccessDenied: Access is denied"

**Cause**: Missing admin consent for Mail.Send permission

**Solution**:
1. Go to Azure Portal → Your App → **API permissions**
2. Click **Grant admin consent for [Your Tenant]**
3. If you're not an admin, request consent from your tenant administrator
4. Verify the permission shows "Granted for [Your Tenant]"

---

### Error: "ErrorInvalidRecipient: The recipient ... was not found"

**Cause**: Trying to send to an external email address without proper tenant configuration

**Solution**:
1. **Option A (Recommended)**: Add recipient's domain to Azure AD as a guest
2. **Option B**: Enable external email in tenant settings
3. **Option C**: Use a test email in the same tenant for testing

---

### Error: "401 Unauthorized" when sending email

**Cause**: Sender email doesn't exist or doesn't have permission

**Solution**:
1. Ensure `MICROSOFT_SENDER_EMAIL` is a REAL mailbox in your tenant
2. Verify the mailbox is active (not disabled)
3. Test with your own email address first

---

### Emails Not Being Sent (No Error)

**Check logs:**

```bash
# Should see:
INFO: Using Microsoft Graph API for email delivery
INFO: Verification email sent to user@example.com

# If you see this instead:
INFO: Using SMTP for email delivery
# Graph API is NOT enabled - check USE_GRAPH_API=true in .env
```

**Verify configuration:**

```python
from app.core.config import settings
print(f"USE_GRAPH_API: {settings.USE_GRAPH_API}")
print(f"CLIENT_ID: {settings.MICROSOFT_CLIENT_ID}")
print(f"SENDER: {settings.MICROSOFT_SENDER_EMAIL}")
```

---

## Security Best Practices

### 1. Secure Credential Storage

❌ **NEVER** commit credentials to git:

```bash
# .gitignore should include:
.env
.env.local
.env.*.local
.env.graph-api
```

✅ **DO** use environment variables or secret managers:

- **Development**: `.env` file (gitignored)
- **Production**: Cloud platform secrets (Railway, Heroku Config Vars, Azure Key Vault)
- **CI/CD**: GitHub Secrets, GitLab CI Variables

### 2. Client Secret Rotation

- Client secrets expire (default: 2 years)
- **Set a calendar reminder** to rotate secrets before expiration
- Keep the OLD secret active for 1 day during rotation to avoid downtime

**Rotation process:**

1. Create NEW client secret in Azure Portal
2. Update `MICROSOFT_CLIENT_SECRET` in production environment
3. Monitor logs for authentication errors
4. After 24 hours, delete OLD secret in Azure Portal

### 3. Principle of Least Privilege

Only grant the `Mail.Send` permission:
- ❌ Do NOT grant `Mail.ReadWrite` (unnecessary)
- ❌ Do NOT grant `Mail.Send.Shared` (unless needed)
- ✅ DO grant ONLY `Mail.Send` application permission

### 4. Monitor API Usage

- Track email sending in Azure Portal → Your App → **Usage**
- Set up alerts for:
  - Failed authentication (> 10 in 1 hour)
  - High email volume (> 5,000 in 1 day)
  - Permission changes

### 5. Rate Limiting

Graph API limits:
- **10,000 emails/day** per application
- No per-minute limit (unlike SMTP)

Implement application-level rate limiting if needed:

```python
# Already implemented in auth.py:
@limiter.limit("3/minute")  # Registration
@limiter.limit("3/hour")    # Resend verification
```

---

## Architecture Details

### Authentication Flow

```
Backend Service
    │
    ├─→ GraphAuthManager
    │       │
    │       ├─→ MSAL Library
    │       │       │
    │       │       └─→ Azure AD Token Endpoint
    │       │               └─→ Returns OAuth 2.0 access token
    │       │
    │       └─→ Token Cache (5-min expiry buffer)
    │
    └─→ GraphEmailService
            │
            └─→ Microsoft Graph API
                    └─→ Sends email via /users/{email}/sendMail
```

### Token Caching

- Tokens are cached in memory with 5-minute expiry buffer
- Reduces authentication API calls (60 min token → 55 min cache)
- Automatic refresh via MSAL when expired

### Fallback Strategy

```python
if USE_GRAPH_API and MICROSOFT_CLIENT_ID:
    use Graph API
else:
    use SMTP
```

This allows graceful fallback if Graph API credentials are not configured.

---

## Additional Resources

- [Microsoft Graph API Documentation](https://docs.microsoft.com/en-us/graph/api/user-sendmail)
- [MSAL Python Documentation](https://github.com/AzureAD/microsoft-authentication-library-for-python)
- [Azure AD App Registration Guide](https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
- [Mail.Send Permission Reference](https://docs.microsoft.com/en-us/graph/permissions-reference#mailsend)

---

## Support

If you encounter issues not covered in this guide:

1. Check the [Troubleshooting](#troubleshooting) section
2. Run `python scripts/testing/test_graph_email.py` for diagnostics
3. Check logs for detailed error messages
4. Verify Azure AD app configuration in [Azure Portal](https://portal.azure.com)

---

**Last Updated**: November 24, 2025  
**Client Secret Expires**: November 24, 2027  
**Version**: 1.0.0
