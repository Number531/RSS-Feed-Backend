"""
Authentication API endpoints.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_user_service
from app.core.config import settings
from app.core.email_verification import (
    delete_verification_token,
    generate_verification_token,
    store_verification_token,
    validate_verification_token,
)
from app.core.exceptions import ConflictError
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.db.session import get_db
from app.middleware.rate_limit import limiter
from app.models.user import User
from app.services.user_service import UserService
from app.schemas.user import (
    ResendVerificationRequest,
    Token,
    TokenRefresh,
    UserCreate,
    UserLogin,
    UserResponse,
    VerifyEmailRequest,
)
from app.services.email_service import email_service
from app.services.graph_email_service import graph_email_service

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
@limiter.limit("10/hour")
async def register(
    request: Request,
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """
    Register a new user.
    
    Rate limits:
    - 3 requests per minute per IP
    - 10 requests per hour per IP

    Args:
        request: FastAPI request (required for rate limiting)
        user_data: User registration data
        user_service: User service for business logic

    Returns:
        Created user

    Raises:
        HTTPException: If email or username already exists
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Extract client info for audit logging
    ip_address = None
    if request.client:
        ip_address = request.client.host
    # Check for forwarded IP (behind proxy/load balancer)
    if "x-forwarded-for" in request.headers:
        ip_address = request.headers["x-forwarded-for"].split(",")[0].strip()
    elif "x-real-ip" in request.headers:
        ip_address = request.headers["x-real-ip"]
    
    user_agent = request.headers.get("user-agent")
    
    # Create user using service layer (handles atomicity and audit logging)
    try:
        user = await user_service.create_user(
            user_data,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Send verification email (if configured)
    # Use Graph API if configured, fallback to SMTP
    email_configured = settings.USE_GRAPH_API and settings.MICROSOFT_CLIENT_ID or settings.SMTP_HOST
    if settings.EMAIL_VERIFICATION_REQUIRED or email_configured:
        try:
            verification_token = generate_verification_token()
            await store_verification_token(user.id, verification_token)
            
            # Choose email service based on configuration
            if settings.USE_GRAPH_API and settings.MICROSOFT_CLIENT_ID:
                logger.info("Using Microsoft Graph API for email delivery")
                await graph_email_service.send_verification_email(
                    to_email=user.email,
                    username=user.username,
                    verification_token=verification_token
                )
            else:
                logger.info("Using SMTP for email delivery")
                await email_service.send_verification_email(
                    to_email=user.email,
                    username=user.username,
                    verification_token=verification_token
                )
            
            logger.info(
                f"Verification email sent to {user.email}",
                extra={"user_id": str(user.id), "email": user.email}
            )
        except Exception as e:
            # Log but don't fail registration if email fails
            logger.error(
                f"Failed to send verification email: {e}",
                extra={"user_id": str(user.id), "email": user.email}
            )

    return user


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Login user and return JWT tokens.

    Args:
        login_data: User login credentials
        db: Database session

    Returns:
        Access and refresh tokens

    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()

    if not user or not user.verify_password(login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    
    # Check email verification if required
    if settings.EMAIL_VERIFICATION_REQUIRED and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email address before logging in. Check your inbox for the verification link."
        )

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    # Generate tokens
    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(token_data: TokenRefresh, db: AsyncSession = Depends(get_db)):
    """
    Refresh access token using refresh token.

    Args:
        token_data: Refresh token
        db: Database session

    Returns:
        New access and refresh tokens

    Raises:
        HTTPException: If refresh token is invalid
    """
    # Verify refresh token
    token_payload = verify_token(token_data.refresh_token, token_type="refresh")

    if not token_payload or not token_payload.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user
    result = await db.execute(select(User).where(User.id == token_payload.user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate new tokens
    access_token = create_access_token(user.id, user.email)
    new_refresh_token = create_refresh_token(user.id)

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/verify-email")
async def verify_email(
    verify_data: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify user email address with token.
    
    Args:
        verify_data: Verification token from email
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Validate token and get user ID
    user_id = await validate_verification_token(verify_data.token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Get user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already verified
    if user.is_verified:
        return {
            "message": "Email already verified",
            "status": "success"
        }
    
    # Mark user as verified
    user.is_verified = True
    await db.commit()
    
    # Delete the verification token
    await delete_verification_token(verify_data.token)
    
    logger.info(
        f"User {user.id} verified email successfully",
        extra={"user_id": str(user.id), "email": user.email}
    )
    
    return {
        "message": "Email verified successfully",
        "status": "success"
    }


@router.post("/resend-verification")
@limiter.limit("3/hour")
async def resend_verification(
    request: Request,
    resend_data: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Resend verification email to user.
    
    Rate limit: 3 requests per hour per IP
    
    Args:
        resend_data: User email address
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user not found or already verified
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Find user by email
    result = await db.execute(select(User).where(User.email == resend_data.email))
    user = result.scalar_one_or_none()
    
    if not user:
        # Don't reveal if email exists for security
        return {
            "message": "If the email exists, a verification link has been sent",
            "status": "success"
        }
    
    # Check if already verified
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Generate and send new verification token
    try:
        verification_token = generate_verification_token()
        await store_verification_token(user.id, verification_token)
        
        # Choose email service based on configuration
        if settings.USE_GRAPH_API and settings.MICROSOFT_CLIENT_ID:
            logger.info("Using Microsoft Graph API for email delivery")
            await graph_email_service.send_verification_email(
                to_email=user.email,
                username=user.username,
                verification_token=verification_token
            )
        else:
            logger.info("Using SMTP for email delivery")
            await email_service.send_verification_email(
                to_email=user.email,
                username=user.username,
                verification_token=verification_token
            )
        
        logger.info(
            f"Resent verification email to {user.email}",
            extra={"user_id": str(user.id), "email": user.email}
        )
        
        return {
            "message": "Verification email sent",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(
            f"Failed to resend verification email: {e}",
            extra={"user_id": str(user.id), "email": user.email}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again later."
        )
