"""Agent 2 — Answer Evaluation Agent."""

from __future__ import annotations

from genai_service.prompts.evaluation_prompts import EVALUATION_SYSTEM, EVALUATION_USER
from genai_service.schemas.evaluation import EvaluationResult
from genai_service.schemas.interview import QuestionMetadata
from genai_service.services.llm_service import LLMService
from genai_service.utils.helpers import clamp
from genai_service.utils.logging import get_logger

logger = get_logger(__name__)


class AnswerEvaluatorAgent:
    """Evaluate candidate answers like a senior technical interviewer."""

    def __init__(self, llm_service: LLMService | None = None) -> None:
        self.llm = llm_service or LLMService()

    async def evaluate(
        self,
        *,
        question: QuestionMetadata,
        candidate_answer: str,
        resume_context: str,
    ) -> EvaluationResult:
        if not candidate_answer.strip():
            return EvaluationResult(
                score=0.0,
                percentage=0.0,
                feedback="No answer was provided.",
                strengths=[],
                weaknesses=["Empty response"],
                missing_points=question.expected_topics,
                grammar_quality=0.0,
                technical_accuracy=0.0,
                confidence_level=0.0,
                correct_answer="",
                model_answer="",
                ideal_answer="",
                detailed_explanation="Candidate submitted an empty answer.",
                industry_standard_answer="",
                reference_concepts=question.expected_topics,
                next_recommendation="Ask a clarifying warmer question on the same skill.",
                hallucination_detected=False,
                answer_completeness=0.0,
                alternative_accepted=False,
                evaluation_rationale="Empty answer scores zero.",
            )

        user = EVALUATION_USER.format(
            resume_context=resume_context[:8000],
            question=question.question,
            skill=question.skill,
            difficulty=question.difficulty.value
            if hasattr(question.difficulty, "value")
            else question.difficulty,
            category=question.category.value
            if hasattr(question.category, "value")
            else question.category,
            expected_topics=", ".join(question.expected_topics),
            candidate_answer=candidate_answer[:15000],
        )

        logger.info("evaluation_start", skill=question.skill)

        result = await self.llm.astructured(
            system=EVALUATION_SYSTEM,
            user=user,
            schema=EvaluationResult,
        )

        result.score = clamp(float(result.score), 0.0, 10.0)
        result.percentage = clamp(
            float(result.percentage) if result.percentage else result.score * 10.0,
            0.0,
            100.0,
        )
        # Keep score/percentage consistent if model drifts
        if abs(result.percentage - result.score * 10) > 15:
            result.percentage = round(result.score * 10, 2)

        for field in (
            "grammar_quality",
            "technical_accuracy",
            "confidence_level",
            "answer_completeness",
        ):
            setattr(result, field, clamp(float(getattr(result, field)), 0.0, 10.0))

        # Prefer ideal_answer as fallback for correct_answer storage
        if not result.correct_answer:
            result.correct_answer = result.ideal_answer or result.model_answer
        if not result.ideal_answer:
            result.ideal_answer = result.correct_answer or result.model_answer

        logger.info(
            "evaluation_complete",
            score=result.score,
            percentage=result.percentage,
            hallucination=result.hallucination_detected,
        )
        return result
