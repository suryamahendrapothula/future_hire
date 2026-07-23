"""Interview API router."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from genai_service.schemas.api import APIResponse
from genai_service.schemas.evaluation import SubmitAnswerResponse
from genai_service.schemas.interview import (
    NextQuestionResponse,
    StartInterviewRequest,
    StartInterviewResponse,
    SubmitAnswerRequest,
)
from genai_service.schemas.report import EndInterviewResponse, InterviewDetailResponse
from genai_service.services.interview_service import InterviewService

router = APIRouter(tags=["Interview"])


class InterviewIdBody(BaseModel):
    interview_id: str = Field(..., min_length=1)


@router.post("/start_interview", response_model=APIResponse[StartInterviewResponse])
async def start_interview(
    body: StartInterviewRequest,
) -> APIResponse[StartInterviewResponse]:
    service = InterviewService()
    data = await service.start(body)
    return APIResponse(success=True, data=data, message="Interview started")


@router.post("/next_question", response_model=APIResponse[NextQuestionResponse])
async def next_question(
    body: InterviewIdBody,
) -> APIResponse[NextQuestionResponse]:
    service = InterviewService()
    data = await service.next_question(body.interview_id)
    return APIResponse(success=True, data=data, message=data.message)


@router.post("/submit_answer", response_model=APIResponse[SubmitAnswerResponse])
async def submit_answer(
    body: SubmitAnswerRequest,
) -> APIResponse[SubmitAnswerResponse]:
    service = InterviewService()
    data = await service.submit_answer(body.interview_id, body.answer)
    return APIResponse(success=True, data=data, message=data.message)


@router.post("/end_interview", response_model=APIResponse[EndInterviewResponse])
async def end_interview(
    body: InterviewIdBody,
) -> APIResponse[EndInterviewResponse]:
    service = InterviewService()
    data = await service.end_interview(body.interview_id)
    return APIResponse(success=True, data=data, message=data.message)


@router.get("/interview/{interview_id}", response_model=APIResponse[InterviewDetailResponse])
async def get_interview(
    interview_id: str,
) -> APIResponse[InterviewDetailResponse]:
    service = InterviewService()
    data = await service.get_interview(interview_id)
    return APIResponse(success=True, data=data, message="Interview retrieved")
