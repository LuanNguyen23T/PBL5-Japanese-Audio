from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.test.schemas import TestExamDetailResponse, TestSubmitRequest, TestSubmitResponse
from app.modules.test.service import TestService

router = APIRouter(prefix="/demo", tags=["demo"])


def get_test_service(db: AsyncSession = Depends(get_db)) -> TestService:
    return TestService(db)


@router.get("/exam", response_model=TestExamDetailResponse)
async def get_demo_exam(service: TestService = Depends(get_test_service)):
    """Return one published exam for unauthenticated trial users."""
    return await service.get_demo_exam()


@router.post("/exams/{exam_id}/submit", response_model=TestSubmitResponse)
async def submit_demo_exam(
    exam_id: UUID,
    payload: TestSubmitRequest,
    service: TestService = Depends(get_test_service),
):
    """Grade a demo submission without storing history or requiring login."""
    return await service.submit_demo_exam(exam_id, payload)
