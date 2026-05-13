import asyncio
import logging
from app.core.memory.memory_manager import MemoryManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_initial_memory():
    memory = MemoryManager()
    
    # 1. Seed Procedural Memory for AI Photos
    # These are "strategies" that have worked well in the past for Flux/Stable Diffusion
    photo_strategies = [
        {
            "strategy": "Use 'monochrome black and white manga-style' and 'clean lineart' for JLPT illustrations. Focus on 1-2 characters in a classroom or station setting.",
            "task_type": "ai_photo_context",
            "quality": 0.95
        },
        {
            "strategy": "For action shots, emphasize the verb in the prompt. Use 'dynamic pose' and 'clear primary action'. Avoid crowds.",
            "task_type": "ai_photo_action",
            "quality": 0.90
        }
    ]
    
    for s in photo_strategies:
        await memory.store_procedural(
            task_type=s["task_type"],
            strategy=s["strategy"],
            result_quality=s["quality"]
        )
        logger.info(f"Seeded procedural memory for {s['task_type']}")

    # 2. Seed Procedural Memory for AI Exams
    exam_strategies = [
        {
            "strategy": "Identify 'Mondai' markers using regex first, then use ReazonSpeech transcripts to refine sentence boundaries. Look for question particles like 'ka' at the end of sentences.",
            "task_type": "ai_exam_generation",
            "quality": 0.92
        }
    ]
    
    for s in exam_strategies:
        await memory.store_procedural(
            task_type=s["task_type"],
            strategy=s["strategy"],
            result_quality=s["quality"]
        )
        logger.info(f"Seeded procedural memory for {s['task_type']}")

    # 3. Seed Contextual Knowledge (Grammar, Vocabulary, Scripts)
    knowledge_items = [
        {
            "domain": "grammar",
            "content": "Rule [~ba yokatta]: Used to express regret about something that didn't happen in the past. Example: 'Motto benkyou sureba yokatta' (I should have studied more)."
        },
        {
            "domain": "grammar",
            "content": "Rule [~te iru]: Used to express an ongoing action or a state resulting from a past action. Example: 'Kare wa ima hon wo yonde iru' (He is reading a book now) or 'Kekkon shite iru' (is married)."
        },
        {
            "domain": "vocabulary",
            "content": "Station context: 'Kaisatsuguchi' (Ticket gate), 'Houmu' (Platform), 'Shuuten' (Terminal/Last stop). Often used in N4/N3 listening tests."
        },
        {
            "domain": "conversation_script",
            "content": "Classroom instruction pattern: 1. Teacher gets attention ('Minasan, chotto kitte kudasai'). 2. Explains the task ('Kyou wa 50-peeji kara desu'). 3. Sets a deadline or rule ('Ashita made ni dashite kudasai')."
        }
    ]

    for k in knowledge_items:
        await memory.store_knowledge(
            domain=k["domain"],
            content=k["content"]
        )
        logger.info(f"Seeded knowledge memory in domain {k['domain']}")

    logger.info("Memory seeding completed successfully.")

if __name__ == "__main__":
    asyncio.run(seed_initial_memory())
