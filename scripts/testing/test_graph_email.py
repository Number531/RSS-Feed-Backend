#!/usr/bin/env python3
"""
Test script for Microsoft Graph API email delivery.

This script tests:
1. Graph API authentication (OAuth 2.0 token acquisition)
2. Sending verification email via Graph API
3. HTML and text email template rendering

Usage:
    python scripts/testing/test_graph_email.py

Prerequisites:
    - Copy .env.graph-api settings to .env
    - Set your Outlook email in MICROSOFT_SENDER_EMAIL
    - Ensure Azure AD app has Mail.Send permission with admin consent
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.core.graph_auth import GraphAuthManager
from app.services.graph_email_service import graph_email_service


async def test_authentication():
    """Test OAuth 2.0 authentication with Microsoft Graph API."""
    print("\n" + "=" * 80)
    print("TEST 1: Microsoft Graph API Authentication")
    print("=" * 80)
    
    try:
        auth_manager = GraphAuthManager()
        access_token = auth_manager.get_access_token()
        
        if not access_token:
            print("❌ Authentication failed: No access token returned")
            return False
        
        print("✅ Authentication successful!")
        print(f"   Token type: Bearer")
        print(f"   Token prefix: {access_token[:50]}...")
        print(f"   Token length: {len(access_token)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_send_verification_email():
    """Test sending a verification email via Graph API."""
    print("\n" + "=" * 80)
    print("TEST 2: Send Verification Email")
    print("=" * 80)
    
    # Get test recipient email
    recipient_email = input("Enter recipient email address (or press Enter for ehgj1996@gmail.com): ").strip()
    if not recipient_email:
        recipient_email = "ehgj1996@gmail.com"
    
    username = "TestUser"
    verification_token = "test-token-12345"
    
    print(f"\nSending verification email to: {recipient_email}")
    print(f"Username: {username}")
    print(f"Verification token: {verification_token}")
    
    try:
        await graph_email_service.send_verification_email(
            to_email=recipient_email,
            username=username,
            verification_token=verification_token,
        )
        
        print("\n✅ Email sent successfully!")
        print(f"   Recipient: {recipient_email}")
        print(f"   From: {settings.MICROSOFT_SENDER_EMAIL}")
        print(f"   Subject: Verify Your Email Address")
        print(f"\n   Verification link:")
        print(f"   {settings.FRONTEND_URL}/verify-email?token={verification_token}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Failed to send email: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_send_custom_email():
    """Test sending a custom email with specific content."""
    print("\n" + "=" * 80)
    print("TEST 3: Send Custom Email")
    print("=" * 80)
    
    recipient_email = input("Enter recipient email address (or press Enter to skip): ").strip()
    if not recipient_email:
        print("⏭️  Skipping custom email test")
        return True
    
    subject = "Test Email from RSS News Aggregator"
    html_body = """
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #0066cc;">Test Email</h2>
            <p>This is a test email from the RSS News Aggregator backend.</p>
            <p>If you received this, the Microsoft Graph API integration is working correctly!</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                Sent via Microsoft Graph API<br>
                OAuth 2.0 Client Credentials Flow
            </p>
        </body>
    </html>
    """
    text_body = """
    Test Email
    
    This is a test email from the RSS News Aggregator backend.
    If you received this, the Microsoft Graph API integration is working correctly!
    
    ---
    Sent via Microsoft Graph API
    OAuth 2.0 Client Credentials Flow
    """
    
    print(f"\nSending custom email to: {recipient_email}")
    print(f"Subject: {subject}")
    
    try:
        await graph_email_service.send_email(
            to_email=recipient_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )
        
        print("\n✅ Custom email sent successfully!")
        print(f"   Recipient: {recipient_email}")
        print(f"   From: {settings.MICROSOFT_SENDER_EMAIL}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Failed to send custom email: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all Graph API email tests."""
    print("\n" + "=" * 80)
    print("Microsoft Graph API Email Delivery Test Suite")
    print("=" * 80)
    
    # Verify configuration
    print("\nConfiguration:")
    print(f"   USE_GRAPH_API: {settings.USE_GRAPH_API}")
    print(f"   CLIENT_ID: {settings.MICROSOFT_CLIENT_ID}")
    print(f"   TENANT_ID: {settings.MICROSOFT_TENANT_ID}")
    print(f"   SENDER_EMAIL: {settings.MICROSOFT_SENDER_EMAIL}")
    print(f"   SENDER_NAME: {settings.MICROSOFT_SENDER_NAME}")
    
    if not settings.MICROSOFT_CLIENT_ID or not settings.MICROSOFT_CLIENT_SECRET:
        print("\n❌ ERROR: Microsoft Graph API credentials not configured!")
        print("   Please copy settings from .env.graph-api to your .env file")
        sys.exit(1)
    
    if not settings.MICROSOFT_SENDER_EMAIL or settings.MICROSOFT_SENDER_EMAIL == "your-outlook-email@outlook.com":
        print("\n⚠️  WARNING: MICROSOFT_SENDER_EMAIL not configured!")
        print("   Please set your actual Outlook/Office 365 email address in .env")
        sys.exit(1)
    
    # Run tests
    results = []
    
    # Test 1: Authentication
    auth_success = await test_authentication()
    results.append(("Authentication", auth_success))
    
    if not auth_success:
        print("\n❌ Authentication failed - cannot proceed with email tests")
        sys.exit(1)
    
    # Test 2: Verification email
    verify_success = await test_send_verification_email()
    results.append(("Verification Email", verify_success))
    
    # Test 3: Custom email (optional)
    custom_success = await test_send_custom_email()
    results.append(("Custom Email", custom_success))
    
    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {test_name:25} {status}")
    
    total_passed = sum(1 for _, success in results if success)
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 All tests passed! Microsoft Graph API email delivery is working.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
