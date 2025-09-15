"""
LLM Service for Excel Mock Interviewer
Handles OpenAI and Anthropic API interactions for AI-powered evaluation
"""
import openai
import anthropic
from typing import Dict, List, Optional, Any
import json
import logging
import asyncio
import time
from datetime import datetime

from excel_interviewer.utils.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with Large Language Models (OpenAI, Anthropic)"""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self.request_count = 0
        self.total_tokens_used = 0
        self.average_response_time = 0.0
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize LLM clients"""
        try:
            if settings.openai_api_key:
                self.openai_client = openai.AsyncOpenAI(
                    api_key=settings.openai_api_key,
                    timeout=30.0
                )
                logger.info("✅ OpenAI client initialized")
            else:
                logger.warning("⚠️  OpenAI API key not provided")
            
            if settings.anthropic_api_key:
                self.anthropic_client = anthropic.AsyncAnthropic(
                    api_key=settings.anthropic_api_key,
                    timeout=30.0
                )
                logger.info("✅ Anthropic client initialized")
            else:
                logger.info("ℹ️  Anthropic API key not provided (optional)")
                
        except Exception as e:
            logger.error(f"❌ LLM client initialization failed: {e}")
    
    async def generate_response(
        self, 
        prompt: str, 
        model: str = None, 
        max_tokens: int = None,
        temperature: float = None
    ) -> str:
        """Generate response using specified LLM"""
        model = model or settings.default_model
        max_tokens = max_tokens or settings.max_tokens
        temperature = temperature or settings.temperature
        
        start_time = time.time()
        
        try:
            if model.startswith("gpt"):
                response = await self._openai_generate(prompt, model, max_tokens, temperature)
            elif model.startswith("claude") and self.anthropic_client:
                response = await self._anthropic_generate(prompt, model, max_tokens, temperature)
            else:
                # Fallback to OpenAI GPT-4
                response = await self._openai_generate(prompt, "gpt-4", max_tokens, temperature)
            
            # Update statistics
            response_time = time.time() - start_time
            self._update_stats(response_time)
            
            return response
            
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            raise
    
    async def _openai_generate(
        self, 
        prompt: str, 
        model: str, 
        max_tokens: int, 
        temperature: float
    ) -> str:
        """Generate response using OpenAI"""
        if not self.openai_client:
            raise Exception("OpenAI client not initialized")
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert Excel interviewer and evaluator. Provide detailed, professional assessments."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                response_format={"type": "text"}
            )
            
            # Track token usage
            if hasattr(response, 'usage') and response.usage:
                self.total_tokens_used += response.usage.total_tokens
            
            return response.choices[0].message.content
            
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise Exception("API rate limit exceeded. Please try again later.")
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise Exception(f"OpenAI API error: {str(e)}")
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise
    
    async def _anthropic_generate(
        self, 
        prompt: str, 
        model: str, 
        max_tokens: int, 
        temperature: float
    ) -> str:
        """Generate response using Anthropic"""
        if not self.anthropic_client:
            raise Exception("Anthropic client not initialized")
        
        try:
            response = await self.anthropic_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except anthropic.RateLimitError as e:
            logger.error(f"Anthropic rate limit exceeded: {e}")
            raise Exception("API rate limit exceeded. Please try again later.")
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise Exception(f"Anthropic API error: {str(e)}")
        except Exception as e:
            logger.error(f"Anthropic generation error: {e}")
            raise
    
    async def evaluate_excel_response(
        self, 
        question: str, 
        candidate_response: str, 
        difficulty: str,
        question_type: str = "general"
    ) -> Dict[str, Any]:
        """Evaluate candidate's Excel response using AI"""
        
        evaluation_prompt = f"""
You are an expert Excel interviewer evaluating a candidate's response for a {difficulty} level position.

QUESTION: {question}
CANDIDATE RESPONSE: {candidate_response}
DIFFICULTY LEVEL: {difficulty}
QUESTION TYPE: {question_type}

Please evaluate the response on these criteria (0-100 scale):
1. Technical Accuracy - Correctness of Excel knowledge and formulas
2. Communication Clarity - How well they explained their approach  
3. Problem Solving Approach - Logical thinking and methodology
4. Completeness - Did they address all parts of the question
5. Efficiency - Did they suggest optimal Excel solutions

Provide:
- Detailed constructive feedback (200-300 words)
- 2-3 specific strengths
- 2-3 areas for improvement  
- Recommended next difficulty level (basic/intermediate/advanced)

Return your evaluation as JSON with this exact structure:
{{
    "technical_accuracy": <score_0_to_100>,
    "communication_clarity": <score_0_to_100>,
    "problem_solving_approach": <score_0_to_100>,
    "completeness": <score_0_to_100>,
    "efficiency": <score_0_to_100>,
    "overall_score": <average_score>,
    "feedback": "<detailed constructive feedback>",
    "strengths": ["<strength1>", "<strength2>", "<strength3>"],
    "areas_for_improvement": ["<area1>", "<area2>", "<area3>"],
    "next_difficulty_level": "<basic|intermediate|advanced>"
}}

Be thorough, fair, and focus on practical Excel skills relevant to business contexts.
Ensure the JSON is valid and properly formatted.
"""
        
        try:
            response = await self.generate_response(
                evaluation_prompt, 
                max_tokens=1200,
                temperature=0.3  # Lower temperature for more consistent evaluations
            )
            
            # Clean the response to ensure it's valid JSON
            response = response.strip()
            if response.startswith("```"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            evaluation = json.loads(response)
            
            # Validate the evaluation structure
            required_fields = [
                "technical_accuracy", "communication_clarity", "problem_solving_approach", 
                "completeness", "efficiency", "overall_score", "feedback", "strengths", 
                "areas_for_improvement", "next_difficulty_level"
            ]
            
            for field in required_fields:
                if field not in evaluation:
                    raise ValueError(f"Missing field: {field}")
            
            # Ensure scores are within valid range
            score_fields = [
                "technical_accuracy", "communication_clarity", "problem_solving_approach",
                "completeness", "efficiency", "overall_score"
            ]
            
            for field in score_fields:
                score = evaluation[field]
                if not isinstance(score, (int, float)) or score < 0 or score > 100:
                    evaluation[field] = max(0, min(100, float(score) if isinstance(score, (int, float)) else 50))
            
            # Recalculate overall score to ensure consistency
            scores = [evaluation[field] for field in score_fields[:-1]]  # Exclude overall_score
            evaluation["overall_score"] = round(sum(scores) / len(scores), 2)
            
            return evaluation
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM evaluation response: {e}")
            logger.error(f"Raw response: {response}")
            return self._get_fallback_evaluation(difficulty)
        except ValueError as e:
            logger.error(f"Invalid evaluation structure: {e}")
            return self._get_fallback_evaluation(difficulty)
        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            return self._get_fallback_evaluation(difficulty)
    
    def _get_fallback_evaluation(self, difficulty: str) -> Dict[str, Any]:
        """Provide fallback evaluation when AI fails"""
        base_scores = {"basic": 65, "intermediate": 55, "advanced": 45}
        base_score = base_scores.get(difficulty, 55)
        
        return {
            "technical_accuracy": base_score,
            "communication_clarity": base_score,
            "problem_solving_approach": base_score,
            "completeness": base_score,
            "efficiency": base_score,
            "overall_score": base_score,
            "feedback": f"Unable to fully evaluate response due to technical issues. Based on {difficulty} level expectations, this appears to be a reasonable attempt. Please provide more specific Excel details for better assessment.",
            "strengths": ["Attempted to answer the question", "Showed understanding of the problem"],
            "areas_for_improvement": [
                "Provide specific Excel formulas and functions",
                "Explain step-by-step process",
                "Include practical examples"
            ],
            "next_difficulty_level": difficulty
        }
    
    def _update_stats(self, response_time: float):
        """Update service statistics"""
        self.request_count += 1
        
        # Update average response time
        if self.average_response_time == 0:
            self.average_response_time = response_time
        else:
            self.average_response_time = (
                (self.average_response_time * (self.request_count - 1) + response_time) 
                / self.request_count
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service usage statistics"""
        return {
            "request_count": self.request_count,
            "total_tokens_used": self.total_tokens_used,
            "average_response_time": round(self.average_response_time, 3),
            "openai_configured": bool(self.openai_client),
            "anthropic_configured": bool(self.anthropic_client)
        }

# Global LLM service instance
llm_service = LLMService()
