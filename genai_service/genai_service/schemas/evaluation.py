"""Answer evaluation Pydantic schemas."""

from pydantic import BaseModel, Field

from genai_service.schemas.enums import DifficultyLevel


class EvaluationResult(BaseModel):
    """Structured output from the Answer Evaluation Agent."""

    score: float = Field(..., ge=0, le=10)
    percentage: float = Field(..., ge=0, le=100)
    feedback: str = ""
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    missing_points: list[str] = Field(default_factory=list)
    grammar_quality: float = Field(default=0.0, ge=0, le=10)
    technical_accuracy: float = Field(default=0.0, ge=0, le=10)
    confidence_level: float = Field(default=0.0, ge=0, le=10)
    correct_answer: str = ""
    model_answer: str = ""
    ideal_answer: str = ""
    detailed_explanation: str = ""
    industry_standard_answer: str = ""
    reference_concepts: list[str] = Field(default_factory=list)
    next_recommendation: str = ""
    hallucination_detected: bool = False
    answer_completeness: float = Field(default=0.0, ge=0, le=10)
    alternative_accepted: bool = False
    evaluation_rationale: str = ""


class DifficultyDecision(BaseModel):
    """Structured output from the Difficulty Manager Agent."""

    previous_difficulty: DifficultyLevel
    new_difficulty: DifficultyLevel
    average_score_pct: float
    last_score_pct: float
    action: str = Field(
        default="maintain",
        description="increase | decrease | maintain",
    )
    reason: str = ""
    avoid_skills: list[str] = Field(default_factory=list)
    prefer_skills: list[str] = Field(default_factory=list)


class SubmitAnswerResponse(BaseModel):
    interview_id: str
    question_number: int
    evaluation: EvaluationResult
    difficulty_decision: DifficultyDecision
    overall_score: float
    interview_status: str
    next_question_available: bool
    message: str = ""
