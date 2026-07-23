"""Custom exceptions for the GenAI Interview Service."""

from typing import Any


class InterviewEngineError(Exception):
    """Base exception for the interview engine."""

    def __init__(self, message: str, *, details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class ConfigurationError(InterviewEngineError):
    """Raised when required configuration is missing or invalid."""


class LLMError(InterviewEngineError):
    """Raised when an LLM call fails after retries."""


class ResumeParseError(InterviewEngineError):
    """Raised when resume parsing fails."""


class SessionNotFoundError(InterviewEngineError):
    """Raised when an interview/candidate session cannot be found."""


class InvalidInterviewStateError(InterviewEngineError):
    """Raised when an operation is illegal for the current interview status."""


class InterviewLimitReachedError(InterviewEngineError):
    """Raised when max questions or time limit is exceeded."""


class ValidationError(InterviewEngineError):
    """Raised for domain-level validation failures."""
