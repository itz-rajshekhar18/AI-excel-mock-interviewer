"""
Evaluation data models for Excel Mock Interviewer

This module defines all Pydantic models related to response evaluation,
scoring criteria, and assessment results.
"""
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import uuid
import statistics

class EvaluationDimension(str, Enum):
    """Evaluation dimensions for Excel skills assessment"""
    TECHNICAL_ACCURACY = "technical_accuracy"
    COMMUNICATION_CLARITY = "communication_clarity"
    PROBLEM_SOLVING_APPROACH = "problem_solving_approach"
    COMPLETENESS = "completeness"
    EFFICIENCY = "efficiency"

class HireRecommendation(str, Enum):
    """Hiring recommendation levels"""
    STRONG_HIRE = "strong_hire"
    HIRE = "hire"
    CONDITIONAL_HIRE = "conditional_hire"
    NO_HIRE = "no_hire"
    STRONG_NO_HIRE = "strong_no_hire"

class SkillAssessment(str, Enum):
    """Overall skill assessment levels"""
    EXPERT = "expert"
    ADVANCED = "advanced"
    INTERMEDIATE = "intermediate"
    BASIC = "basic"
    BEGINNER = "beginner"
    INSUFFICIENT_DATA = "insufficient_data"

class EvaluationCriteria(BaseModel):
    """Individual evaluation criteria scores"""
    technical_accuracy: float = Field(..., ge=0, le=100, description="Technical correctness of Excel knowledge")
    communication_clarity: float = Field(..., ge=0, le=100, description="Clarity of explanation and communication")
    problem_solving_approach: float = Field(..., ge=0, le=100, description="Logical approach to problem solving")
    completeness: float = Field(..., ge=0, le=100, description="Completeness of the response")
    efficiency: float = Field(..., ge=0, le=100, description="Efficiency of proposed Excel solution")
    
    def calculate_overall_score(self) -> float:
        """Calculate weighted overall score"""
        weights = {
            "technical_accuracy": 0.35,
            "communication_clarity": 0.15,
            "problem_solving_approach": 0.25,
            "completeness": 0.15,
            "efficiency": 0.10
        }
        
        weighted_sum = (
            self.technical_accuracy * weights["technical_accuracy"] +
            self.communication_clarity * weights["communication_clarity"] +
            self.problem_solving_approach * weights["problem_solving_approach"] +
            self.completeness * weights["completeness"] +
            self.efficiency * weights["efficiency"]
        )
        
        return round(weighted_sum, 2)

class ResponseEvaluation(BaseModel):
    """Complete evaluation of a candidate's response"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    interview_id: str = Field(..., description="Associated interview ID")
    question_id: str = Field(..., description="Question being evaluated")
    candidate_response: str = Field(..., min_length=1, max_length=10000, description="Candidate's response text")
    
    # Core evaluation scores
    scores: EvaluationCriteria = Field(..., description="Individual criterion scores")
    overall_score: float = Field(..., ge=0, le=100, description="Overall weighted score")
    
    # Detailed feedback
    feedback: str = Field(..., min_length=10, max_length=2000, description="Detailed evaluation feedback")
    strengths: List[str] = Field(default_factory=list, description="Identified strengths")
    areas_for_improvement: List[str] = Field(default_factory=list, description="Areas needing improvement")
    
    # Adaptive assessment
    next_difficulty_level: str = Field(..., description="Recommended next difficulty level")
    confidence_level: float = Field(default=0.8, ge=0.0, le=1.0, description="AI confidence in evaluation")
    
    # Metadata
    evaluation_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When evaluation was performed")
    evaluation_method: str = Field(default="ai_llm", description="Method used for evaluation")
    evaluator_version: str = Field(default="1.0.0", description="Version of evaluation system")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class FinalAssessment(BaseModel):
    """Comprehensive final assessment for completed interview"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    interview_id: str = Field(..., description="Associated interview ID")
    
    # Overall results
    overall_score: float = Field(..., ge=0, le=100, description="Final overall score")
    skill_level_assessment: SkillAssessment = Field(..., description="Assessed skill level")
    hire_recommendation: HireRecommendation = Field(..., description="Hiring recommendation")
    
    # Detailed scoring
    category_scores: Dict[str, float] = Field(default_factory=dict, description="Scores by Excel skill category")
    dimension_scores: Dict[str, float] = Field(default_factory=dict, description="Scores by evaluation dimension")
    
    # Comprehensive feedback
    detailed_feedback: str = Field(..., min_length=50, max_length=5000, description="Comprehensive assessment feedback")
    executive_summary: str = Field(..., min_length=20, max_length=500, description="Brief executive summary")
    recommendations: List[str] = Field(default_factory=list, description="Development recommendations")
    
    # Performance analysis
    strengths_summary: List[str] = Field(default_factory=list, description="Key strengths identified")
    improvement_areas: List[str] = Field(default_factory=list, description="Priority improvement areas")
    
    # Statistical analysis
    statistics: Dict[str, Any] = Field(default_factory=dict, description="Performance statistics")
    
    # Metadata
    assessment_date: datetime = Field(default_factory=datetime.utcnow, description="Assessment completion date")
    assessment_version: str = Field(default="1.0.0", description="Assessment system version")
    total_questions: int = Field(default=0, description="Total questions answered")
    interview_duration_minutes: Optional[int] = Field(None, description="Total interview duration")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class EvaluationRequest(BaseModel):
    """Request model for evaluation API"""
    question_text: str = Field(..., min_length=5, max_length=2000)
    candidate_response: str = Field(..., min_length=1, max_length=10000)
    difficulty_level: str = Field(default="intermediate")
    question_type: str = Field(default="general")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for evaluation")

class EvaluationSummary(BaseModel):
    """Summary model for evaluation results"""
    evaluation_id: str
    overall_score: float
    performance_level: str
    key_strengths: List[str]
    main_improvements: List[str]
    next_difficulty: str
    evaluation_date: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
