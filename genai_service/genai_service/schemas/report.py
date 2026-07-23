"""Final report and dashboard Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from genai_service.schemas.enums import HiringRecommendation
from genai_service.schemas.interview import QuestionHistoryItem


class SkillScore(BaseModel):
    skill: str
    score: float = Field(..., ge=0, le=100)
    questions_asked: int = 0
    average_difficulty: str = ""


class SoftSkillScores(BaseModel):
    communication: float = Field(default=0.0, ge=0, le=100)
    problem_solving: float = Field(default=0.0, ge=0, le=100)
    confidence: float = Field(default=0.0, ge=0, le=100)
    technical_accuracy: float = Field(default=0.0, ge=0, le=100)


class FinalReport(BaseModel):
    interview_id: str
    candidate_id: str
    candidate_name: str
    overall_score: float = Field(..., ge=0, le=100)
    skill_wise_scores: list[SkillScore] = Field(default_factory=list)
    soft_skills: SoftSkillScores = Field(default_factory=SoftSkillScores)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    topics_to_improve: list[str] = Field(default_factory=list)
    recommended_learning_path: list[str] = Field(default_factory=list)
    hiring_recommendation: HiringRecommendation
    recruiter_comments: str = ""
    questions_asked: int = 0
    duration_minutes: float = 0.0
    difficulty_trajectory: list[str] = Field(default_factory=list)
    generated_at: datetime


class DifficultyPoint(BaseModel):
    question_number: int
    difficulty: str
    score_pct: float


class DashboardData(BaseModel):
    candidate_id: str
    candidate_name: str
    resume_summary: str = ""
    skills: list[str] = Field(default_factory=list)
    interview_id: str
    interview_duration_minutes: float = 0.0
    questions_asked: int = 0
    question_history: list[QuestionHistoryItem] = Field(default_factory=list)
    scores: list[float] = Field(default_factory=list)
    difficulty_graph: list[DifficultyPoint] = Field(default_factory=list)
    skill_graph: list[SkillScore] = Field(default_factory=list)
    overall_score: float = 0.0
    weak_topics: list[str] = Field(default_factory=list)
    strong_topics: list[str] = Field(default_factory=list)
    final_recommendation: HiringRecommendation | None = None
    recruiter_comments: str = ""
    soft_skills: SoftSkillScores = Field(default_factory=SoftSkillScores)
    started_at: datetime | None = None
    ended_at: datetime | None = None


class EndInterviewResponse(BaseModel):
    interview_id: str
    status: str
    report: FinalReport
    message: str = "Interview completed successfully"


class CandidateSummary(BaseModel):
    """Summary of a candidate and their latest interview for the HR dashboard."""
    candidate_id: str
    name: str
    email: str
    interview_id: str
    status: str
    overall_score: float = 0.0
    questions_asked: int = 0
    started_at: datetime | None = None
    ended_at: datetime | None = None


class ChatHistoryItem(BaseModel):
    """A single Q&A interaction within an interview."""
    question_number: int
    question: str
    candidate_answer: str = ""
    correct_answer: str = ""
    score: float = 0.0
    percentage: float = 0.0
    feedback: str = ""
    skill: str = ""
    difficulty: str = ""
    category: str = ""


class ChatHistoryResponse(BaseModel):
    """Full chat history for a specific interview."""
    interview_id: str
    candidate_name: str
    candidate_email: str
    status: str
    overall_score: float = 0.0
    items: list[ChatHistoryItem] = Field(default_factory=list)


class InterviewDetailResponse(BaseModel):
    interview_id: str
    session_id: str
    candidate_id: str
    candidate_name: str
    status: str
    difficulty_level: str
    question_number: int
    overall_score: float
    skills: list[str]
    question_history: list[QuestionHistoryItem]
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendation: HiringRecommendation | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    report: FinalReport | None = None
