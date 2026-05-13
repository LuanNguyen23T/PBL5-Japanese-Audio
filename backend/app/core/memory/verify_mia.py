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

    # Test 4: Storing and Retrieving Knowledge for Chatbot
    logger.info("Testing Knowledge Memory for Chatbot...")
    chat_context = await planner.plan_chat_response(
        user_input="How do I use ba yokatta?",
        user_id=1
    )
    logger.info(f"Chat Context Output:\n{chat_context}")
    if "ba yokatta" in chat_context:
        logger.info("✅ Knowledge retrieval successful!")
    else:
        logger.error("❌ Knowledge retrieval failed.")

    # Test 5: Storing and Retrieving Learning History for Assessment
    logger.info("Testing Learning History for Capability Assessment...")
    await planner.memory.store_learning_history(
        user_id=1,
        exam_id=101,
        score=45.5,
        evaluation="User struggled with N4 transitive verbs and fast-paced station announcements."
    )
    
    assessment_context = await planner.assess_capability(user_id=1)
    logger.info(f"Assessment Context Output:\n{assessment_context}")
    if "station announcements" in assessment_context:
        logger.info("✅ Learning history retrieval successful!")
    else:
        logger.error("❌ Learning history retrieval failed.")

if __name__ == "__main__":
    asyncio.run(verify_mia_flow())
