"""LangGraph interview state definition."""

from datetime import datetime
from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages

from genai_service.schemas.enums import DifficultyLevel, InterviewStatus


def merge_lists(left: list, right: list) -> list:
    """Reducer that appends new items while preserving order."""
    return list(left or []) + list(right or [])


def overwrite(left: Any, right: Any) -> Any:
    """Reducer that prefers the latest non-None value."""
    return right if right is not None else left


class InterviewState(TypedDict, total=False):
    """Complete interview state maintained across LangGraph nodes."""

    # Identity
    session_id: str
    interview_id: str
    candidate_id: str
    candidate_name: str

    # Resume context
    resume_text: str
    skills: list[str]
    projects: list[dict[str, Any]]
    experience: list[dict[str, Any]]
    education: list[dict[str, Any]]
    certificates: list[dict[str, Any]]
    achievements: list[str]
    primary_domains: list[str]
    years_of_experience: float

    # Interview control
    difficulty_level: str
    max_questions: int
    time_limit_minutes: int
    question_number: int
    interview_status: str

    # Current turn
    current_question: dict[str, Any]
    candidate_answer: str
    correct_answer: str
    evaluation: dict[str, Any]
    score: float
    overall_score: float
    difficulty_decision: dict[str, Any]

    # Histories (append-only via reducer where used in graph)
    question_history: Annotated[list[dict[str, Any]], merge_lists]
    answer_history: Annotated[list[str], merge_lists]
    feedback_history: Annotated[list[str], merge_lists]
    score_history: Annotated[list[float], merge_lists]
    difficulty_history: Annotated[list[str], merge_lists]

    # Aggregates
    strengths: list[str]
    weaknesses: list[str]
    recommendation: str
    final_report: dict[str, Any]

    # Timestamps
    started_at: str
    updated_at: str
    ended_at: str

    # Internal
    asked_question_texts: list[str]
    error: str
    messages: Annotated[list, add_messages]


def create_initial_state(
    *,
    session_id: str,
    interview_id: str,
    candidate_id: str,
    candidate_name: str,
    resume_text: str,
    skills: list[str],
    projects: list[dict[str, Any]],
    experience: list[dict[str, Any]],
    education: list[dict[str, Any]],
    certificates: list[dict[str, Any]] | None = None,
    achievements: list[str] | None = None,
    primary_domains: list[str] | None = None,
    years_of_experience: float = 0.0,
    difficulty_level: DifficultyLevel = DifficultyLevel.MEDIUM,
    max_questions: int = 15,
    time_limit_minutes: int = 30,
) -> InterviewState:
    now = datetime.utcnow().isoformat()
    return InterviewState(
        session_id=session_id,
        interview_id=interview_id,
        candidate_id=candidate_id,
        candidate_name=candidate_name,
        resume_text=resume_text,
        skills=skills,
        projects=projects,
        experience=experience,
        education=education,
        certificates=certificates or [],
        achievements=achievements or [],
        primary_domains=primary_domains or [],
        years_of_experience=years_of_experience,
        difficulty_level=difficulty_level.value,
        max_questions=max_questions,
        time_limit_minutes=time_limit_minutes,
        question_number=0,
        interview_status=InterviewStatus.CREATED.value,
        current_question={},
        candidate_answer="",
        correct_answer="",
        evaluation={},
        score=0.0,
        overall_score=0.0,
        difficulty_decision={},
        question_history=[],
        answer_history=[],
        feedback_history=[],
        score_history=[],
        difficulty_history=[],
        strengths=[],
        weaknesses=[],
        recommendation="",
        final_report={},
        started_at=now,
        updated_at=now,
        ended_at="",
        asked_question_texts=[],
        error="",
        messages=[],
    )
