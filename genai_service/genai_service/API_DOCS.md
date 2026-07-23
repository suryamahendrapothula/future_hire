# GenAI Interview Service — API Documentation

Base URL: `http://localhost:8100`

All endpoints return a standard wrapper:
```json
{
  "success": true,
  "data": { ... },
  "message": "...",
  "errors": []
}
```

---

## 1. Health Check

**GET** `/health`

```bash
curl http://localhost:8100/health
```

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "environment": "development",
  "llm_model": "llama-3.3-70b-versatile"
}
```

---

## 2. Upload Resume

**POST** `/api/v1/upload_resume`

Upload a file or send raw text. Returns `candidate_id` needed for starting interviews.

### Option A: File Upload
```bash
curl -X POST http://localhost:8100/api/v1/upload_resume \
  -F "file=@resume.pdf"
```

### Option B: Text
```bash
curl -X POST http://localhost:8100/api/v1/upload_resume \
  -F "resume_text=John Doe, 5 years Python, Django, React developer..."
```

**Response:**
```json
{
  "success": true,
  "data": {
    "candidate_id": "cand_abc123...",
    "candidate_name": "John Doe",
    "skills": ["Python", "Django", "React", "PostgreSQL"],
    "primary_domains": ["Backend", "Frontend"],
    "years_of_experience": 5.0,
    "message": "Resume parsed successfully"
  },
  "message": "Resume uploaded and parsed"
}
```

---

## 3. Start Interview

**POST** `/api/v1/start_interview`

```bash
curl -X POST http://localhost:8100/api/v1/start_interview \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id": "cand_abc123...",
    "max_questions": 10,
    "time_limit_minutes": 30,
    "starting_difficulty": "medium"
  }'
```

**Request Body:**
| Field | Type | Required | Default |
|-------|------|----------|---------|
| `candidate_id` | string | ✅ | — |
| `max_questions` | int | ❌ | 15 |
| `time_limit_minutes` | int | ❌ | 30 |
| `starting_difficulty` | string | ❌ | `"medium"` |

**Difficulty values:** `easy`, `medium`, `hard`, `expert`

**Response:**
```json
{
  "success": true,
  "data": {
    "interview_id": "int_xyz789...",
    "session_id": "sess_...",
    "candidate_name": "John Doe",
    "skills": ["Python", "Django", "React"],
    "difficulty_level": "medium",
    "max_questions": 10,
    "time_limit_minutes": 30,
    "question": {
      "question": "In your Django project, how did you handle database migrations...",
      "skill": "Django",
      "difficulty": "medium",
      "category": "project_based",
      "expected_topics": ["migrations", "schema changes", "rollback"],
      "estimated_time_seconds": 180,
      "question_number": 1,
      "rationale": "Candidate listed Django in projects..."
    },
    "interview_status": "awaiting_answer",
    "started_at": "2025-01-01T00:00:00"
  }
}
```

---

## 4. Submit Answer

**POST** `/api/v1/submit_answer`

```bash
curl -X POST http://localhost:8100/api/v1/submit_answer \
  -H "Content-Type: application/json" \
  -d '{
    "interview_id": "int_xyz789...",
    "answer": "I used Django makemigrations and migrate commands..."
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "interview_id": "int_xyz789...",
    "question_number": 1,
    "evaluation": {
      "score": 7.5,
      "percentage": 75.0,
      "feedback": "Good understanding of migrations...",
      "strengths": ["Correct workflow", "Mentioned rollback"],
      "weaknesses": ["Missing zero-downtime strategies"],
      "correct_answer": "...",
      "ideal_answer": "...",
      "hallucination_detected": false
    },
    "difficulty_decision": {
      "previous_difficulty": "medium",
      "new_difficulty": "medium",
      "action": "maintain",
      "reason": "Score within 60-85% band"
    },
    "overall_score": 75.0,
    "interview_status": "in_progress",
    "next_question_available": true,
    "message": "Answer evaluated successfully"
  }
}
```

---

## 5. Next Question

**POST** `/api/v1/next_question`

```bash
curl -X POST http://localhost:8100/api/v1/next_question \
  -H "Content-Type: application/json" \
  -d '{"interview_id": "int_xyz789..."}'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "interview_id": "int_xyz789...",
    "question": {
      "question": "Explain how you implemented caching in your React app...",
      "skill": "React",
      "difficulty": "medium",
      "category": "scenario_based",
      "expected_topics": ["memoization", "useMemo", "React.memo"],
      "estimated_time_seconds": 150,
      "question_number": 2,
      "rationale": "Testing React skill from resume..."
    },
    "question_number": 2,
    "remaining_questions": 8,
    "difficulty_level": "medium",
    "interview_status": "awaiting_answer"
  }
}
```

---

## 6. End Interview

**POST** `/api/v1/end_interview`

Ends the interview early and generates the final report.

```bash
curl -X POST http://localhost:8100/api/v1/end_interview \
  -H "Content-Type: application/json" \
  -d '{"interview_id": "int_xyz789..."}'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "interview_id": "int_xyz789...",
    "status": "completed",
    "report": {
      "interview_id": "int_xyz789...",
      "candidate_id": "cand_abc123...",
      "candidate_name": "John Doe",
      "overall_score": 72.5,
      "skill_wise_scores": [
        {"skill": "Django", "score": 75.0, "questions_asked": 3},
        {"skill": "React", "score": 70.0, "questions_asked": 2}
      ],
      "soft_skills": {
        "communication": 78.0,
        "problem_solving": 72.0,
        "confidence": 75.0,
        "technical_accuracy": 70.0
      },
      "strengths": ["Strong Django knowledge", "Good problem decomposition"],
      "weaknesses": ["Weak on advanced React patterns"],
      "topics_to_improve": ["React hooks", "State management"],
      "recommended_learning_path": ["Advanced React patterns course"],
      "hiring_recommendation": "hire",
      "recruiter_comments": "Solid mid-level candidate...",
      "questions_asked": 5,
      "duration_minutes": 12.5,
      "difficulty_trajectory": ["medium", "medium", "hard"],
      "generated_at": "2025-01-01T00:15:00"
    },
    "message": "Interview completed successfully"
  }
}
```

---

## 7. Get Interview Details

**GET** `/api/v1/interview/{interview_id}`

```bash
curl http://localhost:8100/api/v1/interview/int_xyz789...
```

Returns full interview details with question history, scores, and report.

---

## 8. List Candidates

**GET** `/api/v1/dashboard/candidates`

```bash
curl http://localhost:8100/api/v1/dashboard/candidates
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "candidate_id": "cand_abc123...",
      "name": "John Doe",
      "email": "john@example.com",
      "interview_id": "int_xyz789...",
      "status": "completed",
      "overall_score": 72.5,
      "questions_asked": 5,
      "started_at": "2025-01-01T00:00:00",
      "ended_at": "2025-01-01T00:15:00"
    }
  ]
}
```

---

## 9. Chat History

**GET** `/api/v1/dashboard/chat-history/{interview_id}`

```bash
curl http://localhost:8100/api/v1/dashboard/chat-history/int_xyz789...
```

Returns the complete Q&A log with scores and feedback for each question.

---

## 10. Candidate Dashboard

**GET** `/api/v1/dashboard/{candidate_id}`

```bash
curl http://localhost:8100/api/v1/dashboard/cand_abc123...
```

Returns analytics: skill graph, difficulty graph, scores, weak/strong topics, soft skills.

---

## Interview Flow

```
1. POST /upload_resume     → get candidate_id
2. POST /start_interview   → get interview_id + first question
3. POST /submit_answer     → get evaluation + score
4. POST /next_question     → get next question
   (repeat 3-4 until done)
5. POST /end_interview     → get final report
```

## Error Codes

| Status | Error | Description |
|--------|-------|-------------|
| 400 | `ValidationError` | Invalid input |
| 400 | `InvalidInterviewStateError` | Wrong interview state for operation |
| 400 | `ResumeParseError` | Resume parsing failed |
| 404 | `SessionNotFoundError` | Interview/candidate not found |
| 409 | `InterviewLimitReachedError` | Max questions exceeded |
| 422 | Validation | Pydantic validation failure |
| 500 | `ConfigurationError` | Missing config (e.g. API key) |
| 502 | `LLMError` | Groq API call failed |

## Enums Reference

**DifficultyLevel:** `easy`, `medium`, `hard`, `expert`

**QuestionCategory:** `basic`, `intermediate`, `advanced`, `scenario_based`, `project_based`, `coding_concepts`, `real_world`, `theory`, `debugging`, `architecture`, `behavior`

**InterviewStatus:** `created`, `in_progress`, `awaiting_answer`, `evaluating`, `completed`, `terminated`, `expired`

**HiringRecommendation:** `strong_hire`, `hire`, `borderline`, `reject`
