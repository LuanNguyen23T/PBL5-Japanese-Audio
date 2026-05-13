import logging
from typing import Optional, List
from app.core.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

class MIAPlanner:
    def __init__(self):
        self.memory = MemoryManager()

    async def plan_task(
        self, 
        task_type: str, 
        user_input: str, 
        user_id: Optional[int] = None,
        context: Optional[dict] = None
    ) -> str:
        """
        Create a plan for the task by retrieving relevant memories and knowledge.
        Returns an enriched prompt or instructions for the executor.
        """
        # 1. Retrieve procedural strategies (few-shot examples)
        strategies = await self.memory.retrieve_procedural(task_type, user_input, limit=2)
        
        # 2. Retrieve user history if user_id is provided
        history = []
        if user_id:
            history = await self.memory.retrieve_historical(user_id, user_input, limit=3)

        # 3. Build the enriched prompt
        enriched_prompt = f"### Task Type: {task_type}\n"
        enriched_prompt += f"### User Request: {user_input}\n\n"

        if strategies:
            enriched_prompt += "### Successful strategies from memory:\n"
            for s in strategies:
                enriched_prompt += f"- Strategy: {s['strategy']}\n"
        
        if history:
            enriched_prompt += "\n### User's historical context:\n"
            for h in history:
                enriched_prompt += f"- Past Interaction: {h['interaction']} (Feedback: {h['metadata'].get('feedback', 'none')})\n"

        if context:
            enriched_prompt += f"\n### Additional Context: {context}\n"

        return enriched_prompt

    async def provide_feedback(
        self, 
        task_type: str, 
        strategy: str, 
        quality: float, 
        user_id: Optional[int] = None,
        interaction: Optional[str] = None
    ):
        """Update memory based on the outcome of a task."""
        await self.memory.store_procedural(task_type, strategy, quality)
        if user_id and interaction:
            await self.memory.store_historical(user_id, interaction, feedback="success" if quality > 0.7 else "failure")
