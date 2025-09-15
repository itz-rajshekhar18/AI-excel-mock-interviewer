"""
Interview data models for Excel Mock Interviewer

This module defines all Pydantic models related to interviews including
status tracking, skill levels, and data validation.
"""
from pydantic import BaseModel, Field, validator, EmailStr
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
import uuid
import re

class InterviewStatus(str, Enum):
    """Interview status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    EXPIRED = "expired"

class SkillLevel(str, Enum):
    """Skill level enumeration for Excel proficiency"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class InterviewPriority(str, Enum):
    """Interview priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class Interview(BaseModel):
    """Main interview model with comprehensive validation"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    candidate_name: str = Field(..., min_length=2, max_length=100, description="Candidate's full name")
    candidate_email: EmailStr = Field(..., description="Candidate's email address")
    position: str = Field(..., min_length=2, max_length=100, description="Position being interviewed for")
    department: Optional[str] = Field(None, max_length=50, description="Department or team")
    status: InterviewStatus = Field(default=InterviewStatus.PENDING, description="Current interview status")
    skill_level: SkillLevel = Field(default=SkillLevel.INTERMEDIATE, description="Target skill level")
    priority: InterviewPriority = Field(default=InterviewPriority.NORMAL, description="Interview priority")
    
    # Timing fields
    start_time: Optional[datetime] = Field(None, description="Interview start timestamp")
    end_time: Optional[datetime] = Field(None, description="Interview end timestamp")
    duration_minutes: Optional[int] = Field(None, ge=0, le=180, description="Interview duration in minutes")
    
    # Interview data
    questions_asked: List[str] = Field(default_factory=list, description="List of question IDs asked")
    responses: List[Dict[str, Any]] = Field(default_factory=list, description="Candidate responses and evaluations")
    current_question_id: Optional[str] = Field(None, description="Currently active question ID")
    
    # Scoring and feedback
    overall_score: Optional[float] = Field(None, ge=0, le=100, description="Overall interview score")
    category_scores: Dict[str, float] = Field(default_factory=dict, description="Scores by category")
    feedback: Optional[str] = Field(None, max_length=5000, description="Detailed feedback")
    hire_recommendation: Optional[str] = Field(None, description="Hiring recommendation")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Interview creator")
    tags: List[str] = Field(default_factory=list, description="Interview tags for categorization")
    notes: Optional[str] = Field(None, max_length=1000, description="Internal notes")
    
    # Configuration
    max_questions: int = Field(default=15, ge=5, le=30, description="Maximum questions to ask")
    time_limit_minutes: int = Field(default=45, ge=15, le=120, description="Interview time limit")
    adaptive_difficulty: bool = Field(default=True, description="Whether to adjust difficulty based on performance")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        schema_extra = {
            "example": {
                "candidate_name": "John Smith",
                "candidate_email": "john.smith@email.com",
                "position": "Financial Analyst",
                "department": "Finance",
                "skill_level": "intermediate",
                "priority": "normal"
            }
        }
    
    @validator('candidate_name')
    def validate_candidate_name(cls, v):
        """Validate candidate name format"""
        if not re.match(r'^[a-zA-Z\s\-\'\.]+$', v):
            raise ValueError('Name can only contain letters, spaces, hyphens, apostrophes, and periods')
        return v.strip().title()
    
    @validator('position')
    def validate_position(cls, v):
        """Validate position format"""
        return v.strip().title()
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate and clean tags"""
        return [tag.strip().lower() for tag in v if tag.strip()]
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        """Ensure end time is after start time"""
        if v and values.get('start_time') and v < values['start_time']:
            raise ValueError('End time must be after start time')
        return v
    
    def calculate_duration(self) -> Optional[int]:
        """Calculate interview duration in minutes"""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() / 60)
        return None
    
    def get_progress_percentage(self) -> float:
        """Calculate interview progress percentage"""
        if not self.questions_asked:
            return 0.0
        return min(100.0, (len(self.questions_asked) / self.max_questions) * 100)
    
    def is_expired(self) -> bool:
        """Check if interview has expired based on time limit"""
        if not self.start_time:
            return False
        
        elapsed = datetime.utcnow() - self.start_time
        return elapsed.total_seconds() / 60 > self.time_limit_minutes

class InterviewCreate(BaseModel):
    """Model for creating new interviews"""
    candidate_name: str = Field(..., min_length=2, max_length=100)
    candidate_email: EmailStr
    position: str = Field(..., min_length=2, max_length=100)
    department: Optional[str] = Field(None, max_length=50)
    skill_level: SkillLevel = Field(default=SkillLevel.INTERMEDIATE)
    priority: InterviewPriority = Field(default=InterviewPriority.NORMAL)
    max_questions: int = Field(default=15, ge=5, le=30)
    time_limit_minutes: int = Field(default=45, ge=15, le=120)
    adaptive_difficulty: bool = Field(default=True)
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = Field(None, max_length=1000)
    created_by: Optional[str] = None
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "candidate_name": "Jane Doe",
                "candidate_email": "jane.doe@example.com",
                "position": "Data Analyst",
                "department": "Operations",
                "skill_level": "intermediate"
            }
        }

class InterviewUpdate(BaseModel):
    """Model for updating existing interviews"""
    status: Optional[InterviewStatus] = None
    overall_score: Optional[float] = Field(None, ge=0, le=100)
    category_scores: Optional[Dict[str, float]] = None
    feedback: Optional[str] = Field(None, max_length=5000)
    hire_recommendation: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None
    end_time: Optional[datetime] = None
    
    class Config:
        use_enum_values = True

class InterviewResponse(BaseModel):
    """Model for interview API responses"""
    id: str
    candidate_name: str
    candidate_email: str
    position: str
    department: Optional[str]
    status: InterviewStatus
    skill_level: SkillLevel
    priority: InterviewPriority
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration_minutes: Optional[int]
    overall_score: Optional[float]
    progress_percentage: float
    questions_completed: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class InterviewSummary(BaseModel):
    """Condensed interview summary for lists and dashboards"""
    id: str
    candidate_name: str
    candidate_email: str
    position: str
    status: InterviewStatus
    overall_score: Optional[float]
    progress_percentage: float
    created_at: datetime
    duration_minutes: Optional[int]
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class InterviewStats(BaseModel):
    """Interview statistics model"""
    total_interviews: int = 0
    completed_interviews: int = 0
    in_progress_interviews: int = 0
    pending_interviews: int = 0
    cancelled_interviews: int = 0
    average_score: float = 0.0
    average_duration_minutes: float = 0.0
    completion_rate: float = 0.0
    
    # Score distribution
    score_distribution: Dict[str, int] = Field(default_factory=dict)
    skill_level_distribution: Dict[str, int] = Field(default_factory=dict)
    position_distribution: Dict[str, int] = Field(default_factory=dict)
    
    # Time-based stats
    interviews_today: int = 0
    interviews_this_week: int = 0
    interviews_this_month: int = 0
    
    def calculate_completion_rate(self) -> float:
        """Calculate interview completion rate"""
        if self.total_interviews == 0:
            return 0.0
        return (self.completed_interviews / self.total_interviews) * 100

class InterviewFilter(BaseModel):
    """Model for filtering interviews"""
    status: Optional[InterviewStatus] = None
    skill_level: Optional[SkillLevel] = None
    priority: Optional[InterviewPriority] = None
    department: Optional[str] = None
    position: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    min_score: Optional[float] = Field(None, ge=0, le=100)
    max_score: Optional[float] = Field(None, ge=0, le=100)
    tags: Optional[List[str]] = None
    search_term: Optional[str] = None
    
    class Config:
        use_enum_values = True
