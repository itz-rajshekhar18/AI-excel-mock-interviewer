"""
API Request/Response Schemas for Excel Mock Interviewer

This module defines all Pydantic schemas used for API request validation
and response serialization in the FastAPI application.
"""
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

# ===== ENUMS =====

class InterviewStatusEnum(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class SkillLevelEnum(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class QuestionTypeEnum(str, Enum):
    FORMULA = "formula"
    DATA_ANALYSIS = "data_analysis"
    PROBLEM_SOLVING = "problem_solving"
    SCENARIO = "scenario"
    PRACTICAL = "practical"

# ===== REQUEST SCHEMAS =====

class InterviewCreateRequest(BaseModel):
    """Schema for creating a new interview"""
    candidate_name: str = Field(..., min_length=2, max_length=100)
    candidate_email: str = Field(...)
    position: str = Field(..., min_length=2, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    skill_level: SkillLevelEnum = Field(SkillLevelEnum.INTERMEDIATE)
    max_questions: Optional[int] = Field(15, ge=5, le=30)
    time_limit_minutes: Optional[int] = Field(45, ge=15, le=120)
    
    @validator('candidate_email')
    def validate_email(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower()

class ResponseSubmissionRequest(BaseModel):
    """Schema for submitting candidate responses"""
    candidate_response: str = Field(..., min_length=1, max_length=10000)
    response_time_seconds: Optional[float] = Field(None, ge=0)
    confidence_level: Optional[int] = Field(None, ge=1, le=5)

class EvaluationRequest(BaseModel):
    """Schema for standalone response evaluation"""
    question_text: str = Field(..., min_length=10, max_length=2000)
    candidate_response: str = Field(..., min_length=1, max_length=10000)
    difficulty_level: str = Field(...)
    question_type: QuestionTypeEnum = Field(QuestionTypeEnum.FORMULA)

# ===== RESPONSE SCHEMAS =====

class InterviewResponse(BaseModel):
    """Schema for interview information response"""
    interview_id: str
    candidate_name: str
    candidate_email: str
    position: str
    department: Optional[str]
    status: InterviewStatusEnum
    skill_level: SkillLevelEnum
    created_at: datetime
    questions_completed: int = 0
    total_questions: int = 0
    current_score: Optional[float] = None

class QuestionResponse(BaseModel):
    """Schema for question information"""
    id: str
    question_text: str
    question_type: QuestionTypeEnum
    difficulty: str
    category: Optional[str]
    expected_keywords: List[str] = []
    time_limit_seconds: Optional[int] = None

class EvaluationResponse(BaseModel):
    """Schema for evaluation results"""
    technical_accuracy: float = Field(..., ge=0, le=100)
    communication_clarity: float = Field(..., ge=0, le=100)
    problem_solving_approach: float = Field(..., ge=0, le=100)
    completeness: float = Field(..., ge=0, le=100)
    efficiency: float = Field(..., ge=0, le=100)
    overall_score: float = Field(..., ge=0, le=100)
    feedback: str
    strengths: List[str] = []
    areas_for_improvement: List[str] = []
    next_difficulty_level: str

class FinalAssessmentResponse(BaseModel):
    """Schema for final interview assessment"""
    interview_id: str
    overall_score: float = Field(..., ge=0, le=100)
    skill_level_assessment: str
    hire_recommendation: str
    detailed_feedback: str
    executive_summary: str
    recommendations: List[str] = []
    total_questions: int
    interview_duration_minutes: int
    assessment_date: datetime

class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, Any] = {}
    database: Dict[str, str] = {}

# ===== ERROR SCHEMAS =====

class ErrorResponse(BaseModel):
    """Error response schema"""
    error: Dict[str, Any]
    suggestions: Optional[List[str]] = None
