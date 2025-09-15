"""
Custom exceptions and exception handlers for the Excel Mock Interviewer API
"""
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Any, Dict
import logging
import time

logger = logging.getLogger(__name__)

# Custom Exception Classes
class InterviewNotFoundException(HTTPException):
    def __init__(self, interview_id: str):
        self.interview_id = interview_id
        super().__init__(status_code=404, detail=f"Interview with ID '{interview_id}' not found")

class InvalidRequestException(HTTPException):
    def __init__(self, message: str, field: str = None):
        self.field = field
        detail = f"Invalid request: {message}"
        if field:
            detail += f" (field: {field})"
        super().__init__(status_code=400, detail=detail)

class EvaluationException(HTTPException):
    def __init__(self, message: str = "Failed to evaluate response"):
        super().__init__(status_code=500, detail=f"Evaluation error: {message}")

class RateLimitExceededException(HTTPException):
    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(
            status_code=429,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": str(retry_after)}
        )

# Exception Handlers
async def handle_interview_not_found(request: Request, exc: InterviewNotFoundException) -> JSONResponse:
    logger.warning(f"Interview not found: {exc.interview_id}")
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "type": "InterviewNotFound",
                "message": exc.detail,
                "interview_id": exc.interview_id,
                "timestamp": time.time()
            }
        }
    )

async def handle_invalid_request(request: Request, exc: InvalidRequestException) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "type": "InvalidRequest",
                "message": exc.detail,
                "field": exc.field if exc.field else None,
                "timestamp": time.time()
            }
        }
    )

# Exception handlers dictionary
exception_handlers = {
    InterviewNotFoundException: handle_interview_not_found,
    InvalidRequestException: handle_invalid_request,
}