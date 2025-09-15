"""
Excel Evaluator Service - AI-powered response evaluation with enhanced analysis
"""
from typing import Dict, List, Optional, Any
import logging
import asyncio
import re
from datetime import datetime

from excel_interviewer.services.llm_service import llm_service
from excel_interviewer.models.evaluation import EvaluationCriteria, ResponseEvaluation

logger = logging.getLogger(__name__)

class ExcelEvaluator:
    """Advanced Excel response evaluator with AI integration and local analysis"""
    
    def __init__(self):
        self.evaluation_cache = {}  # Cache for similar evaluations
        self.evaluation_count = 0
        self.average_evaluation_time = 0.0
        
        # Excel function keywords for analysis
        self.excel_functions = {
            "basic": [
                "SUM", "AVERAGE", "COUNT", "MIN", "MAX", "IF", "ROUND", "ABS",
                "TODAY", "NOW", "LEN", "TRIM", "UPPER", "LOWER", "CONCATENATE"
            ],
            "intermediate": [
                "VLOOKUP", "HLOOKUP", "INDEX", "MATCH", "COUNTIF", "SUMIF", "AVERAGEIF",
                "COUNTIFS", "SUMIFS", "AVERAGEIFS", "IFERROR", "IFNA", "CHOOSE",
                "INDIRECT", "OFFSET", "LEFT", "RIGHT", "MID", "FIND", "SEARCH", "SUBSTITUTE"
            ],
            "advanced": [
                "XLOOKUP", "FILTER", "SORT", "UNIQUE", "SEQUENCE", "LAMBDA",
                "POWER QUERY", "PIVOT", "DAX", "SOLVER", "GOAL SEEK",
                "ARRAY", "SPILL", "DYNAMIC", "POWER PIVOT"
            ]
        }
        
        # Excel concepts and terminology
        self.excel_concepts = [
            "cell reference", "relative reference", "absolute reference", "mixed reference",
            "range", "worksheet", "workbook", "formula bar", "name box",
            "conditional formatting", "data validation", "pivot table", "chart",
            "filter", "sort", "freeze panes", "split", "macro", "VBA"
        ]
        
        logger.info("Excel Evaluator initialized with comprehensive analysis capabilities")
    
    async def evaluate_response(
        self,
        question_text: str,
        candidate_response: str,
        difficulty: str,
        question_type: str = "general",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive evaluation of candidate's Excel response
        Combines AI evaluation with local analysis for robust assessment
        """
        start_time = datetime.utcnow()
        
        try:
            # Check cache first (for identical responses)
            cache_key = self._generate_cache_key(question_text, candidate_response, difficulty)
            if cache_key in self.evaluation_cache:
                logger.info("Returning cached evaluation")
                cached_result = self.evaluation_cache[cache_key].copy()
                cached_result["evaluation_method"] = "cached"
                return cached_result
            
            # Perform local pre-analysis
            local_analysis = await self._perform_local_analysis(
                question_text, candidate_response, difficulty, question_type
            )
            
            # Get AI evaluation
            ai_evaluation = await llm_service.evaluate_excel_response(
                question=question_text,
                candidate_response=candidate_response,
                difficulty=difficulty
            )
            
            # Combine AI and local analysis
            enhanced_evaluation = await self._enhance_evaluation(
                ai_evaluation, local_analysis, question_text, candidate_response, difficulty
            )
            
            # Cache the result
            self.evaluation_cache[cache_key] = enhanced_evaluation.copy()
            
            # Update statistics
            evaluation_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_stats(evaluation_time)
            
            enhanced_evaluation["evaluation_time"] = evaluation_time
            enhanced_evaluation["evaluation_method"] = "ai_enhanced"
            
            return enhanced_evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating response: {e}")
            return self._get_fallback_evaluation(difficulty, question_type)
    
    async def _perform_local_analysis(
        self,
        question: str,
        response: str,
        difficulty: str,
        question_type: str
    ) -> Dict[str, Any]:
        """Perform local analysis of the response"""
        
        analysis = {
            "response_length": len(response),
            "word_count": len(response.split()),
            "excel_functions_mentioned": [],
            "excel_concepts_mentioned": [],
            "keyword_density": 0.0,
            "technical_indicators": {},
            "communication_indicators": {},
            "completeness_indicators": {}
        }
        
        response_upper = response.upper()
        response_lower = response.lower()
        
        # Analyze Excel functions mentioned
        all_functions = []
        for level, functions in self.excel_functions.items():
            all_functions.extend(functions)
        
        mentioned_functions = []
        for func in all_functions:
            if func.upper() in response_upper:
                mentioned_functions.append(func)
        
        analysis["excel_functions_mentioned"] = list(set(mentioned_functions))
        
        # Analyze Excel concepts mentioned
        mentioned_concepts = []
        for concept in self.excel_concepts:
            if concept.lower() in response_lower:
                mentioned_concepts.append(concept)
        
        analysis["excel_concepts_mentioned"] = mentioned_concepts
        
        # Calculate keyword density
        total_keywords = len(mentioned_functions) + len(mentioned_concepts)
        if analysis["word_count"] > 0:
            analysis["keyword_density"] = total_keywords / analysis["word_count"]
        
        # Technical indicators
        analysis["technical_indicators"] = {
            "mentions_formulas": any(indicator in response_lower for indicator in ["formula", "function", "="]),
            "mentions_steps": any(indicator in response_lower for indicator in ["first", "then", "next", "step"]),
            "mentions_specific_functions": len(mentioned_functions) > 0,
            "mentions_cell_references": bool(re.search(r'[A-Z]+\d+', response.upper())),
            "mentions_ranges": ":" in response and bool(re.search(r'[A-Z]+\d+:[A-Z]+\d+', response.upper()))
        }
        
        # Communication indicators
        analysis["communication_indicators"] = {
            "uses_explanation": any(word in response_lower for word in ["because", "since", "therefore", "so that"]),
            "provides_examples": any(word in response_lower for word in ["example", "for instance", "such as"]),
            "structured_response": len([s for s in response.split(".") if s.strip()]) > 2,
            "appropriate_length": 20 <= analysis["word_count"] <= 200
        }
        
        # Completeness indicators
        analysis["completeness_indicators"] = {
            "addresses_how": any(word in response_lower for word in ["how", "method", "approach", "way"]),
            "addresses_what": any(word in response_lower for word in ["what", "which", "function", "feature"]),
            "addresses_when": any(word in response_lower for word in ["when", "situation", "case"]),
            "provides_alternatives": any(word in response_lower for word in ["alternatively", "also", "another", "or"])
        }
        
        return analysis
    
    async def _enhance_evaluation(
        self,
        ai_evaluation: Dict[str, Any],
        local_analysis: Dict[str, Any],
        question: str,
        response: str,
        difficulty: str
    ) -> Dict[str, Any]:
        """Enhance AI evaluation with local analysis insights"""
        
        try:
            enhanced = ai_evaluation.copy()
            
            # Adjust scores based on local analysis
            adjustments = self._calculate_score_adjustments(local_analysis, difficulty)
            
            # Apply adjustments to each score
            score_fields = [
                "technical_accuracy", "communication_clarity", "problem_solving_approach",
                "completeness", "efficiency"
            ]
            
            for field in score_fields:
                if field in enhanced and field in adjustments:
                    original_score = enhanced[field]
                    adjustment = adjustments[field]
                    
                    # Apply adjustment (max ±15 points)
                    adjusted_score = original_score + min(15, max(-15, adjustment))
                    enhanced[field] = max(0, min(100, adjusted_score))
            
            # Recalculate overall score
            scores = [enhanced[field] for field in score_fields]
            enhanced["overall_score"] = round(sum(scores) / len(scores), 2)
            
            # Add local analysis insights
            enhanced["local_analysis"] = local_analysis
            enhanced["score_adjustments"] = adjustments
            
            # Add confidence score based on analysis consistency
            enhanced["confidence_score"] = self._calculate_confidence(enhanced, local_analysis)
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Error enhancing evaluation: {e}")
            return ai_evaluation
    
    def _calculate_score_adjustments(
        self, 
        analysis: Dict[str, Any], 
        difficulty: str
    ) -> Dict[str, float]:
        """Calculate score adjustments based on local analysis"""
        
        adjustments = {
            "technical_accuracy": 0.0,
            "communication_clarity": 0.0,
            "problem_solving_approach": 0.0,
            "completeness": 0.0,
            "efficiency": 0.0
        }
        
        # Technical accuracy adjustments
        tech_indicators = analysis["technical_indicators"]
        if tech_indicators["mentions_specific_functions"]:
            adjustments["technical_accuracy"] += 5
        if tech_indicators["mentions_cell_references"]:
            adjustments["technical_accuracy"] += 3
        if tech_indicators["mentions_ranges"]:
            adjustments["technical_accuracy"] += 2
        
        # Communication clarity adjustments
        comm_indicators = analysis["communication_indicators"]
        if comm_indicators["uses_explanation"]:
            adjustments["communication_clarity"] += 4
        if comm_indicators["provides_examples"]:
            adjustments["communication_clarity"] += 3
        if comm_indicators["structured_response"]:
            adjustments["communication_clarity"] += 2
        if not comm_indicators["appropriate_length"]:
            adjustments["communication_clarity"] -= 5
        
        # Problem solving adjustments
        if tech_indicators["mentions_steps"]:
            adjustments["problem_solving_approach"] += 4
        if analysis["keyword_density"] > 0.1:  # Good keyword usage
            adjustments["problem_solving_approach"] += 2
        
        # Completeness adjustments
        comp_indicators = analysis["completeness_indicators"]
        completeness_score = sum(comp_indicators.values()) * 2
        adjustments["completeness"] += completeness_score
        
        return adjustments
    
    def _calculate_confidence(self, evaluation: Dict[str, Any], analysis: Dict[str, Any]) -> float:
        """Calculate confidence level in the evaluation"""
        
        confidence_factors = []
        
        # Response length factor
        word_count = analysis["word_count"]
        if 30 <= word_count <= 150:
            confidence_factors.append(0.9)
        elif 15 <= word_count <= 200:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.5)
        
        # Technical content factor
        if len(analysis["excel_functions_mentioned"]) > 0:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.6)
        
        return round(sum(confidence_factors) / len(confidence_factors), 2)
    
    def _generate_cache_key(self, question: str, response: str, difficulty: str) -> str:
        """Generate cache key for evaluation"""
        return f"{hash(question)}_{hash(response)}_{difficulty}"
    
    def _get_fallback_evaluation(self, difficulty: str, question_type: str) -> Dict[str, Any]:
        """Provide fallback evaluation when AI and local analysis fail"""
        base_scores = {"basic": 60, "intermediate": 50, "advanced": 40}
        base_score = base_scores.get(difficulty, 50)
        
        return {
            "technical_accuracy": base_score,
            "communication_clarity": base_score - 5,
            "problem_solving_approach": base_score,
            "completeness": base_score - 10,
            "efficiency": base_score - 5,
            "overall_score": base_score - 5,
            "feedback": f"Unable to fully evaluate response due to technical issues. Based on {difficulty} level expectations, this appears to be a reasonable attempt. Please provide more specific Excel details for better assessment.",
            "strengths": ["Attempted to answer the question"],
            "areas_for_improvement": [
                "Provide specific Excel formulas and functions",
                "Explain step-by-step process clearly",
                "Include practical examples and use cases"
            ],
            "next_difficulty_level": difficulty,
            "confidence_score": 0.3,
            "evaluation_method": "fallback"
        }
    
    def _update_stats(self, evaluation_time: float):
        """Update evaluation service statistics"""
        self.evaluation_count += 1
        
        if self.average_evaluation_time == 0:
            self.average_evaluation_time = evaluation_time
        else:
            self.average_evaluation_time = (
                (self.average_evaluation_time * (self.evaluation_count - 1) + evaluation_time) 
                / self.evaluation_count
            )
    
    def get_evaluation_stats(self) -> Dict[str, Any]:
        """Get evaluation service statistics"""
        return {
            "total_evaluations": self.evaluation_count,
            "average_evaluation_time": round(self.average_evaluation_time, 3),
            "cache_size": len(self.evaluation_cache),
            "excel_functions_tracked": {
                "basic": len(self.excel_functions["basic"]),
                "intermediate": len(self.excel_functions["intermediate"]),
                "advanced": len(self.excel_functions["advanced"])
            },
            "concepts_tracked": len(self.excel_concepts)
        }

# Global excel evaluator instance
excel_evaluator = ExcelEvaluator()
