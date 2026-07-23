"""Shared enums and constants for the interview engine."""

from enum import Enum


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


DIFFICULTY_ORDER: list[DifficultyLevel] = [
    DifficultyLevel.EASY,
    DifficultyLevel.MEDIUM,
    DifficultyLevel.HARD,
    DifficultyLevel.EXPERT,
]


class QuestionCategory(str, Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    SCENARIO_BASED = "scenario_based"
    PROJECT_BASED = "project_based"
    CODING_CONCEPTS = "coding_concepts"
    REAL_WORLD = "real_world"
    THEORY = "theory"
    DEBUGGING = "debugging"
    ARCHITECTURE = "architecture"
    BEHAVIOR = "behavior"


class InterviewStatus(str, Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    AWAITING_ANSWER = "awaiting_answer"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    TERMINATED = "terminated"
    EXPIRED = "expired"


class HiringRecommendation(str, Enum):
    STRONG_HIRE = "strong_hire"
    HIRE = "hire"
    BORDERLINE = "borderline"
    REJECT = "reject"


class LLMProvider(str, Enum):
    GROQ = "groq"
