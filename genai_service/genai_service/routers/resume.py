"""Resume API router."""

from __future__ import annotations

from fastapi import APIRouter, File, Form, UploadFile

from genai_service.schemas.api import APIResponse
from genai_service.schemas.resume import UploadResumeResponse
from genai_service.services.interview_service import InterviewService
from genai_service.utils.exceptions import ResumeParseError, ValidationError

router = APIRouter(tags=["Resume"])


@router.post("/upload_resume", response_model=APIResponse[UploadResumeResponse])
async def upload_resume(
    file: UploadFile | None = File(default=None),
    resume_text: str | None = Form(default=None),
) -> APIResponse[UploadResumeResponse]:
    """Upload a resume file (PDF/DOCX/TXT) or paste raw resume text."""
    service = InterviewService()

    if file is not None and file.filename:
        content = await file.read()
        if not content:
            raise ResumeParseError("Uploaded file is empty")
        data = await service.upload_resume_file(content=content, filename=file.filename)
    elif resume_text and resume_text.strip():
        data = await service.upload_resume_text(resume_text)
    else:
        raise ValidationError("Provide either a resume file or resume_text")

    return APIResponse(success=True, data=data, message="Resume uploaded and parsed")
