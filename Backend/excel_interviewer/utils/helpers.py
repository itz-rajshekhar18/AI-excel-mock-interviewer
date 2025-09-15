"""
Helper utilities for Excel Mock Interviewer
"""
import uuid
import re
import random
import string
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import math

def generate_interview_id() -> str:
    """Generate a unique interview ID"""
    return str(uuid.uuid4())

def generate_report_id() -> str:
    """Generate a unique report ID"""
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"RPT-{timestamp}-{random_suffix}"

def format_score(score: Union[int, float], decimal_places: int = 2) -> str:
    """Format score with proper decimal places"""
    if not isinstance(score, (int, float)):
        return "0.00"
    score = max(0, min(100, score))
    return f"{score:.{decimal_places}f}"

def calculate_percentile(score: float, all_scores: List[float]) -> int:
    """Calculate percentile rank for a score"""
    if not all_scores:
        return 50
    
    valid_scores = [s for s in all_scores if s is not None]
    if not valid_scores:
        return 50
    
    valid_scores.sort()
    below_count = sum(1 for s in valid_scores if s < score)
    equal_count = sum(1 for s in valid_scores if s == score)
    
    percentile = (below_count + 0.5 * equal_count) / len(valid_scores) * 100
    return max(1, min(99, int(round(percentile))))

def format_duration(seconds: Union[int, float]) -> str:
    """Format duration in seconds to human-readable format"""
    if not isinstance(seconds, (int, float)) or seconds < 0:
        return "0s"
    
    seconds = int(seconds)
    
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds}s" if remaining_seconds else f"{minutes}m"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        return f"{hours}h {remaining_minutes}m" if remaining_minutes else f"{hours}h"

def extract_excel_functions(text: str) -> List[str]:
    """Extract Excel function names from text"""
    excel_functions = [
        'SUM', 'AVERAGE', 'COUNT', 'MIN', 'MAX', 'IF', 'VLOOKUP', 'HLOOKUP',
        'INDEX', 'MATCH', 'XLOOKUP', 'COUNTIF', 'SUMIF', 'PIVOT', 'FILTER'
    ]
    
    found_functions = []
    text_upper = text.upper()
    
    for func in excel_functions:
        if re.search(rf'\b{func}\s*\(', text_upper):
            found_functions.append(func)
    
    return found_functions

def sanitize_input(input_text: str, max_length: int = 10000) -> str:
    """Sanitize user input by removing dangerous content"""
    if not isinstance(input_text, str):
        return ""
    
    # Remove excessive whitespace
    cleaned_text = re.sub(r'\s+', ' ', input_text).strip()
    
    # Limit length
    if len(cleaned_text) > max_length:
        cleaned_text = cleaned_text[:max_length] + "..."
    
    return cleaned_text
