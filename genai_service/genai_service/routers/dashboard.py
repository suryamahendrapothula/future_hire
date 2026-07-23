"""Admin dashboard API router."""

from __future__ import annotations

from fastapi import APIRouter

from genai_service.schemas.api import APIResponse
from genai_service.schemas.report import (
    CandidateSummary,
    ChatHistoryResponse,
    DashboardData,
)
from genai_service.services.interview_service import InterviewService

router = APIRouter(tags=["Dashboard"])


@router.get(
    "/dashboard/candidates",
    response_model=APIResponse[list[CandidateSummary]],
)
async def list_candidates() -> APIResponse[list[CandidateSummary]]:
    """Return all candidates who have participated in at least one interview."""
    service = InterviewService()
    data = await service.list_candidates()
    return APIResponse(success=True, data=data, message="Candidates retrieved")


@router.get(
    "/dashboard/chat-history/{interview_id}",
    response_model=APIResponse[ChatHistoryResponse],
)
async def get_chat_history(
    interview_id: str,
) -> APIResponse[ChatHistoryResponse]:
    """Return the full Q&A chat log for a specific interview."""
    service = InterviewService()
    data = await service.get_chat_history(interview_id)
    return APIResponse(success=True, data=data, message="Chat history retrieved")


@router.get(
    "/dashboard/{candidate_id}",
    response_model=APIResponse[DashboardData],
)
async def get_dashboard(
    candidate_id: str,
) -> APIResponse[DashboardData]:
    service = InterviewService()
    data = await service.get_dashboard(candidate_id)
    return APIResponse(success=True, data=data, message="Dashboard data retrieved")
