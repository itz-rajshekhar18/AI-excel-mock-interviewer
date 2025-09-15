"""
FastAPI Router and API components for Excel Mock Interviewer

This module contains all API route definitions, middleware, dependencies,
and exception handlers for the Excel skills assessment platform.
"""

from .routes import router
from .dependencies import (
    get_db,
    get_current_interview,
    validate_interview_access,
    rate_limiter
)
from .schema import (
    InterviewCreateRequest,
    ResponseSubmissionRequest,
    EvaluationRequest,
    InterviewResponse
)
from .middleware import (
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    RateLimitMiddleware
)
from .exceptions import (
    InterviewNotFoundException,
    InvalidRequestException,
    EvaluationException,
    QuestionBankException,
    handle_interview_not_found,
    handle_invalid_request,
    handle_evaluation_exception,
    handle_question_bank_exception,
    exception_handlers
)

# API version
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# Export main router and utilities
__all__ = [
    "router", "get_db", "get_current_interview", "validate_interview_access",
    "rate_limiter", "InterviewCreateRequest", "ResponseSubmissionRequest",
    "EvaluationRequest", "InterviewResponse", "RequestLoggingMiddleware", 
    "SecurityHeadersMiddleware", "RateLimitMiddleware", "InterviewNotFoundException", 
    "InvalidRequestException", "EvaluationException", "QuestionBankException",
    "handle_interview_not_found", "handle_invalid_request", "handle_evaluation_exception",
    "handle_question_bank_exception", "exception_handlers", "API_VERSION", "API_PREFIX"
]
