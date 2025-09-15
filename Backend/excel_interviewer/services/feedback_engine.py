"""
Feedback Engine - Generates comprehensive assessment reports and feedback
"""
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
import statistics

from excel_interviewer.models.evaluation import FinalAssessment, HireRecommendation, SkillAssessment
from excel_interviewer.services.llm_service import llm_service

logger = logging.getLogger(__name__)

class FeedbackEngine:
    """Generates comprehensive feedback and final assessments"""
    
    def __init__(self):
        self.reports_generated = 0
        self.average_generation_time = 0.0
        
    async def generate_final_assessment(
        self, 
        interview_id: str, 
        responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate comprehensive final assessment"""
        start_time = datetime.utcnow()
        
        try:
            if not responses:
                return self._get_default_assessment("No responses provided")
            
            # Calculate overall statistics
            stats = self._calculate_performance_statistics(responses)
            
            # Analyze performance by categories
            category_analysis = self._analyze_category_performance(responses)
            
            # Determine skill level and recommendation
            skill_level = self._determine_skill_level(stats["overall_score"])
            hire_recommendation = self._determine_hire_recommendation(stats["overall_score"], stats)
            
            # Generate detailed feedback using AI
            detailed_feedback = await self._generate_detailed_feedback(responses, stats)
            
            # Generate executive summary
            executive_summary = self._generate_executive_summary(
                stats["overall_score"], skill_level, hire_recommendation
            )
            
            # Compile final assessment
            final_assessment = {
                "interview_id": interview_id,
                "overall_score": stats["overall_score"],
                "skill_level_assessment": skill_level,
                "hire_recommendation": hire_recommendation,
                
                # Detailed scoring
                "category_scores": category_analysis["category_scores"],
                "dimension_scores": stats["dimension_averages"],
                "question_scores": [
                    {
                        "question_id": r["question_id"],
                        "question_text": r["question_text"][:100] + "..." if len(r["question_text"]) > 100 else r["question_text"],
                        "score": r["evaluation"]["overall_score"],
                        "difficulty": r.get("difficulty", "intermediate")
                    }
                    for r in responses
                ],
                
                # Comprehensive feedback
                "detailed_feedback": detailed_feedback,
                "executive_summary": executive_summary,
                "recommendations": self._generate_recommendations(category_analysis, stats),
                
                # Performance analysis
                "strengths_summary": self._extract_strengths(responses),
                "improvement_areas": self._extract_improvement_areas(responses),
                "readiness_assessment": self._assess_role_readiness(stats["overall_score"], category_analysis),
                
                # Statistical analysis
                "statistics": stats,
                "benchmarking": self._generate_benchmarking(stats["overall_score"], skill_level),
                
                # Metadata
                "assessment_date": datetime.utcnow().isoformat(),
                "assessment_version": "1.0.0",
                "total_questions": len(responses),
                "interview_duration_minutes": self._estimate_duration(responses)
            }
            
            # Update statistics
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_stats(generation_time)
            
            logger.info(f"Generated final assessment for interview {interview_id}")
            return final_assessment
            
        except Exception as e:
            logger.error(f"Error generating final assessment: {e}")
            return self._get_default_assessment(f"Error generating assessment: {str(e)}")
    
    def _calculate_performance_statistics(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive performance statistics"""
        if not responses:
            return {"overall_score": 0, "dimension_averages": {}, "consistency": 0}
        
        all_scores = []
        dimension_scores = {
            "technical_accuracy": [],
            "communication_clarity": [],
            "problem_solving_approach": [],
            "completeness": [],
            "efficiency": []
        }
        
        for response in responses:
            evaluation = response.get("evaluation", {})
            overall_score = evaluation.get("overall_score", 0)
            all_scores.append(overall_score)
            
            # Collect dimension scores
            for dimension in dimension_scores.keys():
                score = evaluation.get(dimension, overall_score)
                dimension_scores[dimension].append(score)
        
        # Calculate averages
        overall_score = statistics.mean(all_scores)
        dimension_averages = {
            dim: statistics.mean(scores) if scores else 0
            for dim, scores in dimension_scores.items()
        }
        
        # Calculate consistency (lower standard deviation = more consistent)
        consistency = 100 - min(statistics.stdev(all_scores) if len(all_scores) > 1 else 0, 25)
        
        # Performance trend
        if len(all_scores) >= 3:
            first_half = all_scores[:len(all_scores)//2]
            second_half = all_scores[len(all_scores)//2:]
            trend = statistics.mean(second_half) - statistics.mean(first_half)
        else:
            trend = 0
        
        return {
            "overall_score": round(overall_score, 2),
            "dimension_averages": {k: round(v, 2) for k, v in dimension_averages.items()},
            "consistency": round(consistency, 2),
            "performance_trend": round(trend, 2),
            "score_range": {
                "min": min(all_scores),
                "max": max(all_scores),
                "range": max(all_scores) - min(all_scores)
            }
        }
    
    def _analyze_category_performance(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance by Excel skill categories"""
        category_scores = {}
        category_counts = {}
        
        # Define category mappings
        question_categories = {
            "basic_001": "Basic Functions",
            "basic_002": "Pivot Tables", 
            "basic_003": "Lookup Functions",
            "basic_004": "Data Manipulation",
            "basic_005": "Basic Functions",
            "inter_001": "Data Manipulation",
            "inter_002": "Lookup Functions",
            "inter_003": "Data Manipulation", 
            "inter_004": "Data Manipulation",
            "inter_005": "Conditional Logic",
            "adv_001": "Statistical Analysis",
            "adv_002": "Financial Modeling",
            "adv_003": "Data Manipulation",
            "adv_004": "Advanced Functions",
            "adv_005": "Automation"
        }
        
        for response in responses:
            question_id = response.get("question_id", "")
            category = question_categories.get(question_id, "General")
            score = response.get("evaluation", {}).get("overall_score", 0)
            
            if category not in category_scores:
                category_scores[category] = []
            
            category_scores[category].append(score)
        
        # Calculate category averages
        category_averages = {
            category: round(statistics.mean(scores), 2)
            for category, scores in category_scores.items()
        }
        
        # Identify strengths and weaknesses
        if category_averages:
            strongest_category = max(category_averages.items(), key=lambda x: x[1])
            weakest_category = min(category_averages.items(), key=lambda x: x[1])
        else:
            strongest_category = ("General", 0)
            weakest_category = ("General", 0)
        
        return {
            "category_scores": category_averages,
            "strongest_category": strongest_category,
            "weakest_category": weakest_category,
            "categories_above_threshold": [
                cat for cat, score in category_averages.items() if score >= 70
            ],
            "categories_needing_improvement": [
                cat for cat, score in category_averages.items() if score < 60
            ]
        }
    
    def _determine_skill_level(self, overall_score: float) -> str:
        """Determine skill level based on overall performance"""
        if overall_score >= 90:
            return SkillAssessment.EXPERT
        elif overall_score >= 80:
            return SkillAssessment.ADVANCED
        elif overall_score >= 65:
            return SkillAssessment.INTERMEDIATE
        elif overall_score >= 45:
            return SkillAssessment.BASIC
        elif overall_score >= 25:
            return SkillAssessment.BEGINNER
        else:
            return SkillAssessment.INSUFFICIENT_DATA
    
    def _determine_hire_recommendation(self, overall_score: float, stats: Dict[str, Any]) -> str:
        """Determine hiring recommendation based on performance"""
        consistency = stats.get("consistency", 0)
        trend = stats.get("performance_trend", 0)
        
        # Base recommendation on score
        if overall_score >= 85 and consistency >= 70:
            return HireRecommendation.STRONG_HIRE
        elif overall_score >= 75 and consistency >= 60:
            return HireRecommendation.HIRE
        elif overall_score >= 60 and (consistency >= 50 or trend > 5):
            return HireRecommendation.CONDITIONAL_HIRE
        elif overall_score >= 40:
            return HireRecommendation.NO_HIRE
        else:
            return HireRecommendation.STRONG_NO_HIRE
    
    async def _generate_detailed_feedback(
        self, 
        responses: List[Dict[str, Any]], 
        stats: Dict[str, Any]
    ) -> str:
        """Generate detailed AI-powered feedback"""
        try:
            # Compile response summaries
            response_summary = []
            for i, response in enumerate(responses[:5]):  # Limit to first 5 for prompt
                eval_data = response.get("evaluation", {})
                response_summary.append(f"Q{i+1}: Score {eval_data.get('overall_score', 0)}/100")
            
            prompt = f"""
Generate detailed performance feedback for an Excel skills interview based on these results:

OVERALL PERFORMANCE:
- Overall Score: {stats['overall_score']}/100
- Consistency: {stats['consistency']}/100
- Performance Trend: {stats['performance_trend']} (positive = improved during interview)
- Questions Answered: {len(responses)}

DIMENSION SCORES:
- Technical Accuracy: {stats['dimension_averages'].get('technical_accuracy', 0)}/100
- Communication Clarity: {stats['dimension_averages'].get('communication_clarity', 0)}/100
- Problem Solving: {stats['dimension_averages'].get('problem_solving_approach', 0)}/100
- Completeness: {stats['dimension_averages'].get('completeness', 0)}/100
- Efficiency: {stats['dimension_averages'].get('efficiency', 0)}/100

QUESTION PERFORMANCE: {'; '.join(response_summary)}

Write a comprehensive 300-400 word performance review that:
1. Summarizes overall Excel proficiency level
2. Highlights specific technical strengths and areas for development
3. Comments on consistency and improvement during the interview
4. Provides actionable recommendations for skill development
5. Maintains a professional, constructive tone

Focus on practical Excel skills relevant to business environments.
"""
            
            feedback = await llm_service.generate_response(prompt, max_tokens=500)
            return feedback.strip()
            
        except Exception as e:
            logger.error(f"Error generating AI feedback: {e}")
            return self._get_default_feedback(stats["overall_score"])
    
    def _generate_executive_summary(
        self, 
        overall_score: float, 
        skill_level: str, 
        recommendation: str
    ) -> str:
        """Generate concise executive summary"""
        performance_descriptor = {
            "expert": "exceptional",
            "advanced": "strong",
            "intermediate": "solid",
            "basic": "developing",
            "beginner": "foundational",
            "insufficient_data": "limited"
        }.get(skill_level, "adequate")
        
        recommendation_text = {
            "strong_hire": "Strongly recommended for hire",
            "hire": "Recommended for hire",
            "conditional_hire": "Conditional hire with training support",
            "no_hire": "Not recommended at this time",
            "strong_no_hire": "Not suitable for the role"
        }.get(recommendation, "Requires further evaluation")
        
        return f"Candidate demonstrates {performance_descriptor} Excel proficiency with an overall score of {overall_score}/100. {recommendation_text}. Assessment indicates {skill_level}-level Excel capabilities suitable for business applications."
    
    def _generate_recommendations(
        self, 
        category_analysis: Dict[str, Any], 
        stats: Dict[str, Any]
    ) -> List[str]:
        """Generate specific development recommendations"""
        recommendations = []
        
        # Performance-based recommendations
        if stats["overall_score"] < 70:
            recommendations.append("Focus on Excel fundamentals including basic formulas and functions")
        
        if stats["dimension_averages"].get("technical_accuracy", 0) < 60:
            recommendations.append("Practice Excel formula syntax and function usage")
        
        if stats["dimension_averages"].get("communication_clarity", 0) < 60:
            recommendations.append("Improve ability to explain Excel processes clearly and logically")
        
        # Category-specific recommendations
        weak_categories = category_analysis.get("categories_needing_improvement", [])
        for category in weak_categories:
            if category == "Lookup Functions":
                recommendations.append("Study VLOOKUP, INDEX-MATCH, and XLOOKUP functions")
            elif category == "Pivot Tables":
                recommendations.append("Practice creating and customizing pivot tables")
            elif category == "Data Manipulation":
                recommendations.append("Learn data cleaning and transformation techniques")
            elif category == "Advanced Functions":
                recommendations.append("Explore array formulas and dynamic functions")
        
        # Consistency recommendations
        if stats["consistency"] < 60:
            recommendations.append("Focus on consistent application of Excel knowledge across different scenarios")
        
        # Limit to top 5 recommendations
        return recommendations[:5] if recommendations else ["Continue practicing Excel skills in business contexts"]
    
    def _extract_strengths(self, responses: List[Dict[str, Any]]) -> List[str]:
        """Extract key strengths from individual evaluations"""
        all_strengths = []
        
        for response in responses:
            evaluation = response.get("evaluation", {})
            strengths = evaluation.get("strengths", [])
            all_strengths.extend(strengths)
        
        # Count frequency and return most common
        strength_counts = {}
        for strength in all_strengths:
            strength_counts[strength] = strength_counts.get(strength, 0) + 1
        
        # Return top 5 most frequent strengths
        sorted_strengths = sorted(strength_counts.items(), key=lambda x: x[1], reverse=True)
        return [strength for strength, count in sorted_strengths[:5]]
    
    def _extract_improvement_areas(self, responses: List[Dict[str, Any]]) -> List[str]:
        """Extract key improvement areas from individual evaluations"""
        all_improvements = []
        
        for response in responses:
            evaluation = response.get("evaluation", {})
            improvements = evaluation.get("areas_for_improvement", [])
            all_improvements.extend(improvements)
        
        # Count frequency and return most common
        improvement_counts = {}
        for improvement in all_improvements:
            improvement_counts[improvement] = improvement_counts.get(improvement, 0) + 1
        
        # Return top 5 most frequent improvement areas
        sorted_improvements = sorted(improvement_counts.items(), key=lambda x: x[1], reverse=True)
        return [improvement for improvement, count in sorted_improvements[:5]]
    
    def _assess_role_readiness(self, overall_score: float, category_analysis: Dict[str, Any]) -> Dict[str, str]:
        """Assess readiness for different types of roles"""
        assessments = {}
        
        # Basic data entry roles
        if overall_score >= 50:
            assessments["data_entry"] = "Ready"
        else:
            assessments["data_entry"] = "Needs training"
        
        # Financial analyst roles
        if overall_score >= 70 and "Financial Modeling" in category_analysis["categories_above_threshold"]:
            assessments["financial_analyst"] = "Ready"
        elif overall_score >= 60:
            assessments["financial_analyst"] = "Ready with training"
        else:
            assessments["financial_analyst"] = "Needs significant training"
        
        # Data analyst roles
        if overall_score >= 75 and len(category_analysis["categories_above_threshold"]) >= 3:
            assessments["data_analyst"] = "Ready"
        elif overall_score >= 65:
            assessments["data_analyst"] = "Ready with training"
        else:
            assessments["data_analyst"] = "Needs significant training"
        
        # Administrative roles
        if overall_score >= 55:
            assessments["administrative"] = "Ready"
        else:
            assessments["administrative"] = "Needs basic training"
        
        return assessments
    
    def _generate_benchmarking(self, overall_score: float, skill_level: str) -> Dict[str, Any]:
        """Generate performance benchmarking data"""
        # Simulated benchmark data - in production, this would come from historical data
        benchmark_data = {
            "industry_average": 68.5,
            "role_average": {
                "entry_level": 55.0,
                "mid_level": 70.0,
                "senior_level": 82.0
            },
            "percentile_rank": self._calculate_percentile(overall_score),
            "skill_level_distribution": {
                "beginner": 15,
                "basic": 25, 
                "intermediate": 35,
                "advanced": 20,
                "expert": 5
            }
        }
        
        return benchmark_data
    
    def _calculate_percentile(self, score: float) -> int:
        """Calculate approximate percentile rank"""
        # Simplified percentile calculation
        if score >= 90: return 95
        elif score >= 80: return 80
        elif score >= 70: return 65
        elif score >= 60: return 45
        elif score >= 50: return 30
        elif score >= 40: return 20
        else: return 10
    
    def _estimate_duration(self, responses: List[Dict[str, Any]]) -> int:
        """Estimate interview duration from response times"""
        total_time = sum(r.get("response_time", 180) for r in responses)  # Default 3 min per question
        return max(int(total_time / 60), len(responses) * 2)  # Minimum 2 min per question
    
    def _get_default_assessment(self, error_message: str = "Unable to complete assessment") -> Dict[str, Any]:
        """Provide default assessment when generation fails"""
        return {
            "overall_score": 0,
            "skill_level_assessment": SkillAssessment.INSUFFICIENT_DATA,
            "hire_recommendation": HireRecommendation.NO_HIRE,
            "detailed_feedback": f"Assessment could not be completed: {error_message}",
            "executive_summary": "Unable to generate comprehensive assessment due to technical issues.",
            "recommendations": ["Complete technical assessment required"],
            "strengths_summary": [],
            "improvement_areas": ["Technical assessment required"],
            "statistics": {"overall_score": 0, "dimension_averages": {}},
            "assessment_date": datetime.utcnow().isoformat(),
            "total_questions": 0
        }
    
    def _get_default_feedback(self, overall_score: float) -> str:
        """Generate basic feedback when AI generation fails"""
        if overall_score >= 80:
            return "Demonstrates strong Excel proficiency with good technical knowledge and problem-solving abilities. Continue building advanced skills through practical application."
        elif overall_score >= 60:
            return "Shows solid understanding of Excel fundamentals with room for improvement in advanced features. Focus on expanding formula knowledge and data analysis techniques."
        else:
            return "Basic Excel knowledge demonstrated but significant improvement needed. Recommend comprehensive Excel training covering core functions, formulas, and data management."
    
    def _update_stats(self, generation_time: float):
        """Update feedback generation statistics"""
        self.reports_generated += 1
        
        if self.average_generation_time == 0:
            self.average_generation_time = generation_time
        else:
            self.average_generation_time = (
                (self.average_generation_time * (self.reports_generated - 1) + generation_time) 
                / self.reports_generated
            )
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get feedback engine statistics"""
        return {
            "reports_generated": self.reports_generated,
            "average_generation_time": round(self.average_generation_time, 3),
            "service_status": "ready"
        }

# Global feedback engine instance
feedback_engine = FeedbackEngine()
