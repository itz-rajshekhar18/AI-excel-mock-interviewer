"""
FastAPI Routes for Excel Mock Interviewer API
"""
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from excel_interviewer.models.database import get_db, InterviewDB, ResponseDB, EvaluationDB
from excel_interviewer.models.interview import InterviewCreate, InterviewUpdate, Interview, InterviewResponse
from excel_interviewer.models.question import QuestionResponse, QuestionRequest
from excel_interviewer.models.evaluation import ResponseEvaluation, EvaluationRequest

from excel_interviewer.services import (
    conversation_manager, excel_evaluator, question_bank, feedback_engine, llm_service
)
from excel_interviewer.api.dependencies import (
    get_current_interview, rate_limiter, evaluation_rate_limiter,
    validate_request_data, log_api_request, check_services_health, check_database_health
)
from excel_interviewer.api.exceptions import (
    InterviewNotFoundException, InvalidRequestException, EvaluationException,
    RateLimitExceededException
)

logger = logging.getLogger(__name__)

# Create main router
router = APIRouter()

# ===== HEALTH CHECK ROUTES =====

@router.get("/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive system health check"""
    try:
        # Check services
        services_health = await check_services_health()
        
        # Check database
        db_health = await check_database_health(db)
        
        # Overall status
        overall_status = "healthy"
        if services_health.get("services_status") != "healthy" or db_health.get("database") != "healthy":
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "services": services_health,
            "database": db_health,
            "uptime": "unknown"  # Would implement with app startup tracking
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@router.get("/metrics", tags=["Health"])
async def get_metrics(db: Session = Depends(get_db)):
    """Get system metrics and statistics"""
    try:
        # Get database counts
        stats = {
            "interviews": {
                "total": db.query(InterviewDB).count(),
                "active": db.query(InterviewDB).filter(InterviewDB.status == "in_progress").count(),
                "completed": db.query(InterviewDB).filter(InterviewDB.status == "completed").count()
            },
            "responses": db.query(ResponseDB).count(),
            "evaluations": db.query(EvaluationDB).count()
        }
        
        # Get question bank stats
        qb_stats = question_bank.get_question_statistics()
        stats["question_bank"] = qb_stats
        
        # Get LLM service stats
        llm_stats = llm_service.get_stats()
        stats["llm_service"] = llm_stats
        
        # Get evaluator stats
        eval_stats = excel_evaluator.get_evaluation_stats()
        stats["evaluator"] = eval_stats
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")

# ===== INTERVIEW MANAGEMENT ROUTES =====

@router.post("/interviews", response_model=Dict[str, Any], tags=["Interviews"])
async def create_interview(
    interview_data: InterviewCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: bool = Depends(rate_limiter)
):
    """Create a new interview session"""
    try:
        # Validate input data
        validated_data = await validate_request_data(
            interview_data.dict(),
            required_fields=["candidate_name", "candidate_email", "position"],
            optional_fields=["department", "skill_level", "max_questions", "time_limit_minutes"]
        )
        
        # Create interview in database
        db_interview = InterviewDB(
            candidate_name=validated_data["candidate_name"],
            candidate_email=validated_data["candidate_email"],
            position=validated_data["position"],
            department=validated_data.get("department"),
            skill_level=validated_data.get("skill_level", "intermediate"),
            max_questions=validated_data.get("max_questions", 15),
            time_limit_minutes=validated_data.get("time_limit_minutes", 45),
            adaptive_difficulty=validated_data.get("adaptive_difficulty", True),
            created_by=validated_data.get("created_by"),
            tags=validated_data.get("tags", []),
            notes=validated_data.get("notes")
        )
        
        db.add(db_interview)
        db.commit()
        db.refresh(db_interview)
        
        # Convert to Pydantic model
        interview = Interview(
            id=str(db_interview.id),
            candidate_name=db_interview.candidate_name,
            candidate_email=db_interview.candidate_email,
            position=db_interview.position,
            department=db_interview.department,
            skill_level=db_interview.skill_level,
            max_questions=db_interview.max_questions,
            time_limit_minutes=db_interview.time_limit_minutes,
            created_at=db_interview.created_at
        )
        
        # Start interview conversation
        conversation_result = await conversation_manager.start_interview(interview)
        
        # Log the API request
        background_tasks.add_task(
            log_api_request,
            request,
            "create_interview",
            interview_id=str(db_interview.id)
        )
        
        if conversation_result["status"] == "success":
            return {
                "interview_id": str(db_interview.id),
                "status": "created",
                "message": conversation_result["message"],
                "first_question": conversation_result["question"],
                "interview_details": {
                    "candidate_name": interview.candidate_name,
                    "position": interview.position,
                    "skill_level": interview.skill_level,
                    "max_questions": interview.max_questions,
                    "time_limit_minutes": interview.time_limit_minutes
                }
            }
        else:
            raise EvaluationException(conversation_result.get("message", "Failed to start interview"))
            
    except Exception as e:
        logger.error(f"Error creating interview: {e}")
        if isinstance(e, (InvalidRequestException, EvaluationException)):
            raise
        raise HTTPException(status_code=500, detail="Failed to create interview")

@router.get("/interviews/{interview_id}", response_model=Dict[str, Any], tags=["Interviews"])
async def get_interview(
    interview_id: str,
    request: Request,
    db: Session = Depends(get_db),
    _: bool = Depends(rate_limiter)
):
    """Get interview details and current status"""
    try:
        # Get interview from database
        interview = await get_current_interview(interview_id, db)
        
        # Get current conversation status
        status_result = await conversation_manager.get_interview_status(interview_id)
        
        return {
            "interview_id": interview_id,
            "candidate_name": interview.candidate_name,
            "position": interview.position,
            "status": interview.status,
            "created_at": interview.created_at.isoformat(),
            "conversation_status": status_result,
            "details": interview.dict()
        }
        
    except InterviewNotFoundException:
        raise
    except Exception as e:
        logger.error(f"Error getting interview {interview_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve interview")

@router.post("/interviews/{interview_id}/responses", response_model=Dict[str, Any], tags=["Interviews"])
async def submit_response(
    interview_id: str,
    response_data: Dict[str, Any],
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: bool = Depends(evaluation_rate_limiter)
):
    """Submit candidate response to current question"""
    try:
        # Validate interview exists
        await get_current_interview(interview_id, db)
        
        # Validate response data
        validated_data = await validate_request_data(
            response_data,
            required_fields=["candidate_response"],
            optional_fields=["response_time_seconds", "confidence_level"]
        )
        
        # Process the response
        result = await conversation_manager.process_response(
            interview_id=interview_id,
            candidate_response=validated_data["candidate_response"],
            response_time_seconds=validated_data.get("response_time_seconds", 0)
        )
        
        # Store response in database
        if result["status"] in ["continue", "completed"]:
            response_record = ResponseDB(
                interview_id=interview_id,
                question_id=result.get("evaluation", {}).get("question_id"),
                candidate_response=validated_data["candidate_response"],
                response_time_seconds=validated_data.get("response_time_seconds"),
                confidence_level=validated_data.get("confidence_level"),
                response_length=len(validated_data["candidate_response"]),
                word_count=len(validated_data["candidate_response"].split())
            )
            
            db.add(response_record)
            db.commit()
        
        # Log the API request
        background_tasks.add_task(
            log_api_request,
            request,
            "submit_response",
            interview_id=interview_id,
            extra_data={"response_length": len(validated_data["candidate_response"])}
        )
        
        return result
        
    except InterviewNotFoundException:
        raise
    except Exception as e:
        logger.error(f"Error processing response for interview {interview_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process response")

@router.get("/interviews/{interview_id}/assessment", response_model=Dict[str, Any], tags=["Interviews"])
async def get_final_assessment(
    interview_id: str,
    request: Request,
    db: Session = Depends(get_db),
    _: bool = Depends(rate_limiter)
):
    """Get final assessment for completed interview"""
    try:
        # Verify interview exists
        interview = await get_current_interview(interview_id, db)
        
        if interview.status != "completed":
            raise InvalidRequestException("Interview has not been completed yet")
        
        # Get interview state to retrieve responses
        from excel_interviewer.utils.state_manager import state_manager
        state = await state_manager.get_interview_state(interview_id)
        
        if not state or "final_assessment" not in state:
            # Generate assessment if not exists
            responses = state.get("responses", []) if state else []
            final_assessment = await feedback_engine.generate_final_assessment(interview_id, responses)
        else:
            final_assessment = state["final_assessment"]
        
        return {
            "interview_id": interview_id,
            "assessment": final_assessment,
            "candidate_info": {
                "name": interview.candidate_name,
                "position": interview.position,
                "interview_date": interview.created_at.isoformat()
            }
        }
        
    except (InterviewNotFoundException, InvalidRequestException):
        raise
    except Exception as e:
        logger.error(f"Error getting assessment for interview {interview_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve assessment")

# ===== QUESTION MANAGEMENT ROUTES =====

@router.get("/questions", response_model=Dict[str, Any], tags=["Questions"])
async def get_questions(
    difficulty: Optional[str] = None,
    question_type: Optional[str] = None,
    category: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    _: bool = Depends(rate_limiter)
):
    """Get available questions with optional filtering"""
    try:
        # Get questions from question bank
        all_questions = question_bank.questions
        
        # Apply filters
        filtered_questions = []
        for question in all_questions:
            if not question.is_active:
                continue
                
            if difficulty and question.difficulty != difficulty:
                continue
                
            if question_type and question.question_type != question_type:
                continue
                
            if category and question.category != category:
                continue
                
            filtered_questions.append(question)
        
        # Pagination
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        page_questions = filtered_questions[start_idx:end_idx]
        
        # Convert to dict format
        questions_data = []
        for q in page_questions:
            questions_data.append({
                "id": q.id,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "difficulty": q.difficulty,
                "category": q.category,
                "expected_keywords": q.expected_keywords,
                "times_used": q.times_used,
                "average_score": q.average_score
            })
        
        return {
            "questions": questions_data,
            "pagination": {
                "page": page,
                "size": size,
                "total": len(filtered_questions),
                "pages": (len(filtered_questions) + size - 1) // size
            },
            "filters": {
                "difficulty": difficulty,
                "question_type": question_type,
                "category": category
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting questions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve questions")

@router.get("/questions/statistics", response_model=Dict[str, Any], tags=["Questions"])
async def get_question_statistics(
    db: Session = Depends(get_db),
    _: bool = Depends(rate_limiter)
):
    """Get question bank statistics and usage data"""
    try:
        stats = question_bank.get_question_statistics()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "question_bank_stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting question statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

# ===== EVALUATION ROUTES =====

@router.post("/evaluate", response_model=Dict[str, Any], tags=["Evaluation"])
async def evaluate_response(
    evaluation_request: EvaluationRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    _: bool = Depends(evaluation_rate_limiter)
):
    """Standalone response evaluation endpoint"""
    try:
        # Evaluate the response
        evaluation = await excel_evaluator.evaluate_response(
            question_text=evaluation_request.question_text,
            candidate_response=evaluation_request.candidate_response,
            difficulty=evaluation_request.difficulty_level,
            question_type=evaluation_request.question_type
        )
        
        # Log the API request
        background_tasks.add_task(
            log_api_request,
            request,
            "evaluate_response",
            extra_data={
                "difficulty": evaluation_request.difficulty_level,
                "question_type": evaluation_request.question_type
            }
        )
        
        return {
            "evaluation": evaluation,
            "request_metadata": {
                "difficulty_level": evaluation_request.difficulty_level,
                "question_type": evaluation_request.question_type,
                "evaluation_timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in standalone evaluation: {e}")
        raise EvaluationException(f"Evaluation failed: {str(e)}")

# Export router
__all__ = ["router"]
