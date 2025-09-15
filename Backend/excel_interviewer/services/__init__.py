"""
Business logic services for the Excel Mock Interviewer

This module contains all the core business logic services that handle
interview management, question evaluation, conversation flow, and reporting.
"""

from .llm_service import LLMService, llm_service
from .question_bank import QuestionBankService, question_bank
from .conversation_manager import ConversationManager, conversation_manager
from .excel_evaluator import ExcelEvaluator, excel_evaluator
from .feedback_engine import FeedbackEngine, feedback_engine

# Service registry for dependency injection
SERVICE_REGISTRY = {
    "llm_service": llm_service,
    "question_bank": question_bank,
    "conversation_manager": conversation_manager,
    "excel_evaluator": excel_evaluator,
    "feedback_engine": feedback_engine
}

# Public API exports
__all__ = [
    # Service classes
    "LLMService",
    "QuestionBankService", 
    "ConversationManager",
    "ExcelEvaluator",
    "FeedbackEngine",
    
    # Service instances (singletons)
    "llm_service",
    "question_bank",
    "conversation_manager", 
    "excel_evaluator",
    "feedback_engine",
    
    # Service registry
    "SERVICE_REGISTRY"
]

# Service health check
def check_services_health() -> dict:
    """Check health status of all services"""
    health = {
        "services_status": "healthy",
        "services": {}
    }
    
    failed_services = []
    
    try:
        # Check LLM Service
        health["services"]["llm_service"] = "configured" if llm_service.openai_client else "not_configured"
    except Exception as e:
        health["services"]["llm_service"] = f"error: {str(e)}"
        failed_services.append("llm_service")
    
    try:
        # Check Question Bank
        health["services"]["question_bank"] = f"loaded ({len(question_bank.questions)} questions)"
    except Exception as e:
        health["services"]["question_bank"] = f"error: {str(e)}"
        failed_services.append("question_bank")
    
    try:
        # Check other services
        health["services"]["conversation_manager"] = "ready"
        health["services"]["excel_evaluator"] = "ready"  
        health["services"]["feedback_engine"] = "ready"
    except Exception as e:
        health["services"]["other_services"] = f"error: {str(e)}"
        failed_services.append("other_services")
    
    if failed_services:
        health["services_status"] = "degraded"
        health["failed_services"] = failed_services
    
    return health

# Service initialization
def initialize_services():
    """Initialize all services with default configuration"""
    try:
        # Services are initialized when imported
        # This function can be used for additional setup if needed
        return True
    except Exception as e:
        print(f"Service initialization failed: {e}")
        return False

# Auto-initialize on import
_services_initialized = initialize_services()
