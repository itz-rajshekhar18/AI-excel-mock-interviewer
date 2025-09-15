"""
Utility modules for Excel Mock Interviewer

This package contains utility functions and classes for configuration management,
state handling, logging, validation, and common helper functions.
"""

from .config import settings, Settings
from .state_manager import state_manager, StateManager
from .logger import setup_logging, get_logger
from .helpers import (
    generate_interview_id,
    format_score,
    calculate_percentile,
    sanitize_input,
    format_duration,
    extract_excel_functions,
    generate_report_id
)
from .validators import (
    validate_email,
    validate_interview_data,
    validate_question_id,
    validate_score_range,
    sanitize_user_input
)

# Package constants
SUPPORTED_EXCEL_FUNCTIONS = [
    "SUM", "AVERAGE", "COUNT", "MIN", "MAX", "IF", "VLOOKUP", "HLOOKUP",
    "INDEX", "MATCH", "XLOOKUP", "COUNTIF", "SUMIF", "PIVOT", "CHART"
]

SKILL_LEVELS = ["beginner", "intermediate", "advanced"]
QUESTION_TYPES = ["formula", "data_analysis", "problem_solving", "scenario", "practical"]

# Export all utilities
__all__ = [
    "settings", "Settings", "state_manager", "StateManager",
    "setup_logging", "get_logger", "generate_interview_id", "format_score",
    "calculate_percentile", "sanitize_input", "format_duration",
    "extract_excel_functions", "generate_report_id", "validate_email",
    "validate_interview_data", "validate_question_id", "validate_score_range",
    "sanitize_user_input"
]
