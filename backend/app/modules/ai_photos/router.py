import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from app.core.security import get_current_user
from app.modules.users.models import User
from app.modules.ai_photos.schemas import (
    AIPhotoJobStartResponse,
    AIPhotoJobStatusResponse,
    AIPhotoRequest,
    AIPhotoResponse,
)
from app.modules.ai_photos.service import AIPhotoService
from app.modules.notifications.service import create_notification

router = APIRouter(prefix="/ai_photos", tags=["ai_photos"])
logger = logging.getLogger(__name__)
_jobs: dict[str, AIPhotoJobStatusResponse] = {}


def get_service():
    return AIPhotoService()


async def _generate_photo_background(job_id: str, request: AIPhotoRequest, user_id: int):
    job = _jobs.get(job_id)
    if not job:
        return

    try:
        job.status = "processing"
        job.progress_message = "Đang tối ưu prompt và chuẩn bị sinh ảnh..."

        service = get_service()
        result = await service.generate(
            photo_type=request.photo_type,
            description=request.description,
            question_text=request.question_text,
            script=request.script,
            answers=request.answers,
        )

        job.status = "done"
        job.progress_message = "Sinh ảnh hoàn tất. Ảnh đã sẵn sàng để chọn."
        job.result = AIPhotoResponse(**result)
        photo_label = "ảnh hành động 2x2" if request.photo_type.value == "action" else "ảnh ngữ cảnh"
        await create_notification(
            user_id=user_id,
            title="Sinh ảnh AI hoàn tất!",
            message=f"{photo_label.capitalize()} đã được tạo xong và sẵn sàng để dùng cho câu hỏi.",
            type="success",
        )
    except HTTPException as exc:
        job.status = "failed"
        job.error = str(exc.detail)
        job.progress_message = "Sinh ảnh thất bại."
        logger.error("AI photo job %s failed: %s", job_id, exc.detail)
        await create_notification(
            user_id=user_id,
            title="Sinh ảnh AI thất bại",
            message=str(exc.detail),
            type="error",
        )
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)
        job.progress_message = "Sinh ảnh thất bại."
        logger.error("AI photo job %s failed: %s", job_id, exc, exc_info=True)
        await create_notification(
            user_id=user_id,
            title="Sinh ảnh AI thất bại",
            message=str(exc),
            type="error",
        )


@router.post("/generate", response_model=AIPhotoResponse)
async def generate_ai_photo(
    request: AIPhotoRequest,
    service: AIPhotoService = Depends(get_service),
    _: User = Depends(get_current_user),
):
    """
    Generate an AI JLPT photo.
    - **context**: 1 image summarising the scene from script + answers + description.
    - **action**: 4 images (one per answer A/B/C/D) stitched into a 2×2 grid.
    """
    try:
        result = await service.generate(
            photo_type=request.photo_type,
            description=request.description,
            question_text=request.question_text,
            script=request.script,
            answers=request.answers,
        )
        return AIPhotoResponse(**result)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/generate-async",
    response_model=AIPhotoJobStartResponse,
    status_code=202,
    summary="Generate an AI JLPT photo in the background",
)
async def generate_ai_photo_async(
    request: AIPhotoRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Start AI photo generation as a background job.
    Returns a `job_id` so the frontend can poll progress without holding a long request open.
    """
    job_id = str(uuid.uuid4())
    _jobs[job_id] = AIPhotoJobStatusResponse(
        job_id=job_id,
        status="pending",
        progress_message="Đã xếp hàng sinh ảnh AI...",
    )
    background_tasks.add_task(_generate_photo_background, job_id, request, current_user.id)
    return AIPhotoJobStartResponse(
        job_id=job_id,
        status="pending",
        progress_message="Đã xếp hàng sinh ảnh AI...",
    )


@router.get("/job/{job_id}", response_model=AIPhotoJobStatusResponse)
async def get_ai_photo_job_status(
    job_id: str,
    _: User = Depends(get_current_user),
):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.delete("/job/{job_id}", status_code=204)
async def delete_ai_photo_job(
    job_id: str,
    _: User = Depends(get_current_user),
):
    if job_id in _jobs:
        del _jobs[job_id]
