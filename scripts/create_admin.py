#!/usr/bin/env python3
"""
Create an admin user for the RSS Feed application.

Usage:
    python scripts/create_admin.py
    
Or with custom credentials:
    ADMIN_EMAIL=admin@example.com ADMIN_USERNAME=admin ADMIN_PASSWORD=SecurePass123! python scripts/create_admin.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.core.config import settings


async def create_admin_user():
    """Create an admin user with credentials from environment variables."""
    
    print("🔐 Creating admin user...")
    print(f"   Email: {settings.ADMIN_EMAIL}")
    print(f"   Username: {settings.ADMIN_USERNAME}")
    
    # Validate credentials
    if not settings.ADMIN_EMAIL or not settings.ADMIN_USERNAME or not settings.ADMIN_PASSWORD:
        print("❌ Error: Admin credentials not set in environment variables")
        print("   Required: ADMIN_EMAIL, ADMIN_USERNAME, ADMIN_PASSWORD")
        return False
    
    if settings.ADMIN_PASSWORD == "changeme123!-MUST-CHANGE-IN-PRODUCTION":
        print("⚠️  Warning: Using default password! Please change in production.")
    
    async with AsyncSessionLocal() as db:
        try:
            # Check if admin already exists
            result = await db.execute(
                select(User).where(User.email == settings.ADMIN_EMAIL)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"⚠️  Admin user already exists with email: {settings.ADMIN_EMAIL}")
                print(f"   User ID: {existing_user.id}")
                print(f"   Is Superuser: {existing_user.is_superuser}")
                
                # Update to ensure superuser status
                if not existing_user.is_superuser:
                    existing_user.is_superuser = True
                    existing_user.is_verified = True
                    await db.commit()
                    print("   ✅ Updated to superuser status")
                
                return True
            
            # Create new admin user
            admin = User(
                email=settings.ADMIN_EMAIL,
                username=settings.ADMIN_USERNAME,
                full_name="Administrator",
                is_superuser=True,
                is_verified=True,
                is_active=True
            )
            admin.set_password(settings.ADMIN_PASSWORD)
            
            db.add(admin)
            await db.commit()
            await db.refresh(admin)
            
            print(f"✅ Admin user created successfully!")
            print(f"   User ID: {admin.id}")
            print(f"   Email: {admin.email}")
            print(f"   Username: {admin.username}")
            print(f"   Superuser: {admin.is_superuser}")
            print(f"   Verified: {admin.is_verified}")
            print()
            print("🔑 You can now login with these credentials")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            await db.rollback()
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Main entry point."""
    print("=" * 60)
    print("RSS Feed - Admin User Creation")
    print("=" * 60)
    print()
    
    success = await create_admin_user()
    
    print()
    print("=" * 60)
    if success:
        print("✅ Admin user setup complete!")
        print()
        print("Next steps:")
        print("1. Start the application")
        print("2. Login at /api/v1/auth/login")
        print("3. Access admin features")
    else:
        print("❌ Admin user setup failed!")
        print("Please check the error messages above")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
