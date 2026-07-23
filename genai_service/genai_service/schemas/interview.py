"""Interview question and session Pydantic schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from genai_service.schemas.enums import DifficultyLevel, InterviewStatus, QuestionCategory


class QuestionMetadata(BaseModel):
    question: str
    skill: str
    difficulty: DifficultyLevel
    category: QuestionCategory = QuestionCategory.BASIC
    expected_topics: list[str] = Field(default_factory=list)
    estimated_time_seconds: int = Field(default=120, ge=30, le=600)
    question_number: int = 0
    rationale: str = Field(
        default="",
        description="Why this question was chosen from the resume",
    )


class StartInterviewRequest(BaseModel):
    candidate_id: str
    max_questions: int | None = None
    time_limit_minutes: int | None = None
    starting_difficulty: DifficultyLevel = DifficultyLevel.MEDIUM


class StartInterviewResponse(BaseModel):
    interview_id: str
    session_id: str
    candidate_name: str
    skills: list[str]
    difficulty_level: DifficultyLevel
    max_questions: int
    time_limit_minutes: int
    question: QuestionMetadata
    interview_status: InterviewStatus
    started_at: datetime


class NextQuestionResponse(BaseModel):
    interview_id: str
    question: QuestionMetadata | None
    question_number: int
    remaining_questions: int
    difficulty_level: DifficultyLevel
    interview_status: InterviewStatus
    message: str = ""


class SubmitAnswerRequest(BaseModel):
    interview_id: str
    answer: str = Field(..., min_length=1, max_length=20000)


class QuestionHistoryItem(BaseModel):
    question_number: int
    question: str
    skill: str
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    category: QuestionCategory | str = QuestionCategory.THEORY
    candidate_answer: str = ""
    correct_answer: str = ""
    score: float = 0.0
    percentage: float = 0.0
    feedback: str = ""
    timestamp: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
