"""
Conversation Manager - Controls interview flow and conversation logic
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import uuid

from excel_interviewer.models.interview import Interview, InterviewStatus
from excel_interviewer.models.question import ExcelQuestion, QuestionResponse
from excel_interviewer.services.question_bank import question_bank
from excel_interviewer.services.excel_evaluator import excel_evaluator
from excel_interviewer.utils.state_manager import state_manager
from excel_interviewer.utils.config import settings

logger = logging.getLogger(__name__)

class ConversationManager:
    """Manages interview conversation flow and state"""
    
    def __init__(self):
        self.active_interviews = {}
        
    async def start_interview(self, interview: Interview) -> Dict[str, Any]:
        """Initialize a new interview session"""
        try:
            # Initialize interview state
            initial_state = {
                "interview_id": interview.id,
                "candidate_name": interview.candidate_name,
                "position": interview.position,
                "skill_level": interview.skill_level,
                "status": InterviewStatus.IN_PROGRESS,
                "current_question_index": 0,
                "questions_asked": [],
                "responses": [],
                "scores": [],
                "current_difficulty": interview.skill_level,
                "start_time": datetime.utcnow().isoformat(),
                "conversation_history": []
            }
            
            # Store state
            await state_manager.set_interview_state(interview.id, initial_state)
            
            # Generate welcome message and first question
            welcome_message = self._generate_welcome_message(
                interview.candidate_name, interview.position
            )
            first_question = await self._get_next_question(interview.id, initial_state)
            
            if first_question:
                initial_state["current_question"] = first_question.dict()
                initial_state["questions_asked"].append(first_question.id)
                await state_manager.set_interview_state(interview.id, initial_state)
                
                return {
                    "status": "success",
                    "message": welcome_message,
                    "question": first_question.dict(),
                    "interview_id": interview.id
                }
            else:
                raise Exception("Could not generate first question")
                
        except Exception as e:
            logger.error(f"Error starting interview: {e}")
            return {
                "status": "error",
                "message": "Failed to start interview. Please try again.",
                "error": str(e)
            }
    
    async def process_response(
        self, 
        interview_id: str, 
        candidate_response: str,
        response_time_seconds: float = 0
    ) -> Dict[str, Any]:
        """Process candidate's response and generate next question"""
        try:
            # Get current interview state
            state = await state_manager.get_interview_state(interview_id)
            if not state:
                return {"status": "error", "message": "Interview session not found"}
            
            current_question = state.get("current_question")
            if not current_question:
                return {"status": "error", "message": "No active question found"}
            
            # Evaluate the response
            evaluation = await excel_evaluator.evaluate_response(
                question_text=current_question["question_text"],
                candidate_response=candidate_response,
                difficulty=state["current_difficulty"],
                question_type=current_question["question_type"]
            )
            
            # Store response and evaluation
            response_data = {
                "question_id": current_question["id"],
                "question_text": current_question["question_text"],
                "candidate_response": candidate_response,
                "evaluation": evaluation,
                "response_time": response_time_seconds,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            state["responses"].append(response_data)
            state["scores"].append(evaluation["overall_score"])
            state["current_question_index"] += 1
            
            # Update conversation history
            state["conversation_history"].extend([
                {"role": "assistant", "content": current_question["question_text"]},
                {"role": "user", "content": candidate_response},
                {"role": "system", "content": f"Score: {evaluation['overall_score']}/100"}
            ])
            
            # Update question statistics
            question_bank.update_question_stats(
                current_question["id"], 
                evaluation["overall_score"],
                response_time_seconds
            )
            
            # Update difficulty based on performance
            new_difficulty = self._adjust_difficulty(state["scores"], state["current_difficulty"])
            state["current_difficulty"] = new_difficulty
            
            # Check if interview should continue
            should_continue = self._should_continue_interview(state)
            
            if should_continue:
                # Get next question
                next_question = await self._get_next_question(interview_id, state)
                
                if next_question:
                    state["current_question"] = next_question.dict()
                    state["questions_asked"].append(next_question.id)
                    await state_manager.set_interview_state(interview_id, state)
                    
                    return {
                        "status": "continue",
                        "evaluation": evaluation,
                        "next_question": next_question.dict(),
                        "progress": {
                            "questions_completed": len(state["responses"]),
                            "total_questions": 15,
                            "average_score": sum(state["scores"]) / len(state["scores"]),
                            "current_difficulty": new_difficulty
                        }
                    }
                else:
                    # No more questions available, end interview
                    return await self._end_interview(interview_id, state)
            else:
                # Interview complete
                return await self._end_interview(interview_id, state)
                
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            return {
                "status": "error", 
                "message": "Failed to process response. Please try again.",
                "error": str(e)
            }
    
    async def _get_next_question(self, interview_id: str, state: Dict) -> Optional[ExcelQuestion]:
        """Get the next appropriate question based on performance"""
        try:
            current_difficulty = state.get("current_difficulty", "intermediate")
            previous_scores = state.get("scores", [])
            asked_question_ids = state.get("questions_asked", [])
            
            # Get adaptive question
            question = question_bank.get_adaptive_question(
                current_difficulty=current_difficulty,
                previous_scores=previous_scores,
                asked_question_ids=asked_question_ids
            )
            
            return question
            
        except Exception as e:
            logger.error(f"Error getting next question: {e}")
            return None
    
    def _adjust_difficulty(self, scores: List[float], current_difficulty: str) -> str:
        """Adjust difficulty based on recent performance"""
        if not scores:
            return current_difficulty
        
        # Look at last 3 scores for trend
        recent_scores = scores[-3:] if len(scores) >= 3 else scores
        avg_recent = sum(recent_scores) / len(recent_scores)
        
        # Difficulty adjustment logic
        if avg_recent >= 85 and current_difficulty != "advanced":
            if current_difficulty == "basic":
                return "intermediate"
            elif current_difficulty == "intermediate":
                return "advanced"
        elif avg_recent < 40 and current_difficulty != "basic":
            if current_difficulty == "advanced":
                return "intermediate"
            elif current_difficulty == "intermediate":
                return "basic"
        
        return current_difficulty
    
    def _should_continue_interview(self, state: Dict) -> bool:
        """Determine if interview should continue"""
        questions_asked = len(state.get("responses", []))
        max_questions = 15
        
        # Continue if under question limit
        if questions_asked < max_questions:
            # Check for early termination conditions
            scores = state.get("scores", [])
            if len(scores) >= 5:
                avg_score = sum(scores) / len(scores)
                # End early if consistently very low performance
                if avg_score < 25:
                    logger.info(f"Ending interview early due to low performance: {avg_score}")
                    return False
        
        return questions_asked < max_questions
    
    async def _end_interview(self, interview_id: str, state: Dict) -> Dict[str, Any]:
        """End the interview and generate final assessment"""
        try:
            from excel_interviewer.services.feedback_engine import feedback_engine
            
            # Mark interview as completed
            state["status"] = InterviewStatus.COMPLETED
            state["end_time"] = datetime.utcnow().isoformat()
            
            # Generate final assessment
            final_assessment = await feedback_engine.generate_final_assessment(
                interview_id, state["responses"]
            )
            
            state["final_assessment"] = final_assessment
            await state_manager.set_interview_state(interview_id, state)
            
            return {
                "status": "completed",
                "message": "Interview completed successfully!",
                "final_assessment": final_assessment,
                "summary": {
                    "questions_completed": len(state["responses"]),
                    "overall_score": final_assessment.get("overall_score", 0),
                    "skill_level": final_assessment.get("skill_level_assessment", "intermediate"),
                    "hire_recommendation": final_assessment.get("hire_recommendation", "no_hire"),
                    "duration_minutes": self._calculate_duration(state)
                }
            }
            
        except Exception as e:
            logger.error(f"Error ending interview: {e}")
            return {
                "status": "error",
                "message": "Failed to complete interview assessment.",
                "error": str(e)
            }
    
    def _calculate_duration(self, state: Dict) -> int:
        """Calculate interview duration in minutes"""
        try:
            start_time = datetime.fromisoformat(state["start_time"])
            end_time = datetime.fromisoformat(state["end_time"])
            duration = end_time - start_time
            return int(duration.total_seconds() / 60)
        except:
            return 0
    
    def _generate_welcome_message(self, candidate_name: str, position: str) -> str:
        """Generate personalized welcome message"""
        return f"""Hello {candidate_name}! Welcome to your Excel skills assessment for the {position} role.

I'm your AI interviewer, and I'll be evaluating your Excel proficiency through a series of questions.

Here's what to expect:
• 10-15 questions covering formulas, data analysis, and problem-solving
• Questions will adapt to your skill level based on your responses
• Take your time to provide detailed, thoughtful answers
• Explain your reasoning and approach when possible

The assessment typically takes 30-45 minutes. Ready to begin?"""
    
    async def get_interview_status(self, interview_id: str) -> Dict[str, Any]:
        """Get current interview status and progress"""
        try:
            state = await state_manager.get_interview_state(interview_id)
            if not state:
                return {"status": "not_found", "message": "Interview not found"}
            
            return {
                "status": "success",
                "interview_status": state.get("status", "unknown"),
                "progress": {
                    "questions_completed": len(state.get("responses", [])),
                    "total_questions": 15,
                    "current_question_index": state.get("current_question_index", 0),
                    "average_score": sum(state.get("scores", [])) / len(state.get("scores", [])) if state.get("scores") else 0,
                    "current_difficulty": state.get("current_difficulty", "intermediate")
                },
                "current_question": state.get("current_question"),
                "conversation_history": state.get("conversation_history", [])[-10:]  # Last 10 messages
            }
            
        except Exception as e:
            logger.error(f"Error getting interview status: {e}")
            return {"status": "error", "message": "Failed to get interview status"}
    
    async def pause_interview(self, interview_id: str) -> Dict[str, Any]:
        """Pause an active interview"""
        try:
            state = await state_manager.get_interview_state(interview_id)
            if not state:
                return {"status": "error", "message": "Interview not found"}
            
            if state.get("status") != InterviewStatus.IN_PROGRESS:
                return {"status": "error", "message": "Interview is not in progress"}
            
            state["status"] = InterviewStatus.PAUSED
            state["paused_at"] = datetime.utcnow().isoformat()
            await state_manager.set_interview_state(interview_id, state)
            
            return {"status": "success", "message": "Interview paused successfully"}
            
        except Exception as e:
            logger.error(f"Error pausing interview: {e}")
            return {"status": "error", "message": "Failed to pause interview"}
    
    async def resume_interview(self, interview_id: str) -> Dict[str, Any]:
        """Resume a paused interview"""
        try:
            state = await state_manager.get_interview_state(interview_id)
            if not state:
                return {"status": "error", "message": "Interview not found"}
            
            if state.get("status") != InterviewStatus.PAUSED:
                return {"status": "error", "message": "Interview is not paused"}
            
            state["status"] = InterviewStatus.IN_PROGRESS
            state["resumed_at"] = datetime.utcnow().isoformat()
            await state_manager.set_interview_state(interview_id, state)
            
            current_question = state.get("current_question")
            return {
                "status": "success", 
                "message": "Interview resumed successfully",
                "current_question": current_question
            }
            
        except Exception as e:
            logger.error(f"Error resuming interview: {e}")
            return {"status": "error", "message": "Failed to resume interview"}
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation manager statistics"""
        return {
            "active_interviews": len(self.active_interviews),
            "service_status": "ready"
        }

# Global conversation manager instance
conversation_manager = ConversationManager()
