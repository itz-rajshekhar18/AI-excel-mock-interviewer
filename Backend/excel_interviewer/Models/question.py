"""
Question data models for Excel Mock Interviewer

This module defines all Pydantic models related to Excel questions including
question types, difficulty levels, and response handling.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid
import re

class QuestionType(str, Enum):
    """Question type enumeration"""
    FORMULA = "formula"
    DATA_ANALYSIS = "data_analysis"
    PROBLEM_SOLVING = "problem_solving"
    SCENARIO = "scenario"
    PRACTICAL = "practical"

class QuestionDifficulty(str, Enum):
    """Question difficulty levels"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class QuestionCategory(str, Enum):
    """Question categories for Excel skills"""
    BASIC_FUNCTIONS = "basic_functions"
    ADVANCED_FUNCTIONS = "advanced_functions"
    DATA_MANIPULATION = "data_manipulation"
    PIVOT_TABLES = "pivot_tables"
    CHARTS_VISUALIZATION = "charts_visualization"
    CONDITIONAL_LOGIC = "conditional_logic"
    LOOKUP_FUNCTIONS = "lookup_functions"
    STATISTICAL_ANALYSIS = "statistical_analysis"
    FINANCIAL_MODELING = "financial_modeling"
    AUTOMATION_MACROS = "automation_macros"

class ExcelQuestion(BaseModel):
    """Excel question model with comprehensive metadata"""
    id: str = Field(..., min_length=1, description="Unique question identifier")
    question_text: str = Field(..., min_length=10, max_length=2000, description="The question text")
    question_type: QuestionType = Field(..., description="Type of Excel question")
    difficulty: QuestionDifficulty = Field(..., description="Question difficulty level")
    category: Optional[QuestionCategory] = Field(None, description="Excel skill category")
    
    # Question content and guidance
    expected_keywords: List[str] = Field(default_factory=list, description="Expected keywords in responses")
    sample_answer: Optional[str] = Field(None, max_length=3000, description="Sample correct answer")
    scoring_criteria: Dict[str, float] = Field(default_factory=dict, description="Scoring weights for evaluation")
    follow_up_questions: List[str] = Field(default_factory=list, description="Potential follow-up questions")
    
    # Question metadata
    tags: List[str] = Field(default_factory=list, description="Question tags for categorization")
    prerequisites: List[str] = Field(default_factory=list, description="Required knowledge prerequisites")
    learning_objectives: List[str] = Field(default_factory=list, description="What this question tests")
    
    # Usage statistics
    times_used: int = Field(default=0, ge=0, description="Number of times question was used")
    average_score: Optional[float] = Field(None, ge=0, le=100, description="Average score for this question")
    pass_rate: Optional[float] = Field(None, ge=0, le=100, description="Percentage of candidates who passed")
    average_response_time: Optional[float] = Field(None, ge=0, description="Average response time in seconds")
    
    # Question management
    is_active: bool = Field(default=True, description="Whether question is active")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Question creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Question creator")
    version: str = Field(default="1.0", description="Question version")
    
    # Additional configuration
    time_limit_seconds: Optional[int] = Field(None, ge=30, le=1800, description="Time limit for answering")
    hints: List[str] = Field(default_factory=list, description="Hints that can be provided")
    difficulty_weight: float = Field(default=1.0, ge=0.1, le=3.0, description="Weight multiplier for difficulty")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        schema_extra = {
            "example": {
                "id": "basic_001",
                "question_text": "How would you calculate the sum of values in cells A1 to A10?",
                "question_type": "formula",
                "difficulty": "basic",
                "category": "basic_functions",
                "expected_keywords": ["SUM", "formula", "range"]
            }
        }
    
    @validator('id')
    def validate_question_id(cls, v):
        """Validate question ID format"""
        if not re.match(r'^(basic|inter|adv)_\d{3}$', v):
            raise ValueError('Question ID must follow format: basic_001, inter_002, adv_003')
        return v.lower()
    
    @validator('expected_keywords')
    def validate_keywords(cls, v):
        """Clean and validate keywords"""
        return [keyword.strip().upper() for keyword in v if keyword.strip()]
    
    @validator('tags') 
    def validate_tags(cls, v):
        """Clean and validate tags"""
        return [tag.strip().lower() for tag in v if tag.strip()]
    
    @validator('scoring_criteria')
    def validate_scoring_criteria(cls, v):
        """Validate scoring criteria weights sum to 1.0"""
        if v and sum(v.values()) > 1.1:  # Allow small tolerance
            raise ValueError('Scoring criteria weights should not exceed 1.0')
        return v
    
    def get_complexity_score(self) -> float:
        """Calculate complexity score based on difficulty and category"""
        difficulty_scores = {
            QuestionDifficulty.BASIC: 1.0,
            QuestionDifficulty.INTERMEDIATE: 2.0, 
            QuestionDifficulty.ADVANCED: 3.0
        }
        
        category_multipliers = {
            QuestionCategory.BASIC_FUNCTIONS: 1.0,
            QuestionCategory.ADVANCED_FUNCTIONS: 1.5,
            QuestionCategory.DATA_MANIPULATION: 1.3,
            QuestionCategory.PIVOT_TABLES: 1.4,
            QuestionCategory.CHARTS_VISUALIZATION: 1.2,
            QuestionCategory.CONDITIONAL_LOGIC: 1.6,
            QuestionCategory.LOOKUP_FUNCTIONS: 1.4,
            QuestionCategory.STATISTICAL_ANALYSIS: 1.8,
            QuestionCategory.FINANCIAL_MODELING: 2.0,
            QuestionCategory.AUTOMATION_MACROS: 2.2
        }
        
        base_score = difficulty_scores.get(self.difficulty, 1.0)
        multiplier = category_multipliers.get(self.category, 1.0) if self.category else 1.0
        
        return base_score * multiplier * self.difficulty_weight
    
    def is_suitable_for_level(self, skill_level: str) -> bool:
        """Check if question is suitable for given skill level"""
        level_mapping = {
            "beginner": [QuestionDifficulty.BASIC],
            "intermediate": [QuestionDifficulty.BASIC, QuestionDifficulty.INTERMEDIATE],
            "advanced": [QuestionDifficulty.BASIC, QuestionDifficulty.INTERMEDIATE, QuestionDifficulty.ADVANCED]
        }
        
        suitable_difficulties = level_mapping.get(skill_level.lower(), [])
        return self.difficulty in suitable_difficulties
    
    def update_usage_stats(self, score: float, response_time: float):
        """Update question usage statistics"""
        self.times_used += 1
        
        # Update average score
        if self.average_score is None:
            self.average_score = score
        else:
            total_score = self.average_score * (self.times_used - 1) + score
            self.average_score = total_score / self.times_used
        
        # Update average response time
        if self.average_response_time is None:
            self.average_response_time = response_time
        else:
            total_time = self.average_response_time * (self.times_used - 1) + response_time
            self.average_response_time = total_time / self.times_used
        
        # Update pass rate (assuming 60% is passing)
        passing_threshold = 60.0
        if score >= passing_threshold:
            if self.pass_rate is None:
                self.pass_rate = 100.0
            else:
                # Calculate new pass rate
                previous_passes = (self.pass_rate / 100.0) * (self.times_used - 1)
                new_passes = previous_passes + 1
                self.pass_rate = (new_passes / self.times_used) * 100
        else:
            if self.pass_rate is None:
                self.pass_rate = 0.0
            else:
                # Calculate new pass rate (no new pass)
                previous_passes = (self.pass_rate / 100.0) * (self.times_used - 1)
                self.pass_rate = (previous_passes / self.times_used) * 100
        
        self.updated_at = datetime.utcnow()

class QuestionResponse(BaseModel):
    """Candidate response to a question"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    question_id: str = Field(..., description="ID of the question being answered")
    interview_id: str = Field(..., description="ID of the interview session")
    candidate_response: str = Field(..., min_length=1, max_length=10000, description="Candidate's response text")
    
    # Response metadata
    response_time_seconds: Optional[float] = Field(None, ge=0, description="Time taken to respond")
    confidence_level: Optional[int] = Field(None, ge=1, le=5, description="Candidate's confidence level (1-5)")
    needs_clarification: bool = Field(default=False, description="Whether response needs clarification")
    
    # Response analysis (auto-calculated)
    response_length: int = Field(default=0, ge=0, description="Length of response in characters")
    word_count: int = Field(default=0, ge=0, description="Number of words in response")
    keyword_matches: List[str] = Field(default_factory=list, description="Matched expected keywords")
    excel_terms_used: List[str] = Field(default_factory=list, description="Excel terms identified in response")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Response creation timestamp")
    submitted_at: Optional[datetime] = Field(None, description="Response submission timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    @validator('response_length', pre=True, always=True)
    def calculate_response_length(cls, v, values):
        """Automatically calculate response length"""
        response = values.get('candidate_response', '')
        return len(response)
    
    @validator('word_count', pre=True, always=True)
    def calculate_word_count(cls, v, values):
        """Automatically calculate word count"""
        response = values.get('candidate_response', '')
        return len(response.split())
    
    def analyze_excel_terms(self) -> List[str]:
        """Analyze and extract Excel terms from response"""
        excel_terms = [
            'SUM', 'AVERAGE', 'COUNT', 'MIN', 'MAX', 'IF', 'VLOOKUP', 'HLOOKUP',
            'INDEX', 'MATCH', 'CONCATENATE', 'LEFT', 'RIGHT', 'MID', 'LEN',
            'TRIM', 'UPPER', 'LOWER', 'PROPER', 'SUBSTITUTE', 'FIND', 'SEARCH',
            'PIVOT', 'CHART', 'GRAPH', 'FILTER', 'SORT', 'CONDITIONAL', 'FORMAT',
            'FORMULA', 'FUNCTION', 'CELL', 'RANGE', 'REFERENCE', 'ABSOLUTE', 'RELATIVE',
            'XLOOKUP', 'COUNTIF', 'SUMIF', 'IFERROR', 'INDIRECT', 'OFFSET'
        ]
        
        response_upper = self.candidate_response.upper()
        found_terms = [term for term in excel_terms if term in response_upper]
        return list(set(found_terms))  # Remove duplicates

class QuestionRequest(BaseModel):
    """Request model for getting questions"""
    interview_id: str = Field(..., description="Interview session ID")
    difficulty: Optional[QuestionDifficulty] = Field(None, description="Requested difficulty level")
    question_type: Optional[QuestionType] = Field(None, description="Requested question type")
    category: Optional[QuestionCategory] = Field(None, description="Requested question category")
    exclude_question_ids: List[str] = Field(default_factory=list, description="Questions to exclude")
    include_inactive: bool = Field(default=False, description="Whether to include inactive questions")
    
    class Config:
        use_enum_values = True

class QuestionCreate(BaseModel):
    """Model for creating new questions"""
    id: str = Field(..., description="Unique question identifier")
    question_text: str = Field(..., min_length=10, max_length=2000)
    question_type: QuestionType
    difficulty: QuestionDifficulty  
    category: Optional[QuestionCategory] = None
    expected_keywords: List[str] = Field(default_factory=list)
    sample_answer: Optional[str] = Field(None, max_length=3000)
    scoring_criteria: Dict[str, float] = Field(default_factory=dict)
    follow_up_questions: List[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True

class QuestionUpdate(BaseModel):
    """Model for updating existing questions"""
    question_text: Optional[str] = Field(None, min_length=10, max_length=2000)
    question_type: Optional[QuestionType] = None
    difficulty: Optional[QuestionDifficulty] = None
    category: Optional[QuestionCategory] = None
    is_active: Optional[bool] = None
    
    class Config:
        use_enum_values = True

class QuestionStats(BaseModel):
    """Question usage and performance statistics"""
    question_id: str
    times_used: int = 0
    average_score: Optional[float] = None
    pass_rate: Optional[float] = None
    average_response_time: Optional[float] = None
    total_responses: int = 0
    score_distribution: Dict[str, int] = Field(default_factory=dict)

# Utility functions
def validate_question_id_format(question_id: str) -> bool:
    """Validate question ID format"""
    pattern = r'^(basic|inter|adv)_\d{3}$'
    return bool(re.match(pattern, question_id))

def generate_question_id(difficulty: QuestionDifficulty, sequence: int) -> str:
    """Generate a properly formatted question ID"""
    difficulty_prefix = {
        QuestionDifficulty.BASIC: "basic",
        QuestionDifficulty.INTERMEDIATE: "inter", 
        QuestionDifficulty.ADVANCED: "adv"
    }
    
    prefix = difficulty_prefix.get(difficulty, "basic")
    return f"{prefix}_{sequence:03d}"
