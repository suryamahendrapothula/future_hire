"""Interview orchestration service — fully in-memory, no database dependency."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from genai_service.agents.resume_parser import ResumeParserAgent
from genai_service.config import get_settings
from genai_service.graph.interview_graph import InterviewGraph, get_interview_graph
from genai_service.memory.store import get_memory_store
from genai_service.schemas.enums import DifficultyLevel, HiringRecommendation, InterviewStatus
from genai_service.schemas.evaluation import (
    DifficultyDecision,
    EvaluationResult,
    SubmitAnswerResponse,
)
from genai_service.schemas.interview import (
    NextQuestionResponse,
    QuestionHistoryItem,
    QuestionMetadata,
    StartInterviewRequest,
    StartInterviewResponse,
)
from genai_service.schemas.report import (
    CandidateSummary,
    ChatHistoryItem,
    ChatHistoryResponse,
    DashboardData,
    DifficultyPoint,
    EndInterviewResponse,
    FinalReport,
    InterviewDetailResponse,
    SkillScore,
    SoftSkillScores,
)
from genai_service.schemas.resume import ParsedResume, UploadResumeResponse
from genai_service.state.interview_state import create_initial_state
from genai_service.utils.exceptions import (
    InterviewLimitReachedError,
    InvalidInterviewStateError,
    SessionNotFoundError,
    ValidationError,
)
from genai_service.utils.helpers import new_id
from genai_service.utils.logging import get_logger

logger = get_logger(__name__)


class InterviewService:
    """In-memory interview orchestration service (no database dependency)."""

    def __init__(
        self,
        graph: InterviewGraph | None = None,
    ) -> None:
        self.graph = graph or get_interview_graph()
        self.parser = ResumeParserAgent()
        self.store = get_memory_store()
        self.settings = get_settings()

    # ------------------------------------------------------------------
    # Resume upload
    # ------------------------------------------------------------------

    async def upload_resume_file(
        self, *, content: bytes, filename: str
    ) -> UploadResumeResponse:
        parsed = await self.parser.parse_bytes(content, filename)
        return await self._persist_candidate(parsed)

    async def upload_resume_text(self, resume_text: str) -> UploadResumeResponse:
        parsed = await self.parser.parse_text(resume_text)
        return await self._persist_candidate(parsed)

    async def _persist_candidate(self, parsed: ParsedResume) -> UploadResumeResponse:
        candidate_id = new_id("cand_")
        candidate_data = {
            "id": candidate_id,
            "name": parsed.candidate_name or "Unknown",
            "email": parsed.email or "",
            "phone": parsed.phone or "",
            "skills": parsed.skills,
            "resume_text": parsed.raw_text,
            "parsed_resume": parsed.model_dump(),
            "primary_domains": parsed.primary_domains,
            "years_of_experience": parsed.years_of_experience,
            "projects": [p.model_dump() for p in parsed.projects],
            "experience": [e.model_dump() for e in parsed.experience],
            "education": [e.model_dump() for e in parsed.education],
            "certificates": [c.model_dump() for c in parsed.certificates],
            "achievements": parsed.achievements,
            "github": parsed.github,
            "linkedin": parsed.linkedin,
        }
        await self.store.set(f"candidate:{candidate_id}", candidate_data)
        logger.info("candidate_created", candidate_id=candidate_id, name=parsed.candidate_name)
        return UploadResumeResponse(
            candidate_id=candidate_id,
            candidate_name=parsed.candidate_name or "Unknown",
            skills=parsed.skills,
            primary_domains=parsed.primary_domains,
            years_of_experience=parsed.years_of_experience,
        )

    # ------------------------------------------------------------------
    # Interview lifecycle
    # ------------------------------------------------------------------

    async def start(self, request: StartInterviewRequest) -> StartInterviewResponse:
        candidate = await self._get_candidate(request.candidate_id)
        parsed = ParsedResume.model_validate(candidate["parsed_resume"])
        if not parsed.skills:
            raise InvalidInterviewStateError("Candidate has no extractable skills")

        interview_id = new_id("int_")
        session_id = new_id("sess_")
        max_q = request.max_questions or self.settings.max_questions
        time_limit = request.time_limit_minutes or self.settings.interview_time_limit_minutes

        initial = create_initial_state(
            session_id=session_id,
            interview_id=interview_id,
            candidate_id=request.candidate_id,
            candidate_name=parsed.candidate_name or "Candidate",
            resume_text=parsed.raw_text,
            skills=parsed.skills,
            projects=[p.model_dump() for p in parsed.projects],
            experience=[e.model_dump() for e in parsed.experience],
            education=[e.model_dump() for e in parsed.education],
            certificates=[c.model_dump() for c in parsed.certificates],
            achievements=parsed.achievements,
            primary_domains=parsed.primary_domains,
            years_of_experience=parsed.years_of_experience,
            difficulty_level=request.starting_difficulty,
            max_questions=max_q,
            time_limit_minutes=time_limit,
        )

        state = await self.graph.start(initial)

        # Store interview in memory
        interview_data = {
            "id": interview_id,
            "session_id": session_id,
            "candidate_id": request.candidate_id,
            "difficulty_level": request.starting_difficulty.value,
            "max_questions": max_q,
            "time_limit_minutes": time_limit,
            "status": state.get("interview_status"),
            "question_number": state.get("question_number", 1),
            "overall_score": state.get("overall_score", 0.0),
            "strengths": state.get("strengths", []),
            "weaknesses": state.get("weaknesses", []),
            "recommendation": state.get("recommendation"),
            "final_report": state.get("final_report"),
            "state_snapshot": dict(state),
            "interactions": [],
            "started_at": datetime.utcnow().isoformat(),
            "ended_at": None,
        }
        await self.store.set(f"interview:{interview_id}", interview_data)
        await self.store.set(f"session:{interview_id}", session_id)

        # Track candidate's interviews
        cand_interviews = await self.store.get(f"candidate_interviews:{request.candidate_id}", [])
        cand_interviews.append(interview_id)
        await self.store.set(f"candidate_interviews:{request.candidate_id}", cand_interviews)

        question = QuestionMetadata.model_validate(state["current_question"])
        logger.info("interview_started", interview_id=interview_id, session_id=session_id)

        return StartInterviewResponse(
            interview_id=interview_id,
            session_id=session_id,
            candidate_name=parsed.candidate_name or "Candidate",
            skills=parsed.skills,
            difficulty_level=DifficultyLevel(
                state.get("difficulty_level", request.starting_difficulty.value)
            ),
            max_questions=max_q,
            time_limit_minutes=time_limit,
            question=question,
            interview_status=InterviewStatus(
                state.get("interview_status", InterviewStatus.AWAITING_ANSWER.value)
            ),
            started_at=datetime.fromisoformat(state["started_at"])
            if state.get("started_at")
            else datetime.utcnow(),
        )

    async def next_question(self, interview_id: str) -> NextQuestionResponse:
        session_id, state = await self._resolve_session(interview_id)

        if state.get("interview_status") == InterviewStatus.COMPLETED.value:
            return NextQuestionResponse(
                interview_id=interview_id,
                question=None,
                question_number=int(state.get("question_number") or 0),
                remaining_questions=0,
                difficulty_level=DifficultyLevel(state.get("difficulty_level", "medium")),
                interview_status=InterviewStatus.COMPLETED,
                message="Interview already completed",
            )

        if state.get("interview_status") == InterviewStatus.AWAITING_ANSWER.value:
            question = QuestionMetadata.model_validate(state["current_question"])
            max_q = int(state.get("max_questions") or self.settings.max_questions)
            qnum = int(state.get("question_number") or 0)
            return NextQuestionResponse(
                interview_id=interview_id,
                question=question,
                question_number=qnum,
                remaining_questions=max(0, max_q - qnum),
                difficulty_level=DifficultyLevel(state.get("difficulty_level", "medium")),
                interview_status=InterviewStatus.AWAITING_ANSWER,
                message="Awaiting answer for current question",
            )

        max_q = int(state.get("max_questions") or self.settings.max_questions)
        qnum = int(state.get("question_number") or 0)
        if qnum >= max_q:
            raise InterviewLimitReachedError("Maximum questions reached")

        state = await self.graph.next_question(session_id)
        await self._persist_state(interview_id, state)

        if state.get("interview_status") == InterviewStatus.COMPLETED.value:
            return NextQuestionResponse(
                interview_id=interview_id,
                question=None,
                question_number=int(state.get("question_number") or 0),
                remaining_questions=0,
                difficulty_level=DifficultyLevel(state.get("difficulty_level", "medium")),
                interview_status=InterviewStatus.COMPLETED,
                message="Interview completed",
            )

        question = QuestionMetadata.model_validate(state["current_question"])
        qnum = int(state.get("question_number") or 0)
        return NextQuestionResponse(
            interview_id=interview_id,
            question=question,
            question_number=qnum,
            remaining_questions=max(0, max_q - qnum),
            difficulty_level=DifficultyLevel(state.get("difficulty_level", "medium")),
            interview_status=InterviewStatus(
                state.get("interview_status", InterviewStatus.AWAITING_ANSWER.value)
            ),
            message="Next question generated",
        )

    async def submit_answer(
        self, interview_id: str, answer: str
    ) -> SubmitAnswerResponse:
        session_id, state = await self._resolve_session(interview_id)

        status = state.get("interview_status")
        if status == InterviewStatus.COMPLETED.value:
            raise InvalidInterviewStateError("Interview already completed")
        if status not in (
            InterviewStatus.AWAITING_ANSWER.value,
            InterviewStatus.IN_PROGRESS.value,
            InterviewStatus.EVALUATING.value,
        ):
            raise InvalidInterviewStateError(
                f"Cannot submit answer in status '{status}'"
            )
        if not state.get("current_question"):
            raise InvalidInterviewStateError("No active question to answer")

        prev_history_len = len(state.get("question_history") or [])
        state = await self.graph.submit_answer(session_id, answer)

        # Store interaction in memory
        history = list(state.get("question_history") or [])
        if len(history) > prev_history_len:
            item = history[-1]
            interview_data = await self.store.get(f"interview:{interview_id}")
            if interview_data:
                interview_data.setdefault("interactions", []).append(item)
                await self.store.set(f"interview:{interview_id}", interview_data)

        await self._persist_state(interview_id, state)

        evaluation = EvaluationResult.model_validate(state.get("evaluation") or {})
        decision = DifficultyDecision.model_validate(
            state.get("difficulty_decision")
            or {
                "previous_difficulty": state.get("difficulty_level", "medium"),
                "new_difficulty": state.get("difficulty_level", "medium"),
                "average_score_pct": state.get("overall_score", 0),
                "last_score_pct": evaluation.percentage,
                "action": "maintain",
                "reason": "",
            }
        )

        max_q = int(state.get("max_questions") or self.settings.max_questions)
        qnum = int(state.get("question_number") or 0)
        completed = state.get("interview_status") == InterviewStatus.COMPLETED.value
        next_available = (not completed) and (qnum < max_q)

        return SubmitAnswerResponse(
            interview_id=interview_id,
            question_number=qnum,
            evaluation=evaluation,
            difficulty_decision=decision,
            overall_score=float(state.get("overall_score") or 0),
            interview_status=str(state.get("interview_status")),
            next_question_available=next_available,
            message="Answer evaluated successfully",
        )

    async def end_interview(self, interview_id: str) -> EndInterviewResponse:
        session_id, state = await self._resolve_session(interview_id)
        state = await self.graph.end_interview(session_id)
        await self._persist_state(interview_id, state, ended=True)

        report = FinalReport.model_validate(state.get("final_report") or {})
        return EndInterviewResponse(
            interview_id=interview_id,
            status=InterviewStatus.COMPLETED.value,
            report=report,
        )

    async def get_interview(self, interview_id: str) -> InterviewDetailResponse:
        interview_data = await self.store.get(f"interview:{interview_id}")
        if not interview_data:
            raise SessionNotFoundError(f"Interview {interview_id} not found")

        candidate = await self._get_candidate(interview_data["candidate_id"])
        interactions = sorted(
            interview_data.get("interactions", []),
            key=lambda i: i.get("question_number", 0),
        )

        history = [
            QuestionHistoryItem(
                question_number=i.get("question_number", 0),
                question=i.get("question", ""),
                skill=i.get("skill", ""),
                difficulty=DifficultyLevel(i.get("difficulty", "medium"))
                if i.get("difficulty") in DifficultyLevel._value2member_map_
                else DifficultyLevel.MEDIUM,
                category=i.get("category", "theory"),
                candidate_answer=i.get("candidate_answer", ""),
                correct_answer=i.get("correct_answer", ""),
                score=float(i.get("score", 0)),
                percentage=float(i.get("percentage", 0)),
                feedback=i.get("feedback", ""),
                timestamp=datetime.fromisoformat(i["timestamp"])
                if i.get("timestamp")
                else None,
                metadata=i.get("metadata", {}),
            )
            for i in interactions
        ]

        report = None
        if interview_data.get("final_report"):
            try:
                report = FinalReport.model_validate(interview_data["final_report"])
            except Exception:
                report = None

        rec = None
        if interview_data.get("recommendation"):
            try:
                rec = HiringRecommendation(interview_data["recommendation"])
            except ValueError:
                rec = None

        return InterviewDetailResponse(
            interview_id=interview_data["id"],
            session_id=interview_data["session_id"],
            candidate_id=interview_data["candidate_id"],
            candidate_name=candidate.get("name", "Unknown"),
            status=interview_data.get("status", "unknown"),
            difficulty_level=interview_data.get("difficulty_level", "medium"),
            question_number=interview_data.get("question_number", 0),
            overall_score=float(interview_data.get("overall_score", 0)),
            skills=candidate.get("skills", []),
            question_history=history,
            strengths=interview_data.get("strengths", []),
            weaknesses=interview_data.get("weaknesses", []),
            recommendation=rec,
            started_at=datetime.fromisoformat(interview_data["started_at"])
            if interview_data.get("started_at")
            else None,
            ended_at=datetime.fromisoformat(interview_data["ended_at"])
            if interview_data.get("ended_at")
            else None,
            report=report,
        )

    async def get_dashboard(self, candidate_id: str) -> DashboardData:
        candidate = await self._get_candidate(candidate_id)
        interview_ids = await self.store.get(f"candidate_interviews:{candidate_id}", [])
        if not interview_ids:
            raise SessionNotFoundError(f"No interviews found for candidate {candidate_id}")

        # Get latest interview
        interview_data = await self.store.get(f"interview:{interview_ids[-1]}")
        if not interview_data:
            raise SessionNotFoundError(f"Interview data not found")

        interactions = sorted(
            interview_data.get("interactions", []),
            key=lambda i: i.get("question_number", 0),
        )

        history = [
            QuestionHistoryItem(
                question_number=i.get("question_number", 0),
                question=i.get("question", ""),
                skill=i.get("skill", ""),
                difficulty=DifficultyLevel(i.get("difficulty", "medium"))
                if i.get("difficulty") in DifficultyLevel._value2member_map_
                else DifficultyLevel.MEDIUM,
                category=i.get("category", "theory"),
                candidate_answer=i.get("candidate_answer", ""),
                correct_answer=i.get("correct_answer", ""),
                score=float(i.get("score", 0)),
                percentage=float(i.get("percentage", 0)),
                feedback=i.get("feedback", ""),
                timestamp=datetime.fromisoformat(i["timestamp"])
                if i.get("timestamp")
                else None,
                metadata=i.get("metadata", {}),
            )
            for i in interactions
        ]

        skill_map: dict[str, list[float]] = {}
        difficulty_graph: list[DifficultyPoint] = []
        for i in interactions:
            skill_map.setdefault(i.get("skill") or "general", []).append(
                float(i.get("percentage", 0))
            )
            difficulty_graph.append(
                DifficultyPoint(
                    question_number=i.get("question_number", 0),
                    difficulty=i.get("difficulty", "medium"),
                    score_pct=float(i.get("percentage", 0)),
                )
            )

        skill_graph = [
            SkillScore(
                skill=skill,
                score=round(sum(vals) / len(vals), 2),
                questions_asked=len(vals),
            )
            for skill, vals in skill_map.items()
        ]
        weak = [s.skill for s in skill_graph if s.score < 60]
        strong = [s.skill for s in skill_graph if s.score >= 75]

        duration = 0.0
        if interview_data.get("started_at"):
            start_dt = datetime.fromisoformat(interview_data["started_at"])
            end_dt = (
                datetime.fromisoformat(interview_data["ended_at"])
                if interview_data.get("ended_at")
                else datetime.utcnow()
            )
            duration = (end_dt - start_dt).total_seconds() / 60.0

        report = interview_data.get("final_report") or {}
        soft = SoftSkillScores.model_validate(report.get("soft_skills") or {})
        rec = None
        if interview_data.get("recommendation"):
            try:
                rec = HiringRecommendation(interview_data["recommendation"])
            except ValueError:
                rec = None

        return DashboardData(
            candidate_id=candidate_id,
            candidate_name=candidate.get("name", "Unknown"),
            resume_summary=(candidate.get("resume_text") or "")[:500],
            skills=candidate.get("skills", []),
            interview_id=interview_data["id"],
            interview_duration_minutes=round(duration, 2),
            questions_asked=len(interactions),
            question_history=history,
            scores=[float(i.get("percentage", 0)) for i in interactions],
            difficulty_graph=difficulty_graph,
            skill_graph=skill_graph,
            overall_score=float(interview_data.get("overall_score", 0)),
            weak_topics=weak or report.get("topics_to_improve", []),
            strong_topics=strong or report.get("strengths", [])[:5],
            final_recommendation=rec,
            recruiter_comments=report.get("recruiter_comments", ""),
            soft_skills=soft,
            started_at=datetime.fromisoformat(interview_data["started_at"])
            if interview_data.get("started_at")
            else None,
            ended_at=datetime.fromisoformat(interview_data["ended_at"])
            if interview_data.get("ended_at")
            else None,
        )

    async def list_candidates(self) -> list[CandidateSummary]:
        """Return all candidates that have at least one interview."""
        candidate_keys = await self.store.keys("candidate:")
        results: list[CandidateSummary] = []

        for key in candidate_keys:
            if key.startswith("candidate_interviews:"):
                continue
            candidate = await self.store.get(key)
            if not candidate:
                continue
            candidate_id = candidate["id"]
            interview_ids = await self.store.get(
                f"candidate_interviews:{candidate_id}", []
            )
            if not interview_ids:
                continue

            # Get latest interview
            interview_data = await self.store.get(f"interview:{interview_ids[-1]}")
            if not interview_data:
                continue

            results.append(
                CandidateSummary(
                    candidate_id=candidate_id,
                    name=candidate.get("name", "Unknown"),
                    email=candidate.get("email", ""),
                    interview_id=interview_data["id"],
                    status=interview_data.get("status", "unknown"),
                    overall_score=float(interview_data.get("overall_score", 0)),
                    questions_asked=len(interview_data.get("interactions", [])),
                    started_at=datetime.fromisoformat(interview_data["started_at"])
                    if interview_data.get("started_at")
                    else None,
                    ended_at=datetime.fromisoformat(interview_data["ended_at"])
                    if interview_data.get("ended_at")
                    else None,
                )
            )
        return results

    async def get_chat_history(self, interview_id: str) -> ChatHistoryResponse:
        """Return the full Q&A chat log for a specific interview."""
        interview_data = await self.store.get(f"interview:{interview_id}")
        if not interview_data:
            raise SessionNotFoundError(f"Interview {interview_id} not found")

        candidate = await self._get_candidate(interview_data["candidate_id"])
        interactions = sorted(
            interview_data.get("interactions", []),
            key=lambda i: i.get("question_number", 0),
        )

        items = [
            ChatHistoryItem(
                question_number=i.get("question_number", 0),
                question=i.get("question", ""),
                candidate_answer=i.get("candidate_answer", ""),
                correct_answer=i.get("correct_answer", ""),
                score=float(i.get("score", 0)),
                percentage=float(i.get("percentage", 0)),
                feedback=i.get("feedback", ""),
                skill=i.get("skill", ""),
                difficulty=i.get("difficulty", ""),
                category=i.get("category", ""),
            )
            for i in interactions
        ]

        return ChatHistoryResponse(
            interview_id=interview_id,
            candidate_name=candidate.get("name", "Unknown"),
            candidate_email=candidate.get("email", ""),
            status=interview_data.get("status", "unknown"),
            overall_score=float(interview_data.get("overall_score", 0)),
            items=items,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_candidate(self, candidate_id: str) -> dict:
        candidate = await self.store.get(f"candidate:{candidate_id}")
        if not candidate:
            raise SessionNotFoundError(f"Candidate {candidate_id} not found")
        return candidate

    async def _resolve_session(self, interview_id: str) -> tuple[str, dict[str, Any]]:
        session_id = await self.store.get(f"session:{interview_id}")
        if not session_id:
            interview_data = await self.store.get(f"interview:{interview_id}")
            if not interview_data:
                raise SessionNotFoundError(f"Interview {interview_id} not found")
            session_id = interview_data["session_id"]
            await self.store.set(f"session:{interview_id}", session_id)

        state = await self.graph.get_state(session_id)
        if not state:
            interview_data = await self.store.get(f"interview:{interview_id}")
            if interview_data and interview_data.get("state_snapshot"):
                state = dict(interview_data["state_snapshot"])
                await self.graph.graph.aupdate_state(
                    {"configurable": {"thread_id": session_id}},
                    state,
                )
            else:
                raise SessionNotFoundError(
                    f"No active state for interview {interview_id}"
                )
        return session_id, state

    async def _persist_state(
        self,
        interview_id: str,
        state: dict[str, Any],
        *,
        ended: bool = False,
    ) -> None:
        interview_data = await self.store.get(f"interview:{interview_id}")
        if not interview_data:
            return

        interview_data["status"] = state.get("interview_status")
        interview_data["difficulty_level"] = state.get("difficulty_level")
        interview_data["question_number"] = state.get("question_number")
        interview_data["overall_score"] = state.get("overall_score")
        interview_data["strengths"] = state.get("strengths")
        interview_data["weaknesses"] = state.get("weaknesses")
        interview_data["recommendation"] = state.get("recommendation")
        interview_data["final_report"] = state.get("final_report")
        interview_data["state_snapshot"] = dict(state)

        if ended or state.get("interview_status") == InterviewStatus.COMPLETED.value:
            interview_data["ended_at"] = datetime.utcnow().isoformat()
            interview_data["status"] = InterviewStatus.COMPLETED.value

        await self.store.set(f"interview:{interview_id}", interview_data)
