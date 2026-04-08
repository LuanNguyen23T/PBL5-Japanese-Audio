from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user
from app.modules.users.models import User
from app.modules.ai_photos.schemas import AIPhotoRequest, AIPhotoResponse
from app.modules.ai_photos.service import AIPhotoService

router = APIRouter(prefix="/ai_photos", tags=["ai_photos"])

def get_service():
    return AIPhotoService()

@router.post("/generate", response_model=AIPhotoResponse)
async def generate_ai_photo(
    request: AIPhotoRequest,
    service: AIPhotoService = Depends(get_service),
    _: User = Depends(get_current_user),
):
    """
    Generate an AI JLPT photo based on a prompt and type.
    """
    try:
        result = await service.generate(user_prompt=request.prompt, photo_type=request.photo_type)
        return AIPhotoResponse(**result)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
