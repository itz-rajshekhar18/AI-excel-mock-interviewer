"""
Dependencies for FastAPI routes in Excel Mock Interviewer API
"""
from fastapi import Depends, Request, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import time

from excel_interviewer.models.database import get_db, InterviewDB
from excel_interviewer.models.interview import Interview
from excel_interviewer.api.exceptions import InterviewNotFoundException, RateLimitExceededException

# Rate limiting storage
rate_limit_store = {}

async def get_current_interview(interview_id: str, db: Session = Depends(get_db)) -> Interview:
    """Get current interview from database"""
    db_interview = db.query(InterviewDB).filter(InterviewDB.id == interview_id).first()
    
    if not db_interview:
        raise InterviewNotFoundException(interview_id)
    
    # Convert to Pydantic model
    interview_data = {
        "id": str(db_interview.id),
        "candidate_name": db_interview.candidate_name,
        "candidate_email": db_interview.candidate_email,
        "position": db_interview.position,
        "status": db_interview.status,
        "skill_level": db_interview.skill_level,
        "created_at": db_interview.created_at
    }
    
    return Interview(**interview_data)

class RateLimiter:
    def __init__(self, calls: int, period: int = 60):
        self.calls = calls
        self.period = period
    
    async def __call__(self, request: Request) -> bool:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        key = f"{client_ip}:{request.url.path}"
        
        if key not in rate_limit_store:
            rate_limit_store[key] = []
        
        rate_limit_store[key].append(current_time)
        
        # Clean old entries
        recent_requests = [ts for ts in rate_limit_store[key] if current_time - ts <= self.period]
        rate_limit_store[key] = recent_requests
        
        if len(recent_requests) > self.calls:
            raise RateLimitExceededException()
        
        return True

# Pre-configured rate limiters
rate_limiter = RateLimiter(calls=100, period=60)
evaluation_rate_limiter = RateLimiter(calls=30, period=60)
