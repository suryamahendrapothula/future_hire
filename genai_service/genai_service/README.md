# GenAI Interview Service

Standalone AI-powered interview engine microservice. Uses **Groq LLM + LangGraph** multi-agent orchestration to conduct, evaluate, and report on technical interviews.

## Quick Start

### 1. Install Dependencies

```bash
cd genai-service
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and set your GROQ_API_KEY
```

### 3. Run the Service

```bash
# From the project root directory
uvicorn genai_service.main:app --host 0.0.0.0 --port 8100 --reload
```

Or rename folder to `genai_service` and run:
```bash
cd ..
python -m uvicorn genai_service.main:app --port 8100 --reload
```

### 4. Open Swagger Docs

Visit: [http://localhost:8100/docs](http://localhost:8100/docs)

## Docker

```bash
docker build -t genai-service .
docker run -p 8100:8100 --env-file .env genai-service
```

## Architecture

```
┌─────────────────────────────────────────────┐
│              FastAPI Server (:8100)          │
│  ┌─────────┐ ┌──────────┐ ┌─────────────┐  │
│  │ Resume  │ │Interview │ │  Dashboard  │  │
│  │ Router  │ │  Router  │ │   Router    │  │
│  └────┬────┘ └────┬─────┘ └──────┬──────┘  │
│       └──────┬─────┴──────────────┘         │
│         InterviewService (in-memory)        │
│       ┌──────┴──────────────────┐           │
│  ┌────┴─────┐          ┌───────┴────────┐  │
│  │MemoryStore│         │ InterviewGraph │  │
│  │  (KV)    │          │  (LangGraph)   │  │
│  └──────────┘          └───────┬────────┘  │
│                    ┌───────────┼──────────┐ │
│               ┌────┴───┐ ┌────┴───┐ ┌────┴┐│
│               │Question│ │Answer  │ │Diff.││
│               │  Gen   │ │Eval    │ │Mgr  ││
│               └────────┘ └────────┘ └─────┘│
│                    ┌───────┴───────┐        │
│               ┌────┴───┐    ┌─────┴──┐     │
│               │Resume  │    │Report  │     │
│               │Parser  │    │  Gen   │     │
│               └────────┘    └────────┘     │
│                        │                    │
│                   Groq LLM API              │
└─────────────────────────────────────────────┘
```

## AI Agents

| Agent | Purpose |
|-------|---------|
| **ResumeParser** | Extracts structured skills, experience, projects from resumes |
| **QuestionGenerator** | Creates interview questions grounded in resume content |
| **AnswerEvaluator** | FAANG-level evaluation with scoring, feedback, ideal answers |
| **DifficultyManager** | Adaptive difficulty (easy→medium→hard→expert) based on performance |
| **ReportGenerator** | Final hiring report with skill scores, recommendations |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Service info |
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/upload_resume` | Parse resume (file or text) |
| `POST` | `/api/v1/start_interview` | Start interview session |
| `POST` | `/api/v1/next_question` | Get next question |
| `POST` | `/api/v1/submit_answer` | Submit & evaluate answer |
| `POST` | `/api/v1/end_interview` | End interview & get report |
| `GET` | `/api/v1/interview/{id}` | Get interview details |
| `GET` | `/api/v1/dashboard/candidates` | List all candidates |
| `GET` | `/api/v1/dashboard/chat-history/{id}` | Get Q&A chat log |
| `GET` | `/api/v1/dashboard/{candidate_id}` | Get candidate dashboard |

See [API_DOCS.md](API_DOCS.md) for full request/response examples.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | — | **Required.** Groq API key |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Primary LLM model |
| `SERVICE_PORT` | `8100` | HTTP port |
| `MAX_QUESTIONS` | `15` | Max questions per interview |
| `INTERVIEW_TIME_LIMIT_MINUTES` | `30` | Time limit |
| `CORS_ORIGINS` | `["*"]` | Allowed CORS origins |
| `ENVIRONMENT` | `development` | dev/staging/production |

## Notes for Developers

- **No database** — All data is stored in-memory. Restarting the service clears all sessions.
- **Backend integration** — Call these endpoints from your backend and persist results in your own database.
- **Frontend integration** — Call these endpoints directly or proxy through your backend.
- **CORS** — Configured to accept requests from common dev ports (4200, 3000, 5173, 8000).
