import logging
import uuid
from typing import Optional, Any
from app.core.memory.vector_db import VectorDB

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self):
        # We use different collections for different types of memory
        self.procedural_memory = VectorDB(collection_name="procedural_memory")
        self.historical_memory = VectorDB(collection_name="historical_memory")
        self.knowledge_memory = VectorDB(collection_name="knowledge_memory")
        self.learning_history_memory = VectorDB(collection_name="learning_history_memory")

    async def store_procedural(self, task_type: str, strategy: str, result_quality: float, metadata: dict = None):
        """
        Store a successful strategy in procedural memory.
        result_quality: 0.0 to 1.0 (how well this strategy worked)
        """
        if result_quality < 0.7:  # Only store high-quality strategies
            return

        mem_id = str(uuid.uuid4())
        meta = {
            "task_type": task_type,
            "quality": result_quality,
            **(metadata or {})
        }
        await self.procedural_memory.add_documents(
            ids=[mem_id],
            documents=[strategy],
            metadatas=[meta]
        )
        logger.info(f"Stored procedural memory: {mem_id} for task {task_type}")

    async def retrieve_procedural(self, task_type: str, query: str, limit: int = 3) -> list[dict]:
        """Retrieve relevant strategies for a task."""
        results = await self.procedural_memory.query(
            query_texts=[query],
            n_results=limit,
            where={"task_type": task_type}
        )
        
        memories = []
        if results and results["documents"]:
            for i in range(len(results["documents"][0])):
                memories.append({
                    "strategy": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i]
                })
        return memories

    async def store_historical(self, user_id: int, interaction: str, feedback: Optional[str] = None, metadata: dict = None):
        """Store user interaction history."""
        mem_id = str(uuid.uuid4())
        meta = {
            "user_id": user_id,
            "feedback": feedback or "none",
            **(metadata or {})
        }
        await self.historical_memory.add_documents(
            ids=[mem_id],
            documents=[interaction],
            metadatas=[meta]
        )

    async def retrieve_historical(self, user_id: int, query: str, limit: int = 5) -> list[dict]:
        """Retrieve user's historical context."""
        results = await self.historical_memory.query(
            query_texts=[query],
            n_results=limit,
            where={"user_id": user_id}
        )
        
        memories = []
        if results and results["documents"]:
            for i in range(len(results["documents"][0])):
                memories.append({
                    "interaction": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i]
                })
        return memories

    async def store_knowledge(self, domain: str, content: str, metadata: dict = None):
        """Store linguistic knowledge (grammar, vocabulary, scripts)."""
        mem_id = str(uuid.uuid4())
        meta = {
            "domain": domain,
            **(metadata or {})
        }
        await self.knowledge_memory.add_documents(
            ids=[mem_id],
            documents=[content],
            metadatas=[meta]
        )
        logger.info(f"Stored knowledge: {mem_id} in domain {domain}")

    async def retrieve_knowledge(self, query: str, domain: Optional[str] = None, limit: int = 5) -> list[dict]:
        """Retrieve relevant linguistic knowledge."""
        where_clause = {"domain": domain} if domain else None
        results = await self.knowledge_memory.query(
            query_texts=[query],
            n_results=limit,
            where=where_clause
        )
        
        knowledge = []
        if results and results["documents"]:
            for i in range(len(results["documents"][0])):
                knowledge.append({
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i]
                })
        return knowledge

    async def store_learning_history(self, user_id: int, exam_id: int, score: float, evaluation: str, metadata: dict = None):
        """Store user exam history and capability evaluation."""
        mem_id = str(uuid.uuid4())
        meta = {
            "user_id": user_id,
            "exam_id": exam_id,
            "score": score,
            **(metadata or {})
        }
        await self.learning_history_memory.add_documents(
            ids=[mem_id],
            documents=[evaluation],
            metadatas=[meta]
        )
        logger.info(f"Stored learning history: {mem_id} for user {user_id}")

    async def retrieve_learning_history(self, user_id: int, query: str = "general capability", limit: int = 5) -> list[dict]:
        """Retrieve user's learning history and evaluations."""
        results = await self.learning_history_memory.query(
            query_texts=[query],
            n_results=limit,
            where={"user_id": user_id}
        )
        
        history = []
        if results and results["documents"]:
            for i in range(len(results["documents"][0])):
                history.append({
                    "evaluation": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i]
                })
        return history
