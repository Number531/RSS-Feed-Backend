"""
Custom Exceptions Module

Defines custom exception classes for the application with proper
HTTP status codes and error messages for FastAPI integration.
"""

from fastapi import HTTPException, status


class ValidationError(HTTPException):
    """
    Exception raised when validation fails.

    This is a custom exception that extends FastAPI's HTTPException
    to provide consistent validation error handling.
    """

    def __init__(self, detail: str):
        """
        Initialize validation error.

        Args:
            detail: Error message describing the validation failure
        """
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class NotFoundError(HTTPException):
    """
    Exception raised when a requested resource is not found.
    """

    def __init__(self, detail: str = "Resource not found"):
        """
        Initialize not found error.

        Args:
            detail: Error message describing what was not found
        """
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class AuthenticationError(HTTPException):
    """
    Exception raised when authentication fails.
    """

    def __init__(self, detail: str = "Could not validate credentials"):
        """
        Initialize authentication error.

        Args:
            detail: Error message describing the authentication failure
        """
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """
    Exception raised when user lacks required permissions.
    """

    def __init__(self, detail: str = "Not enough permissions"):
        """
        Initialize authorization error.

        Args:
            detail: Error message describing the permission issue
        """
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ConflictError(HTTPException):
    """
    Exception raised when there's a conflict with existing data.
    """

    def __init__(self, detail: str = "Resource conflict"):
        """
        Initialize conflict error.

        Args:
            detail: Error message describing the conflict
        """
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class DuplicateVoteError(ConflictError):
    """
    Exception raised when a user tries to vote on the same article twice.
    """

    def __init__(self, detail: str = "You have already voted on this article"):
        """
        Initialize duplicate vote error.

        Args:
            detail: Error message for duplicate vote attempt
        """
        super().__init__(detail=detail)


class InvalidVoteTypeError(ValidationError):
    """
    Exception raised when an invalid vote type is provided.
    """

    def __init__(self, detail: str = "Invalid vote type"):
        """
        Initialize invalid vote type error.

        Args:
            detail: Error message for invalid vote type
        """
        super().__init__(detail=detail)


# Fact-check related exceptions


class AlreadyFactCheckedError(ConflictError):
    """
    Exception raised when attempting to fact-check an already fact-checked article.
    """

    def __init__(self, detail: str = "Article has already been fact-checked"):
        """
        Initialize already fact-checked error.

        Args:
            detail: Error message for duplicate fact-check attempt
        """
        super().__init__(detail=detail)


class FactCheckAPIError(HTTPException):
    """
    Exception raised when the fact-check API returns an error.
    """

    def __init__(self, detail: str = "Fact-check API error occurred"):
        """
        Initialize fact-check API error.

        Args:
            detail: Error message from the API
        """
        super().__init__(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)


class FactCheckTimeoutError(HTTPException):
    """
    Exception raised when fact-check job exceeds timeout limit.
    """

    def __init__(self, detail: str = "Fact-check job timed out"):
        """
        Initialize fact-check timeout error.

        Args:
            detail: Error message for timeout
        """
        super().__init__(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=detail)


class ArticleNotFoundError(NotFoundError):
    """
    Exception raised when an article is not found.
    """

    def __init__(self, article_id: str = None):
        """
        Initialize article not found error.

        Args:
            article_id: The ID of the article that was not found
        """
        detail = f"Article with ID '{article_id}' not found" if article_id else "Article not found"
        super().__init__(detail=detail)
