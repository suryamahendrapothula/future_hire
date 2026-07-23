"""Prompt package exports."""

from genai_service.prompts.difficulty_prompts import DIFFICULTY_SYSTEM, DIFFICULTY_USER
from genai_service.prompts.evaluation_prompts import EVALUATION_SYSTEM, EVALUATION_USER
from genai_service.prompts.question_prompts import QUESTION_GENERATOR_SYSTEM, QUESTION_GENERATOR_USER
from genai_service.prompts.report_prompts import REPORT_SYSTEM, REPORT_USER
from genai_service.prompts.resume_prompts import RESUME_PARSER_SYSTEM, RESUME_PARSER_USER

__all__ = [
    "DIFFICULTY_SYSTEM",
    "DIFFICULTY_USER",
    "EVALUATION_SYSTEM",
    "EVALUATION_USER",
    "QUESTION_GENERATOR_SYSTEM",
    "QUESTION_GENERATOR_USER",
    "REPORT_SYSTEM",
    "REPORT_USER",
    "RESUME_PARSER_SYSTEM",
    "RESUME_PARSER_USER",
]
