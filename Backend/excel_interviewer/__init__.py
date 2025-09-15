"""
Excel Mock Interviewer - AI-Powered Excel Skills Assessment Platform

A comprehensive backend system for conducting automated Excel interviews using AI evaluation.
This package provides all the necessary components for managing interviews, questions, 
evaluations, and generating detailed assessment reports.
"""

# Package metadata
__version__ = "1.0.0"
__author__ = "Excel Mock Interviewer Team"
__license__ = "MIT"
__description__ = "AI-Powered Excel Skills Assessment Platform"

# Import core modules for easy access
from .models import (
    # Interview models
    Interview, InterviewStatus, SkillLevel, InterviewPriority,
    InterviewCreate, InterviewUpdate, InterviewResponse,
    
    # Question models  
    ExcelQuestion, QuestionType, QuestionDifficulty, QuestionCategory,
    QuestionResponse, QuestionRequest,
    
    # Evaluation models
    EvaluationCriteria, ResponseEvaluation, FinalAssessment,
    HireRecommendation, SkillAssessment,
    
    # Database models
    InterviewDB, QuestionDB, EvaluationDB, ResponseDB,
    init_db, get_db
)

from .services import (
    # Core services
    llm_service,
    question_bank,
    ConversationManager,
    ExcelEvaluator,
    FeedbackEngine
)

from .utils import (
    settings,
    state_manager
)

# API components
from .api import router

# Public API - what can be imported from the package
__all__ = [
    # Version info
    "__version__", "__author__", "__license__", "__description__",
    
    # Core models
    "Interview", "InterviewStatus", "SkillLevel", "InterviewPriority",
    "InterviewCreate", "InterviewUpdate", "InterviewResponse",
    "ExcelQuestion", "QuestionType", "QuestionDifficulty", "QuestionCategory",
    "QuestionResponse", "QuestionRequest",
    "EvaluationCriteria", "ResponseEvaluation", "FinalAssessment",
    "HireRecommendation", "SkillAssessment",
    
    # Database models
    "InterviewDB", "QuestionDB", "EvaluationDB", "ResponseDB",
    "init_db", "get_db",
    
    # Services
    "llm_service", "question_bank", "ConversationManager", 
    "ExcelEvaluator", "FeedbackEngine",
    
    # Utils
    "settings", "state_manager",
    
    # API
    "router"
]

# Package health check
def health_check() -> dict:
    """Perform a health check of all package components"""
    health = {
        "package": "excel_interviewer",
        "version": __version__,
        "status": "healthy",
        "components": {}
    }
    
    try:
        # Check database connection
        from .models.database import validate_database_connection
        health["components"]["database"] = "connected" if validate_database_connection() else "disconnected"
    except Exception as e:
        health["components"]["database"] = f"error: {str(e)}"
    
    try:
        # Check Redis connection  
        health["components"]["redis"] = "connected" if state_manager.redis_client else "disconnected"
    except Exception as e:
        health["components"]["redis"] = f"error: {str(e)}"
    
    try:
        # Check question bank
        health["components"]["question_bank"] = f"loaded ({len(question_bank.questions)} questions)"
    except Exception as e:
        health["components"]["question_bank"] = f"error: {str(e)}"
    
    return health

def get_package_info() -> dict:
    """Get comprehensive package information"""
    return {
        "name": "excel_interviewer",
        "version": __version__,
        "author": __author__,
        "license": __license__,
        "description": __description__,
        "features": [
            "AI-powered Excel skills assessment",
            "Adaptive interview difficulty",
            "Comprehensive evaluation reports", 
            "Real-time conversation management",
            "Question bank with 50+ questions",
            "RESTful API with OpenAPI docs"
        ]
    }
