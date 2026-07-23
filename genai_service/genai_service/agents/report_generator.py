"""Final Report Generator Agent."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from typing import Any

from genai_service.prompts.report_prompts import REPORT_SYSTEM, REPORT_USER
from genai_service.schemas.enums import HiringRecommendation
from genai_service.schemas.llm_outputs import GeneratedReport
from genai_service.schemas.report import FinalReport, SkillScore, SoftSkillScores
from genai_service.services.llm_service import LLMService
from genai_service.utils.helpers import average, clamp
from genai_service.utils.logging import get_logger

logger = get_logger(__name__)


class ReportGeneratorAgent:
    """Produce hiring recommendations and analytics reports."""

    def __init__(self, llm_service: LLMService | None = None) -> None:
        self.llm = llm_service or LLMService()

    @staticmethod
    def _compute_skill_scores(history: list[dict[str, Any]]) -> list[SkillScore]:
        buckets: dict[str, list[float]] = defaultdict(list)
        diffs: dict[str, list[str]] = defaultdict(list)
        for item in history:
            skill = item.get("skill") or "general"
            score = float(item.get("percentage") or item.get("score", 0) * 10)
            buckets[skill].append(score)
            diffs[skill].append(str(item.get("difficulty", "")))

        results: list[SkillScore] = []
        for skill, scores in buckets.items():
            dlist = [d for d in diffs[skill] if d]
            avg_diff = dlist[-1] if dlist else ""
            results.append(
                SkillScore(
                    skill=skill,
                    score=round(average(scores), 2),
                    questions_asked=len(scores),
                    average_difficulty=avg_diff,
                )
            )
        return sorted(results, key=lambda s: s.score)

    @staticmethod
    def _soft_skills(history: list[dict[str, Any]]) -> SoftSkillScores:
        comm, tech, conf, solve = [], [], [], []
        for item in history:
            ev = item.get("evaluation") or {}
            if "grammar_quality" in ev:
                comm.append(float(ev["grammar_quality"]) * 10)
            if "technical_accuracy" in ev:
                tech.append(float(ev["technical_accuracy"]) * 10)
            if "confidence_level" in ev:
                conf.append(float(ev["confidence_level"]) * 10)
            pct = float(item.get("percentage") or 0)
            solve.append(pct)
        return SoftSkillScores(
            communication=round(average(comm), 2) if comm else round(average(solve), 2),
            problem_solving=round(average(solve), 2),
            confidence=round(average(conf), 2) if conf else round(average(solve), 2),
            technical_accuracy=round(average(tech), 2) if tech else round(average(solve), 2),
        )

    @staticmethod
    def _recommendation_from_score(score: float) -> HiringRecommendation:
        if score >= 85:
            return HiringRecommendation.STRONG_HIRE
        if score >= 70:
            return HiringRecommendation.HIRE
        if score >= 55:
            return HiringRecommendation.BORDERLINE
        return HiringRecommendation.REJECT

    async def generate(
        self,
        *,
        interview_id: str,
        candidate_id: str,
        candidate_name: str,
        skills: list[str],
        question_history: list[dict[str, Any]],
        overall_score: float,
        duration_minutes: float,
        difficulty_trajectory: list[str],
    ) -> FinalReport:
        overall = clamp(overall_score, 0.0, 100.0)
        skill_scores = self._compute_skill_scores(question_history)
        soft = self._soft_skills(question_history)
        fallback_rec = self._recommendation_from_score(overall)

        history_compact = [
            {
                "q": h.get("question"),
                "skill": h.get("skill"),
                "difficulty": h.get("difficulty"),
                "score_pct": h.get("percentage"),
                "feedback": (h.get("feedback") or "")[:300],
                "strengths": (h.get("evaluation") or {}).get("strengths", [])[:3],
                "weaknesses": (h.get("evaluation") or {}).get("weaknesses", [])[:3],
            }
            for h in question_history
        ]

        user = REPORT_USER.format(
            candidate_name=candidate_name,
            candidate_id=candidate_id,
            interview_id=interview_id,
            duration_minutes=round(duration_minutes, 2),
            skills=", ".join(skills),
            history_json=json.dumps(history_compact, default=str)[:12000],
            overall_score=round(overall, 2),
            communication=soft.communication,
            problem_solving=soft.problem_solving,
            confidence=soft.confidence,
            technical_accuracy=soft.technical_accuracy,
        )

        try:
            llm_report = await self.llm.astructured(
                system=REPORT_SYSTEM,
                user=user,
                schema=GeneratedReport,
            )
            recommendation = llm_report.hiring_recommendation or fallback_rec
            report = FinalReport(
                interview_id=interview_id,
                candidate_id=candidate_id,
                candidate_name=candidate_name,
                overall_score=round(float(llm_report.overall_score or overall), 2),
                skill_wise_scores=llm_report.skill_wise_scores or skill_scores,
                soft_skills=llm_report.soft_skills or soft,
                strengths=llm_report.strengths,
                weaknesses=llm_report.weaknesses,
                topics_to_improve=llm_report.topics_to_improve,
                recommended_learning_path=llm_report.recommended_learning_path,
                hiring_recommendation=recommendation,
                recruiter_comments=llm_report.recruiter_comments,
                questions_asked=len(question_history),
                duration_minutes=round(duration_minutes, 2),
                difficulty_trajectory=llm_report.difficulty_trajectory or difficulty_trajectory,
                generated_at=datetime.utcnow(),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("report_llm_fallback", error=str(exc))
            all_strengths: list[str] = []
            all_weaknesses: list[str] = []
            for h in question_history:
                ev = h.get("evaluation") or {}
                all_strengths.extend(ev.get("strengths") or [])
                all_weaknesses.extend(ev.get("weaknesses") or [])

            report = FinalReport(
                interview_id=interview_id,
                candidate_id=candidate_id,
                candidate_name=candidate_name,
                overall_score=round(overall, 2),
                skill_wise_scores=skill_scores,
                soft_skills=soft,
                strengths=list(dict.fromkeys(all_strengths))[:8],
                weaknesses=list(dict.fromkeys(all_weaknesses))[:8],
                topics_to_improve=[s.skill for s in skill_scores if s.score < 60][:8],
                recommended_learning_path=[
                    f"Deepen fundamentals in {s.skill}"
                    for s in skill_scores
                    if s.score < 70
                ][:6],
                hiring_recommendation=fallback_rec,
                recruiter_comments=(
                    f"Candidate scored {overall:.1f}% across {len(question_history)} questions. "
                    f"Recommendation: {fallback_rec.value}."
                ),
                questions_asked=len(question_history),
                duration_minutes=round(duration_minutes, 2),
                difficulty_trajectory=difficulty_trajectory,
                generated_at=datetime.utcnow(),
            )

        logger.info(
            "report_generated",
            interview_id=interview_id,
            recommendation=report.hiring_recommendation.value,
            overall=report.overall_score,
        )
        return report
