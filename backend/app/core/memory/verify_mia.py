import asyncio
import logging
from app.core.memory.planner import MIAPlanner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_mia_flow():
    planner = MIAPlanner()
    
    # Test 1: Planning a task (should retrieve seeded procedural memory)
    logger.info("Testing task planning...")
    enriched_prompt = await planner.plan_task(
        task_type="ai_photo_context",
        user_input="A student studying Japanese in a library.",
        user_id=1
    )
    logger.info(f"Enriched Prompt Output:\n{enriched_prompt}")
    
    if "Successful strategies from memory" in enriched_prompt:
        logger.info("✅ Procedural memory retrieval successful!")
    else:
        logger.error("❌ Procedural memory retrieval failed.")

    # Test 2: Providing feedback (storing historical memory)
    logger.info("Testing feedback storage...")
    await planner.provide_feedback(
        task_type="ai_photo_context",
        strategy="Manga style drawing of a library",
        quality=0.9,
        user_id=1,
        interaction="A student studying Japanese in a library."
    )
    logger.info("✅ Feedback stored.")

    # Test 3: Retrieving historical memory
    logger.info("Testing historical memory retrieval...")
    enriched_with_history = await planner.plan_task(
        task_type="ai_photo_context",
        user_input="Another library scene",
        user_id=1
    )
    logger.info(f"Enriched Prompt with History:\n{enriched_with_history}")
    
    if "User's historical context" in enriched_with_history:
        logger.info("✅ Historical memory retrieval successful!")
    else:
        logger.error("❌ Historical memory retrieval failed.")

if __name__ == "__main__":
    asyncio.run(verify_mia_flow())
