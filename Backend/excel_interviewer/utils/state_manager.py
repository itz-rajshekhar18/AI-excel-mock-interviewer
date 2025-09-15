"""
State Manager for Excel Mock Interviewer
"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import redis.asyncio as redis

class StateManager:
    """Manages interview session state with Redis backend and memory fallback"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.memory_store: Dict[str, Any] = {}
        self.is_redis_available = False
        
    async def initialize(self):
        """Initialize state manager with Redis connection"""
        try:
            self.redis_client = redis.Redis.from_url(settings.redis_url)
            await self.redis_client.ping()
            self.is_redis_available = True
            logger.info("✅ Redis state manager initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ Redis not available, using memory fallback: {e}")
            self.is_redis_available = False
    
    async def set_interview_state(self, interview_id: str, state: Dict[str, Any], ttl: int = 7200) -> bool:
        """Store interview state with TTL"""
        try:
            state["last_updated"] = datetime.utcnow().isoformat()
            
            if self.is_redis_available and self.redis_client:
                key = f"interview:{interview_id}"
                serialized_state = json.dumps(state, default=str)
                await self.redis_client.setex(key, ttl, serialized_state)
            else:
                self.memory_store[f"interview:{interview_id}"] = {
                    "data": state,
                    "expires_at": datetime.utcnow() + timedelta(seconds=ttl)
                }
            return True
        except Exception as e:
            logger.error(f"Error storing interview state {interview_id}: {e}")
            return False
    
    async def get_interview_state(self, interview_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve interview state"""
        try:
            if self.is_redis_available and self.redis_client:
                key = f"interview:{interview_id}"
                serialized_state = await self.redis_client.get(key)
                if serialized_state:
                    return json.loads(serialized_state)
            else:
                key = f"interview:{interview_id}"
                if key in self.memory_store:
                    stored_data = self.memory_store[key]
                    if datetime.utcnow() < stored_data["expires_at"]:
                        return stored_data["data"]
            return None
        except Exception as e:
            logger.error(f"Error retrieving interview state {interview_id}: {e}")
            return None

# Global state manager instance
state_manager = StateManager()
