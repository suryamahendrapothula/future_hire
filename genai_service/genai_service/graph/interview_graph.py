"""LangGraph multi-agent interview workflow."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from genai_service.agents.answer_evaluator import AnswerEvaluatorAgent
from genai_service.agents.difficulty_manager import DifficultyManagerAgent
from genai_service.agents.question_generator import QuestionGeneratorAgent
from genai_service.agents.report_generator import ReportGeneratorAgent
from genai_service.config import get_settings
from genai_service.schemas.enums import InterviewStatus
from genai_service.schemas.interview import QuestionMetadata
from genai_service.state.interview_state import InterviewState
from genai_service.utils.helpers import average, utcnow_iso
from genai_service.utils.logging import get_logger

logger = get_logger(__name__)


class InterviewGraph:
    """
    LangGraph orchestration:

      generate_question -> (await external answer) -> evaluate_answer
      -> manage_difficulty -> generate_question | generate_report -> END
    """

    def __init__(
        self,
        *,
        question_agent: QuestionGeneratorAgent | None = None,
        evaluator_agent: AnswerEvaluatorAgent | None = None,
        difficulty_agent: DifficultyManagerAgent | None = None,
        report_agent: ReportGeneratorAgent | None = None,
        checkpointer: MemorySaver | None = None,
    ) -> None:
        self.question_agent = question_agent or QuestionGeneratorAgent()
        self.evaluator_agent = evaluator_agent or AnswerEvaluatorAgent()
        self.difficulty_agent = difficulty_agent or DifficultyManagerAgent()
        self.report_agent = report_agent or ReportGeneratorAgent()
        self.checkpointer = checkpointer or MemorySaver()
        self.settings = get_settings()
        self.graph = self._build()

    def _build(self):
        builder = StateGraph(InterviewState)

        builder.add_node("generate_question", self.generate_question_node)
        builder.add_node("evaluate_answer", self.evaluate_answer_node)
        builder.add_node("manage_difficulty", self.manage_difficulty_node)
        builder.add_node("generate_report", self.generate_report_node)

        builder.add_edge(START, "generate_question")
        builder.add_edge("generate_question", END)

        # Evaluation chain used after answer submission
        builder.add_edge("evaluate_answer", "manage_difficulty")
        builder.add_conditional_edges(
            "manage_difficulty",
            self.should_continue,
            {
                "continue": END,  # next question fetched via dedicated invoke
                "finish": "generate_report",
            },
        )
        builder.add_edge("generate_report", END)

        return builder.compile(checkpointer=self.checkpointer)

    # ------------------------------------------------------------------
    # Nodes
    # ------------------------------------------------------------------

    async def generate_question_node(self, state: InterviewState) -> dict[str, Any]:
        qnum = int(state.get("question_number") or 0) + 1
        max_q = int(state.get("max_questions") or self.settings.max_questions)
        decision = state.get("difficulty_decision") or {}

        question = await self.question_agent.generate(
            candidate_name=state.get("candidate_name") or "Candidate",
            skills=list(state.get("skills") or []),
            projects=list(state.get("projects") or []),
            experience=list(state.get("experience") or []),
            education=list(state.get("education") or []),
            certificates=list(state.get("certificates") or []),
            achievements=list(state.get("achievements") or []),
            asked_questions=list(state.get("asked_question_texts") or []),
            difficulty=state.get("difficulty_level") or "medium",
            question_number=qnum,
            max_questions=max_q,
            years_of_experience=float(state.get("years_of_experience") or 0),
            primary_domains=list(state.get("primary_domains") or []),
            prefer_skills=list(decision.get("prefer_skills") or []),
            avoid_skills=list(decision.get("avoid_skills") or []),
        )

        q_dict = question.model_dump(mode="json")
        asked = list(state.get("asked_question_texts") or [])
        asked.append(question.question)

        logger.info(
            "graph_question_generated",
            interview_id=state.get("interview_id"),
            question_number=qnum,
        )

        return {
            "question_number": qnum,
            "current_question": q_dict,
            "candidate_answer": "",
            "correct_answer": "",
            "evaluation": {},
            "interview_status": InterviewStatus.AWAITING_ANSWER.value,
            "asked_question_texts": asked,
            "updated_at": utcnow_iso(),
        }

    async def evaluate_answer_node(self, state: InterviewState) -> dict[str, Any]:
        current = state.get("current_question") or {}
        question = QuestionMetadata.model_validate(current)
        answer = state.get("candidate_answer") or ""

        resume_bits = [
            f"Skills: {', '.join(state.get('skills') or [])}",
            f"Projects: {state.get('projects')}",
            f"Experience: {state.get('experience')}",
        ]
        evaluation = await self.evaluator_agent.evaluate(
            question=question,
            candidate_answer=answer,
            resume_context="\n".join(resume_bits),
        )
        ev = evaluation.model_dump(mode="json")

        history_item = {
            "question_number": state.get("question_number"),
            "question": question.question,
            "skill": question.skill,
            "difficulty": question.difficulty.value
            if hasattr(question.difficulty, "value")
            else question.difficulty,
            "category": question.category.value
            if hasattr(question.category, "value")
            else question.category,
            "candidate_answer": answer,
            "correct_answer": evaluation.correct_answer or evaluation.ideal_answer,
            "score": evaluation.score,
            "percentage": evaluation.percentage,
            "feedback": evaluation.feedback,
            "timestamp": utcnow_iso(),
            "evaluation": ev,
            "metadata": {
                "expected_topics": question.expected_topics,
                "estimated_time_seconds": question.estimated_time_seconds,
                "rationale": question.rationale,
            },
        }

        scores = list(state.get("score_history") or []) + [evaluation.score]
        overall = average([s * 10.0 if s <= 10 else s for s in scores])

        strengths = list(dict.fromkeys(
            list(state.get("strengths") or []) + list(evaluation.strengths or [])
        ))[:20]
        weaknesses = list(dict.fromkeys(
            list(state.get("weaknesses") or []) + list(evaluation.weaknesses or [])
        ))[:20]

        logger.info(
            "graph_answer_evaluated",
            interview_id=state.get("interview_id"),
            score=evaluation.score,
        )

        return {
            "evaluation": ev,
            "score": evaluation.score,
            "correct_answer": evaluation.correct_answer or evaluation.ideal_answer,
            "overall_score": round(overall, 2),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "interview_status": InterviewStatus.EVALUATING.value,
            # Use reducers for append-only histories
            "question_history": [history_item],
            "answer_history": [answer],
            "feedback_history": [evaluation.feedback],
            "score_history": [evaluation.score],
            "updated_at": utcnow_iso(),
        }

    async def manage_difficulty_node(self, state: InterviewState) -> dict[str, Any]:
        history = list(state.get("question_history") or [])
        recent_skills = [h.get("skill", "") for h in history if h.get("skill")]
        evaluation = state.get("evaluation") or {}

        decision = await self.difficulty_agent.decide(
            previous_difficulty=state.get("difficulty_level") or "medium",
            score_history=list(state.get("score_history") or []),
            difficulty_history=list(state.get("difficulty_history") or []),
            question_number=int(state.get("question_number") or 0),
            available_skills=list(state.get("skills") or []),
            recent_skills=recent_skills,
            weaknesses=list(evaluation.get("weaknesses") or []),
            strengths=list(evaluation.get("strengths") or []),
        )
        d = decision.model_dump(mode="json")
        new_level = decision.new_difficulty.value

        return {
            "difficulty_decision": d,
            "difficulty_level": new_level,
            "difficulty_history": [new_level],
            "updated_at": utcnow_iso(),
        }

    async def generate_report_node(self, state: InterviewState) -> dict[str, Any]:
        started = state.get("started_at") or utcnow_iso()
        try:
            start_dt = datetime.fromisoformat(started)
            duration = (datetime.utcnow() - start_dt).total_seconds() / 60.0
        except ValueError:
            duration = 0.0

        report = await self.report_agent.generate(
            interview_id=state.get("interview_id") or "",
            candidate_id=state.get("candidate_id") or "",
            candidate_name=state.get("candidate_name") or "",
            skills=list(state.get("skills") or []),
            question_history=list(state.get("question_history") or []),
            overall_score=float(state.get("overall_score") or 0.0),
            duration_minutes=duration,
            difficulty_trajectory=list(state.get("difficulty_history") or []),
        )

        return {
            "final_report": report.model_dump(mode="json"),
            "recommendation": report.hiring_recommendation.value,
            "strengths": report.strengths,
            "weaknesses": report.weaknesses,
            "interview_status": InterviewStatus.COMPLETED.value,
            "ended_at": utcnow_iso(),
            "updated_at": utcnow_iso(),
        }

    def should_continue(self, state: InterviewState) -> Literal["continue", "finish"]:
        qnum = int(state.get("question_number") or 0)
        max_q = int(state.get("max_questions") or self.settings.max_questions)
        if qnum >= max_q:
            return "finish"

        # Time limit check
        started = state.get("started_at")
        limit = int(state.get("time_limit_minutes") or self.settings.interview_time_limit_minutes)
        if started:
            try:
                start_dt = datetime.fromisoformat(started)
                elapsed_min = (datetime.utcnow() - start_dt).total_seconds() / 60.0
                if elapsed_min >= limit:
                    return "finish"
            except ValueError:
                pass
        return "continue"

    # ------------------------------------------------------------------
    # Public invoke helpers
    # ------------------------------------------------------------------

    def _config(self, thread_id: str) -> dict[str, Any]:
        return {"configurable": {"thread_id": thread_id}}

    async def start(self, initial_state: InterviewState) -> InterviewState:
        thread_id = initial_state["session_id"]
        result = await self.graph.ainvoke(initial_state, config=self._config(thread_id))
        return result  # type: ignore[return-value]

    async def submit_answer(self, session_id: str, answer: str) -> InterviewState:
        """Evaluate answer + manage difficulty (+ report if finished)."""
        return await self._run_evaluation_pipeline(session_id, answer)

    async def _run_evaluation_pipeline(self, session_id: str, answer: str) -> InterviewState:
        config = self._config(session_id)
        snapshot = await self.graph.aget_state(config)
        values = dict(snapshot.values)
        values["candidate_answer"] = answer

        eval_update = await self.evaluate_answer_node(values)  # type: ignore[arg-type]
        values = {**values, **eval_update}
        # Merge list reducers manually for histories
        for key in ("question_history", "answer_history", "feedback_history", "score_history"):
            prev = list(snapshot.values.get(key) or [])
            added = list(eval_update.get(key) or [])
            values[key] = prev + added

        diff_update = await self.manage_difficulty_node(values)  # type: ignore[arg-type]
        prev_diff_hist = list(values.get("difficulty_history") or [])
        values = {**values, **diff_update}
        values["difficulty_history"] = prev_diff_hist + list(
            diff_update.get("difficulty_history") or []
        )

        decision = self.should_continue(values)  # type: ignore[arg-type]
        if decision == "finish":
            report_update = await self.generate_report_node(values)  # type: ignore[arg-type]
            values = {**values, **report_update}
        else:
            values["interview_status"] = InterviewStatus.IN_PROGRESS.value

        await self.graph.aupdate_state(config, values)
        return values  # type: ignore[return-value]

    async def next_question(self, session_id: str) -> InterviewState:
        config = self._config(session_id)
        snapshot = await self.graph.aget_state(config)
        values = dict(snapshot.values)

        status = values.get("interview_status")
        if status == InterviewStatus.COMPLETED.value:
            return values  # type: ignore[return-value]

        qnum = int(values.get("question_number") or 0)
        max_q = int(values.get("max_questions") or self.settings.max_questions)
        if qnum >= max_q:
            report_update = await self.generate_report_node(values)  # type: ignore[arg-type]
            values = {**values, **report_update}
            await self.graph.aupdate_state(config, values)
            return values  # type: ignore[return-value]

        q_update = await self.generate_question_node(values)  # type: ignore[arg-type]
        # asked_question_texts is overwritten intentionally with full list
        values = {**values, **q_update}
        await self.graph.aupdate_state(config, values)
        return values  # type: ignore[return-value]

    async def end_interview(self, session_id: str) -> InterviewState:
        config = self._config(session_id)
        snapshot = await self.graph.aget_state(config)
        values = dict(snapshot.values)
        if values.get("interview_status") != InterviewStatus.COMPLETED.value:
            report_update = await self.generate_report_node(values)  # type: ignore[arg-type]
            values = {**values, **report_update}
            await self.graph.aupdate_state(config, values)
        return values  # type: ignore[return-value]

    async def get_state(self, session_id: str) -> InterviewState | None:
        config = self._config(session_id)
        snapshot = await self.graph.aget_state(config)
        if not snapshot or not snapshot.values:
            return None
        return dict(snapshot.values)  # type: ignore[return-value]


_interview_graph: InterviewGraph | None = None


def get_interview_graph() -> InterviewGraph:
    global _interview_graph
    if _interview_graph is None:
        _interview_graph = InterviewGraph()
    return _interview_graph
