"""
Question Bank Service - Pre-built Excel interview questions and management
"""
from typing import List, Dict, Optional, Any
import random
import logging
from datetime import datetime

from excel_interviewer.models.question import (
    ExcelQuestion, QuestionType, QuestionDifficulty, QuestionCategory
)

logger = logging.getLogger(__name__)

class QuestionBankService:
    """Service for managing Excel interview questions"""
    
    def __init__(self):
        self.questions = []
        self.question_stats = {}
        self._load_questions()
        logger.info(f"Question bank initialized with {len(self.questions)} questions")
    
    def _load_questions(self) -> None:
        """Load pre-built Excel questions"""
        questions_data = [
            # ===== BASIC LEVEL QUESTIONS =====
            {
                "id": "basic_001",
                "question_text": "How would you calculate the sum of values in cells A1 to A10?",
                "question_type": QuestionType.FORMULA,
                "difficulty": QuestionDifficulty.BASIC,
                "category": QuestionCategory.BASIC_FUNCTIONS,
                "expected_keywords": ["SUM", "formula", "range", "A1:A10"],
                "sample_answer": "Use the SUM function: =SUM(A1:A10). This adds all values in the range A1 through A10.",
                "follow_up_questions": ["What if some cells contain text?", "How would you sum only positive values?"],
                "tags": ["sum", "basic", "arithmetic"],
                "time_limit_seconds": 120
            },
            {
                "id": "basic_002", 
                "question_text": "Explain how to create a basic pivot table from a data set.",
                "question_type": QuestionType.DATA_ANALYSIS,
                "difficulty": QuestionDifficulty.BASIC,
                "category": QuestionCategory.PIVOT_TABLES,
                "expected_keywords": ["pivot table", "data", "fields", "drag", "insert"],
                "sample_answer": "Select data range, go to Insert > PivotTable, drag fields to Rows/Columns/Values areas, configure as needed.",
                "follow_up_questions": ["How do you refresh a pivot table?", "What are calculated fields?"],
                "tags": ["pivot", "data analysis", "summarize"],
                "time_limit_seconds": 180
            },
            {
                "id": "basic_003",
                "question_text": "How do you use VLOOKUP to find a value in another table?",
                "question_type": QuestionType.FORMULA,
                "difficulty": QuestionDifficulty.BASIC,
                "category": QuestionCategory.LOOKUP_FUNCTIONS,
                "expected_keywords": ["VLOOKUP", "lookup", "table", "exact match", "FALSE"],
                "sample_answer": "=VLOOKUP(lookup_value, table_array, col_index_num, FALSE) for exact match. The function searches for lookup_value in the first column of table_array and returns a value from the specified column.",
                "follow_up_questions": ["What's the difference between TRUE and FALSE?", "What are VLOOKUP limitations?"],
                "tags": ["vlookup", "lookup", "reference"],
                "time_limit_seconds": 150
            },
            {
                "id": "basic_004",
                "question_text": "How would you apply conditional formatting to highlight cells based on their values?",
                "question_type": QuestionType.DATA_ANALYSIS,
                "difficulty": QuestionDifficulty.BASIC,
                "category": QuestionCategory.DATA_MANIPULATION,
                "expected_keywords": ["conditional formatting", "highlight", "rules", "format"],
                "sample_answer": "Select cells, go to Home > Conditional Formatting, choose rule type (Greater Than, Less Than, etc.), set conditions and formatting style.",
                "follow_up_questions": ["How do you create custom formulas for formatting?", "Can you format entire rows?"],
                "tags": ["formatting", "conditional", "visual"],
                "time_limit_seconds": 120
            },
            {
                "id": "basic_005",
                "question_text": "What is the difference between relative and absolute cell references?",
                "question_type": QuestionType.FORMULA,
                "difficulty": QuestionDifficulty.BASIC,
                "category": QuestionCategory.BASIC_FUNCTIONS,
                "expected_keywords": ["relative", "absolute", "dollar sign", "$", "reference"],
                "sample_answer": "Relative references (A1) change when copied to other cells. Absolute references ($A$1) stay fixed. Mixed references ($A1 or A$1) fix either row or column.",
                "follow_up_questions": ["When would you use mixed references?", "How do you quickly make a reference absolute?"],
                "tags": ["references", "formula", "copying"],
                "time_limit_seconds": 120
            },
            
            # ===== INTERMEDIATE LEVEL QUESTIONS =====
            {
                "id": "inter_001",
                "question_text": "You have sales data with duplicate entries. How would you identify and remove duplicates while preserving the most recent record?",
                "question_type": QuestionType.DATA_ANALYSIS,
                "difficulty": QuestionDifficulty.INTERMEDIATE,
                "category": QuestionCategory.DATA_MANIPULATION,
                "expected_keywords": ["duplicates", "remove", "filter", "sort", "unique", "recent"],
                "sample_answer": "Sort by date descending, then use Data > Remove Duplicates feature. Alternatively, use advanced filter with 'unique records only' option or UNIQUE function in newer Excel versions.",
                "follow_up_questions": ["How would you handle this with formulas?", "What about partial duplicates?"],
                "tags": ["duplicates", "data cleaning", "advanced"],
                "time_limit_seconds": 240
            },
            {
                "id": "inter_002",
                "question_text": "Explain INDEX-MATCH combination and when you'd use it over VLOOKUP.",
                "question_type": QuestionType.FORMULA,
                "difficulty": QuestionDifficulty.INTERMEDIATE,
                "category": QuestionCategory.LOOKUP_FUNCTIONS,
                "expected_keywords": ["INDEX", "MATCH", "lookup", "left", "performance", "flexible"],
                "sample_answer": "=INDEX(return_range, MATCH(lookup_value, lookup_range, 0)). More flexible than VLOOKUP - can look left, faster for large datasets, works with inserted/deleted columns.",
                "follow_up_questions": ["How do you do a two-way lookup?", "What about approximate matches?"],
                "tags": ["index", "match", "advanced lookup"],
                "time_limit_seconds": 200
            },
            {
                "id": "inter_003",
                "question_text": "How would you create a dynamic dashboard that updates when new data is added?",
                "question_type": QuestionType.SCENARIO,
                "difficulty": QuestionDifficulty.INTERMEDIATE,
                "category": QuestionCategory.DATA_MANIPULATION,
                "expected_keywords": ["dynamic", "dashboard", "tables", "charts", "refresh", "named ranges"],
                "sample_answer": "Use Excel Tables for auto-expanding ranges, create charts referencing tables, use pivot tables with auto-refresh, implement named ranges with OFFSET/COUNTA for dynamic ranges.",
                "follow_up_questions": ["How do you automate the refresh?", "What about real-time data connections?"],
                "tags": ["dashboard", "dynamic", "automation"],
                "time_limit_seconds": 300
            },
            {
                "id": "inter_004",
                "question_text": "Describe how to use data validation to create dropdown lists and prevent invalid data entry.",
                "question_type": QuestionType.DATA_ANALYSIS,
                "difficulty": QuestionDifficulty.INTERMEDIATE,
                "category": QuestionCategory.DATA_MANIPULATION,
                "expected_keywords": ["data validation", "dropdown", "list", "validation rules", "error alerts"],
                "sample_answer": "Use Data > Data Validation, set criteria to List, define source range or type values directly. Configure error alerts and input messages for user guidance.",
                "follow_up_questions": ["How do you create dependent dropdowns?", "What about custom validation formulas?"],
                "tags": ["validation", "dropdown", "data quality"],
                "time_limit_seconds": 180
            },
            {
                "id": "inter_005",
                "question_text": "How would you use COUNTIFS and SUMIFS for multi-criteria analysis?",
                "question_type": QuestionType.FORMULA,
                "difficulty": QuestionDifficulty.INTERMEDIATE,
                "category": QuestionCategory.CONDITIONAL_LOGIC,
                "expected_keywords": ["COUNTIFS", "SUMIFS", "criteria", "multiple conditions", "analysis"],
                "sample_answer": "COUNTIFS(range1,criteria1,range2,criteria2...) counts cells meeting multiple criteria. SUMIFS(sum_range,criteria_range1,criteria1,criteria_range2,criteria2...) sums with multiple conditions.",
                "follow_up_questions": ["How do you use wildcards in criteria?", "What about date range criteria?"],
                "tags": ["countifs", "sumifs", "multiple criteria"],
                "time_limit_seconds": 200
            },
            
            # ===== ADVANCED LEVEL QUESTIONS =====
            {
                "id": "adv_001",
                "question_text": "You need to analyze sales performance across multiple dimensions (time, region, product) with complex calculations. Describe your approach using advanced Excel features.",
                "question_type": QuestionType.PROBLEM_SOLVING,
                "difficulty": QuestionDifficulty.ADVANCED,
                "category": QuestionCategory.STATISTICAL_ANALYSIS,
                "expected_keywords": ["pivot", "power query", "data model", "relationships", "measures", "DAX"],
                "sample_answer": "Create data model with Power Pivot, establish relationships between tables, use DAX for calculated measures (YoY growth, running totals), build comprehensive pivot tables with slicers and timelines.",
                "follow_up_questions": ["How would you handle year-over-year comparisons?", "What about forecasting trends?"],
                "tags": ["power pivot", "dax", "advanced analysis"],
                "time_limit_seconds": 400
            },
            {
                "id": "adv_002",
                "question_text": "Describe how you'd build an automated financial model that handles scenario analysis and sensitivity testing.",
                "question_type": QuestionType.PRACTICAL,
                "difficulty": QuestionDifficulty.ADVANCED,
                "category": QuestionCategory.FINANCIAL_MODELING,
                "expected_keywords": ["scenario", "data table", "solver", "sensitivity", "automation", "goal seek"],
                "sample_answer": "Use Data Tables for sensitivity analysis, Scenario Manager for different cases, Goal Seek/Solver for optimization, dynamic named ranges, VBA for automation and user interface.",
                "follow_up_questions": ["How do you validate model accuracy?", "What about Monte Carlo simulation?"],
                "tags": ["financial modeling", "scenarios", "automation"],
                "time_limit_seconds": 450
            },
            {
                "id": "adv_003",
                "question_text": "You have messy data from multiple sources that needs cleaning and standardization before analysis. Walk through your process.",
                "question_type": QuestionType.DATA_ANALYSIS,
                "difficulty": QuestionDifficulty.ADVANCED,
                "category": QuestionCategory.DATA_MANIPULATION,
                "expected_keywords": ["power query", "ETL", "transform", "standardize", "automation", "data types"],
                "sample_answer": "Use Power Query for ETL process: connect to multiple sources, transform data (split columns, merge, standardize formats, handle nulls), establish data types, load to data model with automatic refresh.",
                "follow_up_questions": ["How do you handle errors in transformation?", "What about incremental data loads?"],
                "tags": ["power query", "etl", "data cleaning"],
                "time_limit_seconds": 350
            },
            {
                "id": "adv_004",
                "question_text": "How would you implement array formulas or dynamic arrays to perform complex calculations across multiple ranges?",
                "question_type": QuestionType.FORMULA,
                "difficulty": QuestionDifficulty.ADVANCED,
                "category": QuestionCategory.ADVANCED_FUNCTIONS,
                "expected_keywords": ["array formulas", "dynamic arrays", "FILTER", "SORT", "UNIQUE", "spill range"],
                "sample_answer": "Use dynamic array functions like FILTER, SORT, UNIQUE for modern Excel. For legacy versions, create array formulas with Ctrl+Shift+Enter. Utilize spill ranges and structured references.",
                "follow_up_questions": ["How do you handle spill errors?", "What about memory considerations?"],
                "tags": ["arrays", "dynamic", "advanced formulas"],
                "time_limit_seconds": 300
            },
            {
                "id": "adv_005",
                "question_text": "Explain how you would create a real-time executive dashboard that pulls data from multiple databases and updates automatically.",
                "question_type": QuestionType.SCENARIO,
                "difficulty": QuestionDifficulty.ADVANCED,
                "category": QuestionCategory.AUTOMATION_MACROS,
                "expected_keywords": ["real-time", "dashboard", "databases", "connections", "refresh", "automation"],
                "sample_answer": "Use Power Query to connect multiple data sources (SQL, APIs, files), create refresh schedules, build pivot tables and charts with automatic updates, implement error handling and user notifications.",
                "follow_up_questions": ["How do you handle connection failures?", "What about performance optimization?"],
                "tags": ["real-time", "connections", "executive dashboard"],
                "time_limit_seconds": 400
            }
        ]
        
        # Convert to ExcelQuestion objects
        self.questions = []
        for q_data in questions_data:
            try:
                question = ExcelQuestion(**q_data)
                self.questions.append(question)
            except Exception as e:
                logger.error(f"Error creating question {q_data.get('id', 'unknown')}: {e}")
        
        logger.info(f"Successfully loaded {len(self.questions)} questions")
    
    def get_question_by_id(self, question_id: str) -> Optional[ExcelQuestion]:
        """Get specific question by ID"""
        return next((q for q in self.questions if q.id == question_id), None)
    
    def get_questions_by_difficulty(self, difficulty: QuestionDifficulty) -> List[ExcelQuestion]:
        """Get questions filtered by difficulty"""
        return [q for q in self.questions if q.difficulty == difficulty and q.is_active]
    
    def get_questions_by_type(self, question_type: QuestionType) -> List[ExcelQuestion]:
        """Get questions filtered by type"""
        return [q for q in self.questions if q.question_type == question_type and q.is_active]
    
    def get_questions_by_category(self, category: QuestionCategory) -> List[ExcelQuestion]:
        """Get questions filtered by category"""
        return [q for q in self.questions if q.category == category and q.is_active]
    
    def get_random_question(
        self, 
        difficulty: Optional[QuestionDifficulty] = None,
        question_type: Optional[QuestionType] = None,
        category: Optional[QuestionCategory] = None,
        exclude_ids: List[str] = None
    ) -> Optional[ExcelQuestion]:
        """Get random question based on criteria"""
        
        filtered_questions = [q for q in self.questions if q.is_active]
        
        # Apply filters
        if difficulty:
            filtered_questions = [q for q in filtered_questions if q.difficulty == difficulty]
        
        if question_type:
            filtered_questions = [q for q in filtered_questions if q.question_type == question_type]
        
        if category:
            filtered_questions = [q for q in filtered_questions if q.category == category]
        
        if exclude_ids:
            filtered_questions = [q for q in filtered_questions if q.id not in exclude_ids]
        
        return random.choice(filtered_questions) if filtered_questions else None
    
    def get_adaptive_question(
        self, 
        current_difficulty: str,
        previous_scores: List[float],
        asked_question_ids: List[str],
        preferred_types: List[QuestionType] = None
    ) -> Optional[ExcelQuestion]:
        """Get next question based on performance and adaptive logic"""
        
        # Determine target difficulty based on recent performance
        if previous_scores:
            recent_scores = previous_scores[-3:]  # Last 3 questions
            avg_recent_score = sum(recent_scores) / len(recent_scores)
            
            # Adaptive difficulty adjustment
            if avg_recent_score >= 85:
                target_difficulty = QuestionDifficulty.ADVANCED
            elif avg_recent_score >= 70:
                target_difficulty = QuestionDifficulty.INTERMEDIATE  
            elif avg_recent_score >= 50:
                # Stay at current level
                target_difficulty = QuestionDifficulty(current_difficulty)
            else:
                # Drop down a level
                difficulty_order = [QuestionDifficulty.BASIC, QuestionDifficulty.INTERMEDIATE, QuestionDifficulty.ADVANCED]
                current_index = difficulty_order.index(QuestionDifficulty(current_difficulty))
                target_difficulty = difficulty_order[max(0, current_index - 1)]
        else:
            # Start with provided difficulty
            target_difficulty = QuestionDifficulty(current_difficulty)
        
        # Try to get question of target difficulty first
        question = self.get_random_question(
            difficulty=target_difficulty,
            question_type=random.choice(preferred_types) if preferred_types else None,
            exclude_ids=asked_question_ids
        )
        
        # If no question found, try adjacent difficulties
        if not question:
            difficulty_order = [QuestionDifficulty.BASIC, QuestionDifficulty.INTERMEDIATE, QuestionDifficulty.ADVANCED]
            current_index = difficulty_order.index(target_difficulty)
            
            # Try easier first, then harder
            for offset in [-1, 1, -2, 2]:
                new_index = current_index + offset
                if 0 <= new_index < len(difficulty_order):
                    question = self.get_random_question(
                        difficulty=difficulty_order[new_index],
                        exclude_ids=asked_question_ids
                    )
                    if question:
                        break
        
        return question
    
    def get_question_statistics(self) -> Dict[str, Any]:
        """Get comprehensive question bank statistics"""
        if not self.questions:
            return {}
        
        active_questions = [q for q in self.questions if q.is_active]
        
        stats = {
            "total_questions": len(self.questions),
            "active_questions": len(active_questions),
            "difficulty_distribution": {},
            "category_distribution": {},
            "type_distribution": {}
        }
        
        # Count distributions
        for question in active_questions:
            # Difficulty distribution
            difficulty = question.difficulty.value
            stats["difficulty_distribution"][difficulty] = stats["difficulty_distribution"].get(difficulty, 0) + 1
            
            # Category distribution
            if question.category:
                category = question.category.value
                stats["category_distribution"][category] = stats["category_distribution"].get(category, 0) + 1
            
            # Type distribution
            qtype = question.question_type.value
            stats["type_distribution"][qtype] = stats["type_distribution"].get(qtype, 0) + 1
        
        return stats
    
    def update_question_stats(self, question_id: str, score: float, response_time: float):
        """Update usage statistics for a question"""
        question = self.get_question_by_id(question_id)
        if question:
            question.update_usage_stats(score, response_time)
            logger.info(f"Updated stats for question {question_id}: score={score}, time={response_time}s")

# Global question bank instance
question_bank = QuestionBankService()

