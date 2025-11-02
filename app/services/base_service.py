"""
Base Service Module

Provides a common base class for all service layers with shared utilities
including error handling, pagination validation, and logging integration.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Generic, Optional, TypeVar

from app.core.exceptions import ValidationError

T = TypeVar("T")


class BaseService(Generic[T]):
    """
    Base service class providing common functionality for all service layers.

    This class provides:
    - Standardized error handling
    - Pagination validation
    - Logging integration
    - Common utility methods
    """

    def __init__(self, logger_name: Optional[str] = None):
        """
        Initialize the base service.

        Args:
            logger_name: Optional custom logger name. If not provided,
                        uses the class name.
        """
        self.logger = logging.getLogger(logger_name or self.__class__.__name__)

    def validate_pagination(self, skip: int, limit: int, max_limit: int = 100) -> None:
        """
        Validate pagination parameters.

        Args:
            skip: Number of items to skip
            limit: Number of items to return
            max_limit: Maximum allowed limit value

        Raises:
            ValidationError: If pagination parameters are invalid
        """
        if skip < 0:
            raise ValidationError("Skip parameter must be non-negative")

        if limit < 1:
            raise ValidationError("Limit parameter must be at least 1")

        if limit > max_limit:
            raise ValidationError(f"Limit parameter cannot exceed {max_limit}")

    def log_operation(self, operation: str, user_id: Optional[int] = None, **kwargs: Any) -> None:
        """
        Log a service operation with context.

        Args:
            operation: Name of the operation being performed
            user_id: Optional user ID performing the operation
            **kwargs: Additional context to log
        """
        context = {
            "operation": operation,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if user_id is not None:
            context["user_id"] = user_id

        context.update(kwargs)

        self.logger.info(f"Operation: {operation}", extra={"context": context})

    def log_error(
        self, operation: str, error: Exception, user_id: Optional[int] = None, **kwargs: Any
    ) -> None:
        """
        Log an error that occurred during a service operation.

        Args:
            operation: Name of the operation that failed
            error: The exception that was raised
            user_id: Optional user ID that triggered the error
            **kwargs: Additional context to log
        """
        context = {
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat(),
        }

        if user_id is not None:
            context["user_id"] = user_id

        context.update(kwargs)

        self.logger.error(
            f"Operation failed: {operation}", extra={"context": context}, exc_info=True
        )

    def create_success_response(
        self, data: T, message: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized success response.

        Args:
            data: The response data
            message: Optional success message
            metadata: Optional additional metadata

        Returns:
            Standardized response dictionary
        """
        response = {
            "success": True,
            "data": data,
        }

        if message:
            response["message"] = message

        if metadata:
            response["metadata"] = metadata

        return response

    def create_pagination_metadata(
        self, total: int, skip: int, limit: int, returned_count: int
    ) -> Dict[str, Any]:
        """
        Create pagination metadata for responses.

        Args:
            total: Total number of items available
            skip: Number of items skipped
            limit: Maximum number of items requested
            returned_count: Actual number of items returned

        Returns:
            Dictionary containing pagination metadata
        """
        has_more = skip + returned_count < total
        page_number = (skip // limit) + 1 if limit > 0 else 1
        total_pages = (total + limit - 1) // limit if limit > 0 else 1

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "returned": returned_count,
            "has_more": has_more,
            "page": page_number,
            "total_pages": total_pages,
        }

    async def _handle_repository_error(
        self, operation: str, error: Exception, user_id: Optional[int] = None
    ) -> None:
        """
        Handle errors that occur at the repository layer.

        This method logs the error and can be extended to perform
        additional error handling logic like notifications or metrics.

        Args:
            operation: Name of the operation that failed
            error: The exception that was raised
            user_id: Optional user ID context
        """
        self.log_error(operation, error, user_id)
        # Re-raise the error to be handled by the API layer
        raise
