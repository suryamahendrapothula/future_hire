"""Agent 1 — Interview Question Generator (resume-grounded only)."""

from __future__ import annotations

import json
from typing import Any

from genai_service.prompts.question_prompts import QUESTION_GENERATOR_SYSTEM, QUESTION_GENERATOR_USER
from genai_service.schemas.enums import DifficultyLevel, QuestionCategory
from genai_service.schemas.interview import QuestionMetadata
from genai_service.schemas.llm_outputs import GeneratedQuestion
from genai_service.services.llm_service import LLMService
from genai_service.utils.logging import get_logger

logger = get_logger(__name__)


class QuestionGeneratorAgent:
    """Generate interview questions strictly from resume context."""

    def __init__(self, llm_service: LLMService | None = None) -> None:
        self.llm = llm_service or LLMService()

    async def generate(
        self,
        *,
        candidate_name: str,
        skills: list[str],
        projects: list[dict[str, Any]],
        experience: list[dict[str, Any]],
        education: list[dict[str, Any]],
        certificates: list[dict[str, Any]],
        achievements: list[str],
        asked_questions: list[str],
        difficulty: str,
        question_number: int,
        max_questions: int,
        years_of_experience: float = 0.0,
        primary_domains: list[str] | None = None,
        prefer_skills: list[str] | None = None,
        avoid_skills: list[str] | None = None,
    ) -> QuestionMetadata:
        certs_achievements = {
            "certificates": certificates,
            "achievements": achievements,
        }
        user = QUESTION_GENERATOR_USER.format(
            candidate_name=candidate_name,
            difficulty=difficulty,
            question_number=question_number,
            max_questions=max_questions,
            years_of_experience=years_of_experience,
            primary_domains=", ".join(primary_domains or []) or "General Software",
            skills=", ".join(skills) if skills else "None listed",
            projects=json.dumps(projects, default=str)[:6000],
            experience=json.dumps(experience, default=str)[:6000],
            education=json.dumps(education, default=str)[:3000],
            certificates_achievements=json.dumps(certs_achievements, default=str)[:3000],
            asked_questions=json.dumps(asked_questions[-20:], default=str),
            prefer_skills=", ".join(prefer_skills or []) or "none",
            avoid_skills=", ".join(avoid_skills or []) or "none",
        )

        logger.info(
            "question_generation_start",
            difficulty=difficulty,
            question_number=question_number,
        )

        result = await self.llm.astructured(
            system=QUESTION_GENERATOR_SYSTEM,
            user=user,
            schema=GeneratedQuestion,
        )

        # Normalize enums / defaults
        requested_difficulty = difficulty
        try:
            resolved_difficulty = DifficultyLevel(str(result.difficulty).lower())
        except ValueError:
            resolved_difficulty = DifficultyLevel(requested_difficulty)

        try:
            category = QuestionCategory(str(result.category).lower())
        except ValueError:
            category = QuestionCategory.THEORY

        skill = result.skill
        # Ensure skill is from resume when possible
        if skills and skill:
            skill_lookup = {s.lower(): s for s in skills}
            if skill.lower() not in skill_lookup:
                # Prefer hinted skills, else first skill
                if prefer_skills:
                    for ps in prefer_skills:
                        if ps.lower() in skill_lookup:
                            skill = skill_lookup[ps.lower()]
                            break
                    else:
                        skill = skills[0]
                else:
                    skill = skills[0]

        question_text = result.question
        rationale = result.rationale

        # Safety: reject near-duplicates of prior questions
        q_norm = question_text.strip().lower()
        for prev in asked_questions:
            if prev.strip().lower() == q_norm:
                question_text = (
                    f"Building on your experience with {skill}, "
                    f"describe a challenging production issue you faced and how you resolved it."
                )
                category = QuestionCategory.PROJECT_BASED
                rationale = "Fallback non-duplicate project probe grounded in resume skill."
                break

        metadata = QuestionMetadata(
            question=question_text,
            skill=skill,
            difficulty=resolved_difficulty,
            category=category,
            expected_topics=result.expected_topics,
            estimated_time_seconds=result.estimated_time_seconds,
            question_number=question_number,
            rationale=rationale,
        )

        logger.info(
            "question_generation_complete",
            skill=metadata.skill,
            category=metadata.category.value,
        )
        return metadata
