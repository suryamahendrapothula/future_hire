"""Resume Parser Agent — extract structured skills/experience from resumes."""

from __future__ import annotations

import io
from pathlib import Path

from genai_service.prompts.resume_prompts import RESUME_PARSER_SYSTEM, RESUME_PARSER_USER
from genai_service.schemas.resume import ParsedResume
from genai_service.services.llm_service import LLMService
from genai_service.utils.exceptions import ResumeParseError
from genai_service.utils.logging import get_logger

logger = get_logger(__name__)


class ResumeParserAgent:
    """Parse resume files/text into a structured ParsedResume model."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

    def __init__(self, llm_service: LLMService | None = None) -> None:
        self.llm = llm_service or LLMService()

    async def parse_text(self, resume_text: str) -> ParsedResume:
        if not resume_text or not resume_text.strip():
            raise ResumeParseError("Resume text is empty")

        truncated = resume_text.strip()[:50000]
        logger.info("resume_parse_start", chars=len(truncated))

        try:
            parsed = await self.llm.astructured(
                system=RESUME_PARSER_SYSTEM,
                user=RESUME_PARSER_USER.format(resume_text=truncated),
                schema=ParsedResume,
            )
        except Exception as exc:  # noqa: BLE001
            raise ResumeParseError("Failed to parse resume with LLM", details=str(exc)) from exc

        parsed.raw_text = truncated
        # Deduplicate skills while preserving order
        seen: set[str] = set()
        unique_skills: list[str] = []
        for skill in parsed.skills:
            key = skill.strip().lower()
            if key and key not in seen:
                seen.add(key)
                unique_skills.append(skill.strip())
        parsed.skills = unique_skills

        if not parsed.skills:
            raise ResumeParseError("No skills could be extracted from the resume")

        logger.info(
            "resume_parse_complete",
            candidate=parsed.candidate_name,
            skills=len(parsed.skills),
        )
        return parsed

    async def parse_bytes(self, content: bytes, filename: str) -> ParsedResume:
        text = self.extract_text(content, filename)
        return await self.parse_text(text)

    @classmethod
    def extract_text(cls, content: bytes, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        if ext not in cls.SUPPORTED_EXTENSIONS:
            raise ResumeParseError(
                f"Unsupported file type '{ext}'. Supported: {sorted(cls.SUPPORTED_EXTENSIONS)}"
            )
        try:
            if ext == ".pdf":
                return cls._extract_pdf(content)
            if ext == ".docx":
                return cls._extract_docx(content)
            return content.decode("utf-8", errors="ignore")
        except ResumeParseError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ResumeParseError("Failed to extract text from resume", details=str(exc)) from exc

    @staticmethod
    def _extract_pdf(content: bytes) -> str:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages).strip()
        if not text:
            raise ResumeParseError("PDF contained no extractable text")
        return text

    @staticmethod
    def _extract_docx(content: bytes) -> str:
        from docx import Document

        doc = Document(io.BytesIO(content))
        text = "\n".join(p.text for p in doc.paragraphs if p.text).strip()
        if not text:
            raise ResumeParseError("DOCX contained no extractable text")
        return text
