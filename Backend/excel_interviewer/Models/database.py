"""
Database configuration and ORM models for Excel Mock Interviewer

This module contains SQLAlchemy models and database setup for persistent storage
of interviews, questions, evaluations, and responses.
"""
from sqlalchemy import (
    create_engine, Column, String, DateTime, Float, Text, JSON, 
    Boolean, Integer, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from datetime import datetime, timedelta
import logging
from typing import Optional, Generator

# Import settings with fallback
try:
    from excel_interviewer.utils.config import settings
except ImportError:
    class MockSettings:
        database_url = "postgresql://user:password@localhost/excel_interviewer"
        debug = False
    settings = MockSettings()

logger = logging.getLogger(__name__)

# Database setup
engine = create_engine(
    settings.database_url, 
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=300
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class InterviewDB(Base):
    """SQLAlchemy model for interviews table"""
    __tablename__ = "interviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    candidate_name = Column(String(255), nullable=False, index=True)
    candidate_email = Column(String(255), nullable=False, index=True)
    position = Column(String(255), nullable=False, index=True)
    department = Column(String(100), nullable=True, index=True)
    status = Column(String(50), default="pending", nullable=False, index=True)
    skill_level = Column(String(50), default="intermediate", nullable=False, index=True)
    priority = Column(String(20), default="normal", nullable=False)
    max_questions = Column(Integer, default=15, nullable=False)
    time_limit_minutes = Column(Integer, default=45, nullable=False)
    adaptive_difficulty = Column(Boolean, default=True, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    questions_asked = Column(JSON, default=list, nullable=False)
    current_question_id = Column(String(100), nullable=True)
    overall_score = Column(Float, nullable=True, index=True)
    category_scores = Column(JSON, default=dict, nullable=False)
    feedback = Column(Text, nullable=True)
    hire_recommendation = Column(String(50), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(255), nullable=True)
    tags = Column(JSON, default=list, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Relationships
    responses = relationship("ResponseDB", back_populates="interview", cascade="all, delete-orphan")
    evaluations = relationship("EvaluationDB", back_populates="interview", cascade="all, delete-orphan")

class QuestionDB(Base):
    """SQLAlchemy model for questions table"""
    __tablename__ = "questions"
    
    id = Column(String(100), primary_key=True, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False, index=True)
    difficulty = Column(String(50), nullable=False, index=True)
    category = Column(String(100), nullable=True, index=True)
    expected_keywords = Column(JSON, default=list, nullable=False)
    sample_answer = Column(Text, nullable=True)
    scoring_criteria = Column(JSON, default=dict, nullable=False)
    follow_up_questions = Column(JSON, default=list, nullable=False)
    times_used = Column(Integer, default=0, nullable=False)
    average_score = Column(Float, nullable=True)
    pass_rate = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    version = Column(String(20), default="1.0", nullable=False)
    
    # Relationships
    responses = relationship("ResponseDB", back_populates="question")

class ResponseDB(Base):
    """SQLAlchemy model for candidate responses"""
    __tablename__ = "responses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interviews.id"), nullable=False, index=True)
    question_id = Column(String(100), ForeignKey("questions.id"), nullable=False, index=True)
    candidate_response = Column(Text, nullable=False)
    response_time_seconds = Column(Float, nullable=True)
    confidence_level = Column(Integer, nullable=True)
    response_length = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    keyword_matches = Column(JSON, default=list, nullable=False)
    excel_terms_used = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    interview = relationship("InterviewDB", back_populates="responses")
    question = relationship("QuestionDB", back_populates="responses")
    evaluation = relationship("EvaluationDB", back_populates="response", uselist=False)

class EvaluationDB(Base):
    """SQLAlchemy model for response evaluations"""
    __tablename__ = "evaluations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interviews.id"), nullable=False, index=True)
    response_id = Column(UUID(as_uuid=True), ForeignKey("responses.id"), nullable=False, index=True)
    question_id = Column(String(100), ForeignKey("questions.id"), nullable=False, index=True)
    technical_accuracy = Column(Float, default=0.0, nullable=False)
    communication_clarity = Column(Float, default=0.0, nullable=False)
    problem_solving_approach = Column(Float, default=0.0, nullable=False)
    completeness = Column(Float, default=0.0, nullable=False)
    efficiency = Column(Float, default=0.0, nullable=False)
    overall_score = Column(Float, nullable=False, index=True)
    feedback = Column(Text, nullable=True)
    strengths = Column(JSON, default=list, nullable=False)
    areas_for_improvement = Column(JSON, default=list, nullable=False)
    next_difficulty_level = Column(String(50), nullable=True)
    confidence_level = Column(Float, default=0.8, nullable=False)
    evaluation_method = Column(String(50), default="ai_llm", nullable=False)
    evaluator_version = Column(String(20), default="1.0.0", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    evaluation_time_seconds = Column(Float, nullable=True)
    
    # Relationships
    interview = relationship("InterviewDB", back_populates="evaluations")
    response = relationship("ResponseDB", back_populates="evaluation")

class AssessmentDB(Base):
    """SQLAlchemy model for final assessments"""
    __tablename__ = "assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interviews.id"), nullable=False, unique=True, index=True)
    overall_score = Column(Float, nullable=False, index=True)
    skill_level_assessment = Column(String(50), nullable=False, index=True)
    hire_recommendation = Column(String(50), nullable=False, index=True)
    category_scores = Column(JSON, default=dict, nullable=False)
    dimension_scores = Column(JSON, default=dict, nullable=False)
    detailed_feedback = Column(Text, nullable=False)
    executive_summary = Column(Text, nullable=False)
    recommendations = Column(JSON, default=list, nullable=False)
    strengths_summary = Column(JSON, default=list, nullable=False)
    improvement_areas = Column(JSON, default=list, nullable=False)
    statistics = Column(JSON, default=dict, nullable=False)
    benchmarking = Column(JSON, default=dict, nullable=False)
    assessment_version = Column(String(20), default="1.0.0", nullable=False)
    total_questions = Column(Integer, default=0, nullable=False)
    interview_duration_minutes = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class SystemLogDB(Base):
    """SQLAlchemy model for system logs and audit trail"""
    __tablename__ = "system_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    level = Column(String(20), nullable=False, index=True)
    message = Column(Text, nullable=False)
    module = Column(String(100), nullable=False, index=True)
    function = Column(String(100), nullable=True)
    interview_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    extra_data = Column(JSON, default=dict, nullable=False)
    stack_trace = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

# Database functions
async def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

async def drop_tables():
    """Drop all database tables"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
    except Exception as e:
        logger.error(f"Error dropping database tables: {e}")
        raise

def get_db() -> Generator[Session, None, None]:
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_test_db_session() -> Session:
    """Create database session for testing"""
    return SessionLocal()

class DatabaseManager:
    """Database management utilities"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def get_table_counts(self) -> dict:
        """Get row counts for all tables"""
        counts = {}
        with self.get_session() as session:
            try:
                counts["interviews"] = session.query(InterviewDB).count()
                counts["questions"] = session.query(QuestionDB).count()
                counts["responses"] = session.query(ResponseDB).count()
                counts["evaluations"] = session.query(EvaluationDB).count()
                counts["assessments"] = session.query(AssessmentDB).count()
                counts["system_logs"] = session.query(SystemLogDB).count()
            except Exception as e:
                logger.error(f"Error getting table counts: {e}")
        return counts

# Global database manager instance
db_manager = DatabaseManager()

def validate_database_connection():
    """Validate database connection on startup"""
    try:
        with SessionLocal() as session:
            session.execute("SELECT 1")
        logger.info("Database connection validated successfully")
        return True
    except Exception as e:
        logger.error(f"Database connection validation failed: {e}")
        return False
