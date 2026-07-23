"""Lightweight schemas used only for LLM structured output (no required identity fields)."""

from pydantic import BaseModel, Field

from genai_service.schemas.enums import (
    DifficultyLevel,
    HiringRecommendation,
    QuestionCategory,
)
from genai_service.schemas.report import SkillScore, SoftSkillScores


class GeneratedQuestion(BaseModel):
    question: str
    skill: str
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    category: QuestionCategory = QuestionCategory.THEORY
    expected_topics: list[str] = Field(default_factory=list)
    estimated_time_seconds: int = Field(default=120, ge=30, le=600)
    rationale: str = ""


class GeneratedReport(BaseModel):
    overall_score: float = Field(..., ge=0, le=100)
    skill_wise_scores: list[SkillScore] = Field(default_factory=list)
    soft_skills: SoftSkillScores = Field(default_factory=SoftSkillScores)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    topics_to_improve: list[str] = Field(default_factory=list)
    recommended_learning_path: list[str] = Field(default_factory=list)
    hiring_recommendation: HiringRecommendation = HiringRecommendation.BORDERLINE
    recruiter_comments: str = ""
    difficulty_trajectory: list[str] = Field(default_factory=list)
