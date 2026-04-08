from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class PhotoType(str, Enum):
    context = "context"
    action = "action"

class AIPhotoRequest(BaseModel):
    prompt: str = Field(..., description="User description for the image context or action")
    photo_type: PhotoType = Field(..., description="Type of generation: context (1 image) or action (4 images grid)")

class AIPhotoResponse(BaseModel):
    b64_image: str = Field(..., description="Base64 encoded image string (JPEG or PNG)")
    info: Optional[str] = Field(None, description="Additional info or prompt used")
    storage_path: Optional[str] = Field(None, description="Temporary local file path where the generated image was stored")
