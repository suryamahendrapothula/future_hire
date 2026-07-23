"""Agent 3 — Difficulty Manager with smooth transitions."""

from __future__ import annotations

from genai_service.config import get_settings
from genai_service.prompts.difficulty_prompts import DIFFICULTY_SYSTEM, DIFFICULTY_USER
from genai_service.schemas.enums import DIFFICULTY_ORDER, DifficultyLevel
from genai_service.schemas.evaluation import DifficultyDecision
from genai_service.services.llm_service import LLMService
from genai_service.utils.helpers import average
from genai_service.utils.logging import get_logger

logger = get_logger(__name__)


class DifficultyManagerAgent:
    """Control interview difficulty with no jumps across the ladder."""

    def __init__(self, llm_service: LLMService | None = None) -> None:
        self.llm = llm_service or LLMService()
        self.settings = get_settings()

    def _rule_based_decision(
        self,
        *,
        previous: DifficultyLevel,
        last_score_pct: float,
        average_score_pct: float,
        weaknesses: list[str],
        strengths: list[str],
        available_skills: list[str],
        recent_skills: list[str],
    ) -> DifficultyDecision:
        inc = self.settings.difficulty_increase_threshold
        dec = self.settings.difficulty_decrease_threshold
        idx = DIFFICULTY_ORDER.index(previous)

        if average_score_pct > inc and idx < len(DIFFICULTY_ORDER) - 1:
            new = DIFFICULTY_ORDER[idx + 1]
            action = "increase"
            reason = f"Average score {average_score_pct:.1f}% > {inc}% — increase one step."
        elif average_score_pct < dec and idx > 0:
            new = DIFFICULTY_ORDER[idx - 1]
            action = "decrease"
            reason = f"Average score {average_score_pct:.1f}% < {dec}% — decrease one step."
        else:
            new = previous
            action = "maintain"
            reason = (
                f"Average score {average_score_pct:.1f}% within "
                f"{dec}–{inc}% band — maintain difficulty."
            )

        # Prefer weaker areas; avoid repeating last skill when possible
        prefer = [w for w in weaknesses if w][:3]
        avoid = recent_skills[-1:] if recent_skills else []
        if strengths and action == "increase":
            prefer = [s for s in strengths if s][:2] + prefer

        # Fall back to under-asked available skills
        if not prefer and available_skills:
            prefer = [s for s in available_skills if s not in avoid][:2]

        return DifficultyDecision(
            previous_difficulty=previous,
            new_difficulty=new,
            average_score_pct=round(average_score_pct, 2),
            last_score_pct=round(last_score_pct, 2),
            action=action,
            reason=reason,
            avoid_skills=avoid,
            prefer_skills=prefer,
        )

    @staticmethod
    def _enforce_smooth_transition(
        previous: DifficultyLevel,
        proposed: DifficultyLevel,
    ) -> DifficultyLevel:
        prev_idx = DIFFICULTY_ORDER.index(previous)
        try:
            new_idx = DIFFICULTY_ORDER.index(proposed)
        except ValueError:
            return previous
        if abs(new_idx - prev_idx) > 1:
            return DIFFICULTY_ORDER[prev_idx + (1 if new_idx > prev_idx else -1)]
        return proposed

    async def decide(
        self,
        *,
        previous_difficulty: str | DifficultyLevel,
        score_history: list[float],
        difficulty_history: list[str],
        question_number: int,
        available_skills: list[str],
        recent_skills: list[str],
        weaknesses: list[str] | None = None,
        strengths: list[str] | None = None,
        use_llm: bool = True,
    ) -> DifficultyDecision:
        raw_prev = str(previous_difficulty).lower().split(".")[-1]
        previous = (
            previous_difficulty
            if isinstance(previous_difficulty, DifficultyLevel)
            else DifficultyLevel(raw_prev)
        )
        # score_history stored as 0-10; convert to %
        pct_scores = [s * 10.0 if s <= 10 else s for s in score_history]
        last_pct = pct_scores[-1] if pct_scores else 0.0
        avg_pct = average(pct_scores)

        rule = self._rule_based_decision(
            previous=previous,
            last_score_pct=last_pct,
            average_score_pct=avg_pct,
            weaknesses=weaknesses or [],
            strengths=strengths or [],
            available_skills=available_skills,
            recent_skills=recent_skills,
        )

        if not use_llm:
            logger.info("difficulty_rule_only", action=rule.action, new=rule.new_difficulty)
            return rule

        user = DIFFICULTY_USER.format(
            previous_difficulty=previous.value,
            last_score_pct=round(last_pct, 2),
            average_score_pct=round(avg_pct, 2),
            question_number=question_number,
            score_history=pct_scores,
            difficulty_history=difficulty_history,
            recent_skills=recent_skills,
            available_skills=available_skills,
            weaknesses=weaknesses or [],
            strengths=strengths or [],
        )

        try:
            llm_decision = await self.llm.astructured(
                system=DIFFICULTY_SYSTEM,
                user=user,
                schema=DifficultyDecision,
            )
            raw_new = str(llm_decision.new_difficulty).lower().split(".")[-1]
            llm_decision.new_difficulty = self._enforce_smooth_transition(
                previous,
                DifficultyLevel(raw_new),
            )
            llm_decision.previous_difficulty = previous
            llm_decision.average_score_pct = round(avg_pct, 2)
            llm_decision.last_score_pct = round(last_pct, 2)

            # Ensure action matches enforced level
            prev_idx = DIFFICULTY_ORDER.index(previous)
            new_idx = DIFFICULTY_ORDER.index(llm_decision.new_difficulty)
            if new_idx > prev_idx:
                llm_decision.action = "increase"
            elif new_idx < prev_idx:
                llm_decision.action = "decrease"
            else:
                llm_decision.action = "maintain"

            # Merge skill hints with rule-based defaults
            if not llm_decision.prefer_skills:
                llm_decision.prefer_skills = rule.prefer_skills
            if not llm_decision.avoid_skills:
                llm_decision.avoid_skills = rule.avoid_skills

            logger.info(
                "difficulty_decision",
                action=llm_decision.action,
                new=llm_decision.new_difficulty.value,
            )
            return llm_decision
        except Exception as exc:  # noqa: BLE001
            logger.warning("difficulty_llm_fallback", error=str(exc))
            return rule
