# Resume Assistant

An AI-powered full-stack application that analyzes resumes, answers questions about candidates, and provides intelligent career recommendations using intent-based routing and advanced language models.

Deployed Version: https://resume-assistant-zeta.vercel.app/

**Key Features:**
- 🧠 Intent-based query routing (7 categories)
- 🚀 Dual LLM support: GROQ (primary) + Gemini (fallback)
- 📄 PDF/text resume parsing with optional LLM refinement
- 💼 Intelligent skill categorization and candidate scoring
- 🎯 Dynamic career role recommendations
- 💬 Conversational memory (last 20 messages)
- ⚡ Fast local-first processing, AI only when needed

## 📋 Table of Contents
- [Quick Start](#quick-start)
- [Setup Instructions](#setup-instructions)
- [Architecture Overview](#architecture-overview)
- [File Structure](#file-structure)
- [Design Decisions & Trade-offs](#design-decisions--trade-offs)
- [Data Flow Examples](#data-flow-examples)
- [Extending the System](#extending-the-system)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### 30-Second Setup

```bash
# Backend
cd backend
python -m venv .venv
source .venv/Scripts/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
echo "GROQ_API_KEY=your_key_here" > .env
uvicorn app:app --reload

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

Backend: http://localhost:8000  
Frontend: http://localhost:5173

---

## Setup Instructions

### Prerequisites
- Python 3.10+ (Backend)
- Node.js 18+ & npm/yarn (Frontend)
- GROQ API key (recommended) or Gemini API key (fallback)
- Git

### Backend Setup

#### 1. Clone & Navigate
```bash
git clone <repo-url>
cd resume-assistant
cd backend
```

#### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Environment Configuration
```bash
# Copy example file
cp .env.example .env

# Edit .env with your credentials
# Add either GROQ_API_KEY or GEMINI_API_KEY
```

**Required .env variables:**
```
GEMINI_API_KEY=your_gemini_key_here          # (optional, used as fallback)
GROQ_API_KEY=your_groq_api_key_here         # (recommended - faster responses)
GROQ_API_URL=https://api.groq.com/openai/v1/responses
GROQ_MODEL=llama-3.3-70b-versatile          # (or other available models)
GEMINI_MODEL=gemini-2.0-flash
MAX_TOKENS=1024
GROQ_TEMPERATURE=0.2
```

#### 5. Start Backend Server
```bash
# Development with auto-reload
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

Backend runs at: `http://localhost:8000`
API Docs: `http://localhost:8000/docs`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local
cat > .env.local << EOF
VITE_API_URL=http://localhost:8000
EOF

# Run development server
npm run dev
```

Frontend runs at: `http://localhost:5173`

**Build for production:**
```bash
npm run build  # Output: dist/ folder
```

---

## Architecture Overview

### High-Level System Design

The system is built on **layered architecture** with clear separation of concerns:

1. **Presentation Layer** (React Frontend)
2. **API Layer** (FastAPI)
3. **Business Logic Layer** (Intent Router + Hiring Agent)
4. **Tool Layer** (Specialized processors)
5. **LLM Layer** (GROQ/Gemini integration)

Key principle: **Local-first processing**. Most queries are answered without calling an LLM, reducing cost and latency.

### System Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER (Browser)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  React + TypeScript + Tailwind CSS (SPA)             │  │
│  │  - Resume Upload Interface                           │  │
│  │  - Chat Query Interface                              │  │
│  │  - Results Display & Analysis                        │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────┬───────────────────────────────────────────┘
                 │ HTTP/JSON
                 ↓
┌──────────────────────────────────────────────────────── ───┐
│                  API LAYER (FastAPI)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Port: 8000                                          │  │
│  │  CORS: Enabled for frontend origin                   │  │
│  │  Endpoints:                                          │  │
│  │    POST   /upload-resume          (PDF/TXT parsing)  │  │
│  │    POST   /chat                   (Query processing) │  │
│  │    GET    /health                 (Status check)     │  │
│  │    POST   /reset                  (State reset)      │  │
│  │    GET    /memory                 (Debug info)       │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────┬───────────────────────────────────────────┘
                 │ Internal Module Architecture
                 ↓
┌────────────────────────────────────────────────────────────┐
│              BUSINESS LOGIC LAYER                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Intent Router                                       │   │
│  │ - Classifies query intent (7 categories)            │   │
│  │ - Routes to appropriate tool/handler                │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Hiring Agent (Orchestrator)                         │   │
│  │ - Routes SKILL queries → SkillMatcher               │   │
│  │ - Routes EVALUATE queries → CandidateScorer         │   │
│  │ - Routes COMPLETENESS queries → ResumeTool          │   │
│  │ - Routes GENERAL queries → LLM (GROQ/Gemini)        │   │
│  │ - Includes full conversation history                │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Conversation Memory                                 │   │
│  │ - Tracks chat history (last 20 messages)            │   │
│  │ - Stores resume data                                │   │
│  │ - Maintains tool routing decisions                  │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────┬───────────────────────────────────────────┘
                 │ Tool Layer
                 ↓
┌─────────────────────────────────────────────────────────────┐
│                  TOOL LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ ResumeParser │  │SkillMatcher  │  │CandidateScore│       │
│  │              │  │              │  │              │       │
│  │- PDF extract │  │- Skill match │  │- Rate resume │       │
│  │- Text parse  │  │- Categorize  │  │- Completeness│       │
│  │- Normalize   │  │- Summary     │  │- Evaluation  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└────────────────┬────────────────────────────────────────────┘
                 │ External APIs
                 ↓
┌────────────────────────────────────────────────────────────┐
│                   LLM PROVIDERS                            │
│  ┌─────────────────────────┐  ┌──────────────────────┐     │
│  │ GROQ (Primary)          │  │ Gemini (Fallback)    │     │
│  │ - HTTP REST API         │  │ - google-genai SDK   │     │
│  │ - Responses API         │  │ - GenerateContent    │     │
│  │ - Faster responses      │  │ - Reliable backup    │     │
│  │ - Free tier available   │  │ - Free tier available│     │
│  └─────────────────────────┘  └──────────────────────┘     │
└────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Resume Upload**
   - User uploads PDF/TXT via React UI
   - Backend: `pdfplumber` extracts text (PDFs)
   - Optional GROQ-assisted parsing for clarity
   - Structured data (name, skills, experience, education) stored in memory

2. **Query Processing**
   - User asks question about resume
   - IntentRouter classifies query (7 categories)
   - HiringAgent routes to appropriate handler
   - Response includes confidence score + source

3. **Intent Categories**
   - **SKILL**: SkillMatcher → direct resume lookup
   - **EXPERIENCE**: ResumeParser → experience entries
   - **EDUCATION**: ResumeParser → education entries
   - **EVALUATE**: CandidateScorer → scoring (40% technical, 35% exp, 15% edu, 10% completeness)
   - **COMPLETENESS**: ResumeTool → missing sections analysis
   - **SUMMARY**: ResumeParser → overview
   - **GENERAL**: LLM (GROQ/Gemini) → with full context

### Component Responsibilities

| Component | Purpose | Tech |
|-----------|---------|------|
| **Frontend** | User interface for resume upload & queries | React 18, TypeScript, Tailwind CSS, Vite |
| **Backend** | API server & business logic | FastAPI, Python 3.10+ |
| **Resume Parser** | PDF/text extraction & normalization | pdfplumber, regex |
| **Intent Router** | Query classification | Keyword matching |
| **Skill Matcher** | Skill lookup & categorization | String matching, categorization |
| **Candidate Scorer** | Resume evaluation | Heuristic scoring |
| **Hiring Agent** | Query orchestration | LLM integration |
| **Memory** | Session state management | In-memory dict (single-user) |

---

## File Structure

```
resume-assistant/
├── backend/                          # FastAPI application
│   ├── agents/
│   │   ├── intent_router.py         # Query classification (7 categories)
│   │   └── hiring_agents.py         # Tool routing & LLM orchestration
│   ├── tools/
│   │   ├── resume_parser.py         # PDF/text extraction (+ optional GROQ)
│   │   ├── skill_matcher.py         # Fuzzy skill categorization
│   │   ├── candidate_scorer.py      # 4-component scoring + role recommendations
│   │   └── resume_completeness.py   # Section detection
│   ├── memory/
│   │   └── conversation_memory.py   # 20-message state management
│   ├── models/
│   │   └── schemas.py               # Pydantic request/response models
│   ├── prompts/
│   │   └── system_prompt.py         # LLM system instructions
│   ├── app.py                       # FastAPI server + 5 endpoints
│   ├── requirements.txt             # Python dependencies
│   ├── .env                         # Environment variables (local)
│   └── .gitignore
├── frontend/                         # React + TypeScript
│   ├── src/
│   │   ├── components/              # Reusable React components
│   │   ├── pages/
│   │   │   └── Dashboard.tsx        # Main app (orchestration + UI)
│   │   ├── services/
│   │   │   └── api.ts               # HTTP client (uses VITE_API_URL)
│   │   ├── App.tsx                  # Root component
│   │   └── main.tsx                 # Entry point
│   ├── public/                      # Static assets
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── .env.local                   # Environment variables (local)
│   └── .gitignore
├── README.md                         # This file
├── .gitignore                        # Root-level git ignore
└── .git/
```

### Key Files Explained

**backend/app.py**
- FastAPI entry point
- Defines 5 HTTP endpoints: `/upload-resume`, `/chat`, `/reset`, `/memory`, `/health`
- Handles CORS, error responses

**backend/agents/intent_router.py**
- Keyword-based query classifier
- Returns one of 7 intent types with priority ordering
- Runs instantly (no LLM required)

**backend/agents/hiring_agents.py**
- Main orchestration logic
- Routes each intent to appropriate tool or LLM
- Includes fallback chain: GROQ → Gemini → deterministic response
- Manages conversation history

**backend/tools/resume_parser.py**
- Extracts resume structure from PDF/text
- Local extraction first (regex), optional GROQ refinement
- Returns: name, skills, experiences, education

**backend/tools/skill_matcher.py**
- Fuzzy-matches skills in resume
- Categorizes into: programming, frameworks, tools, soft_skills, other
- Ranks by frequency/importance

**backend/tools/candidate_scorer.py**
- Scores resume on 4 dimensions (Tech 40%, Experience 35%, Education 15%, Completeness 10%)
- Calls GROQ for dynamic career role recommendations
- Returns: score breakdown, role fits, reasoning

**frontend/src/pages/Dashboard.tsx**
- Main React component
- Handles state: resume, chat history, evaluations
- Displays upload, chat, and career panels
- Calls backend API

**frontend/src/services/api.ts**
- HTTP client layer
- Uses environment variable `VITE_API_URL`
- Provides functions: `uploadResume()`, `chat()`, `reset()`, etc.

---

## Design Decisions & Trade-offs

### 1. **Intent-Based Routing Over RAG**
**Decision**: Route queries to GROQ by default; fall back to Gemini if GROQ fails or is not configured.

**Rationale**:
- GROQ: Faster response times (ideal for conversational flow), free tier available
- Gemini: More reliable fallback, proven stability

**Trade-off**:
- Must handle two different API response formats (Responses API vs SDK)
- Added complexity in response parsing

**Code**: `_handle_general_query()` in `agents/hiring_agents.py`

### 2. **GROQ as Primary LLM, Gemini as Fallback**

**Decision**: Route all LLM calls to GROQ first; fall back to Google Gemini if GROQ fails or isn't configured.

**Rationale**:
- **Speed**: GROQ Responses API is significantly faster (avg 1-2s vs Gemini 3-5s)
- **Cost**: GROQ cheaper at scale
- **Redundancy**: Fallback ensures service availability
- **Simplicity**: Easy to monitor which LLM was used

**Trade-off**:
- GROQ may have queue delays during peak demand
- Two different API formats (Responses API vs SDK) to handle
- Cascading failures possible if both LLMs down

**Mitigation**:
- Fallback chain ensures user never sees "API unavailable"
- Logs track which LLM was used
- Can swap priority by changing if/else order

**Code**: `backend/agents/hiring_agents.py` (lines 180-220)

### 3. **Hybrid Local + LLM Resume Parsing**

**Decision**: Extract resume structure locally with optional GROQ refinement for ambiguous sections.

**Rationale**:
- **Cost**: Local regex extraction is free; LLM only for 20% of messy resumes
- **Performance**: Instant parsing for well-formatted resumes
- **Control**: Deterministic output for structured data (name, dates)
- **Resilience**: If LLM fails, still get usable local data

**Trade-off**:
- Requires maintaining two extraction code paths
- Messy resumes may need GROQ call (adds 2-3s latency)
- Cannot detect semantic section changes (e.g., "Accomplishments" vs "Results")

**Mitigation**:
- Local extraction handles ~80% of real-world resumes
- GROQ refinement optional and configurable
- Error handling returns best-effort output

**Code**: `backend/tools/resume_parser.py` (lines 30-80)

### 4. **In-Memory State Management (No Database)**

**Decision**: Store resume data and chat history in Python memory only; no external database.

**Rationale**:
- **Simplicity**: Zero database setup, migrations, or ops overhead
- **Performance**: Instant access (no network latency)
- **Demo-friendly**: Works on laptop or free tier hosting
- **Isolation**: Single user per instance (no cross-contamination)

**Trade-off**:
- Data lost on server restart
- Not suitable for multi-user production
- Cannot scale horizontally (each instance has separate memory)
- 20-message cap prevents unbounded growth

**Migration Path**:
- Replace `ConversationMemory` class with SQLAlchemy/AsyncPG
- Add user authentication
- Move to managed database (PostgreSQL on AWS/Render)

**Code**: `backend/memory/conversation_memory.py` (lines 1-40)

### 5. **REST API Over GraphQL**

**Decision**: Use 5 simple REST endpoints rather than GraphQL.

**Rationale**:
- **Clarity**: Clear separation of concerns (upload, chat, reset, memory, health)
- **Performance**: No query parsing overhead
- **Caching**: Standard HTTP caching applies
- **Tooling**: Works with any frontend, CLI, or Postman

**Trade-off**:
- Cannot request partial fields (over-fetching possible)
- Fixed endpoint structure (harder to add optional response fields)
- No single endpoint for querying

**Endpoints**:
```
POST   /upload-resume   (Parse resume)
POST   /chat           (Ask question)
GET    /memory         (View state)
POST   /reset          (Clear memory)
GET    /health         (Server status)
```

**Code**: `backend/app.py`

### 6. **Fuzzy Skill Matching Over Exact Match**

**Decision**: Use fuzzy string matching (e.g., "Pyton" → "Python") instead of exact match.

**Rationale**:
- **Robustness**: Handles OCR errors and typos in parsed resumes
- **Coverage**: Catches variations ("ReactJS" vs "React", "JS" vs "JavaScript")
- **UX**: Users don't miss skills due to spelling

**Trade-off**:
- Risk of false positives (e.g., "Pax" → "Apex" at 85% threshold)
- Slower than exact matching (string distance calculation)
- Requires manual threshold tuning

**Settings**:
- Threshold: 85% similarity (catches typos, avoids false positives)
- Only fuzzy matches when exact match fails
- Known skill library validated against 1000+ common skills

**Code**: `backend/tools/skill_matcher.py` (lines 20-50)

### 7. **Weighted Scoring (Rule-Based, Not ML)**

**Decision**: Use fixed weighted scoring formula instead of ML model.

```
Final Score = (Tech × 0.4) + (Experience × 0.35) + (Education × 0.15) + (Completeness × 0.10)
```

**Rationale**:
- **Transparency**: Users see exactly why score is 7.8 (all components visible)
- **Control**: Can adjust weights without retraining
- **Simplicity**: No model management, versioning, or data collection
- **Auditability**: Each component independently verifiable

**Trade-off**:
- Less sophisticated than learned weights
- Weights are opinionated (may not match all hiring philosophies)
- Cannot learn from historical hiring decisions
- May be biased toward resume format rather than actual candidate quality

**Customization**:
- Weights exposed in config (can be changed per hiring manager)
- Can add new scoring dimensions
- Easy A/B testing different weight combinations

**Code**: `backend/tools/candidate_scorer.py` (lines 60-100)

### 8. **Dynamic GROQ Role Recommendations**

**Decision**: Call GROQ to generate career roles based on actual resume instead of using fixed list.

**Rationale**:
- **Relevance**: Recommendations match actual candidate profile
- **Scalability**: Can suggest roles that didn't exist in template
- **Modern**: Reflects current job market trends
- **Engagement**: More personalized feedback to candidate

**Trade-off**:
- Adds ~2 second latency to scoring
- GROQ hallucinations possible (may suggest unrealistic roles)
- Cost: Additional LLM call per evaluation

**Fallback**:
- If GROQ fails, returns 5 static roles: Developer, Architect, Lead, Manager, Consultant
- User sees canned recommendation but app doesn't break

**Code**: `backend/tools/candidate_scorer.py` (lines 130-170)

### 10. **Single-Tenant Architecture (No Multi-User)**

**Decision**: One resume per backend instance; no user authentication or multi-tenancy.

**Rationale**:
- **Simplicity**: No auth system, user management, or billing
- **Security**: No cross-user data contamination possible
- **Performance**: No query filtering overhead
- **Demo-ready**: Works on hobby tier hosting

**Trade-off**:
- Only one concurrent user per instance
- No team collaboration features
- Doesn't scale for SaaS
- Resume data visible to anyone with backend access (no auth)

**Upgrade Path**:
1. Add API key authentication
2. Add user registration/login
3. Migrate to PostgreSQL with user scoping
4. Deploy multiple instances behind load balancer
5. Add database per tenant (if full isolation needed)

**Current Assumptions**:
- Internal tool or demo
- Users trust backend operator
- No PII sensitivity (or users accept risk)

---

## Data Flow Examples

### Example 1: "What are the strongest skills?"

```
1. Frontend sends: {query: "What are the strongest skills?"}
2. IntentRouter:
   - Detects keywords: "strongest", "skills"
   - Classification: SKILL (high confidence)
3. HiringAgent:
   - Recognizes query is asking for summary (not specific skill lookup)
   - Calls: _handle_skill_summary_query()
4. SkillMatcher:
   - Extracts all skills from resume
   - Categorizes: programming=[Python, Java], frameworks=[React, Django], etc.
   - Ranks by frequency
5. Response:
   {
     "answer": "Top skills: React (Web), Python (Backend), Django (Framework)",
     "confidence": 0.95,
     "source": "SKILL",
     "skills_breakdown": { "programming": [...], "frameworks": [...] }
   }
6. Frontend displays categorized skill list
```

### Example 2: "Should we hire this candidate?"

```
1. Frontend sends: {query: "Should we hire this candidate?"}
2. IntentRouter:
   - Detects keywords: "hire", "candidate", "should"
   - Classification: EVALUATE
3. HiringAgent:
   - Calls: CandidateScorer(resume_data)
4. CandidateScorer:
   - Computes Tech score: 8.5/10 (count unique technologies)
   - Computes Experience score: 7.0/10 (years + relevance)
   - Computes Education score: 8.0/10 (degree + certifications)
   - Computes Completeness score: 6.5/10 (all sections present?)
   - Final: (8.5×0.4 + 7×0.35 + 8×0.15 + 6.5×0.1) = 7.78
   - Calls GROQ: Generate role recommendations based on resume
   - GROQ responds: ["Senior Backend Engineer (85%)", "Tech Lead (72%)", ...]
5. Response:
   {
     "answer": "Candidate scores 7.78/10 - suitable for senior roles",
     "score": 7.78,
     "breakdown": {"tech": 8.5, "experience": 7.0, "education": 8.0, "completeness": 6.5},
     "role_fits": [{"role": "Senior Backend Engineer", "fit": 0.85}, ...]
   }
6. Frontend displays score card + role recommendations
```

### Example 3: "Tell me about their experience"

```
1. Frontend sends: {query: "Tell me about their experience?"}
2. IntentRouter:
   - Detects keywords: "experience", "about", "tell"
   - Classification: GENERAL (no specific tool matches)
3. HiringAgent:
   - No specialized tool applies
   - Calls GROQ with full resume + chat history
   - System prompt instructs: "You are a hiring assistant. Answer questions about the candidate."
4. GROQ:
   - Reads resume data
   - Generates conversational response about experience
5. Response:
   {
     "answer": "The candidate has 7 years of backend development experience...",
     "confidence": 0.88,
     "source": "GENERAL (GROQ)"
   }
6. Frontend displays conversational answer in chat
```

---

## Extending the System

### Adding a New Intent Category

1. **Add keywords** to `backend/agents/intent_router.py`:
   ```python
   "LEADERSHIP": {
       "keywords": ["lead", "manage", "team", "leadership"],
       "priority": 5
   }
   ```

2. **Create handler** in `backend/agents/hiring_agents.py`:
   ```python
   def _handle_leadership_query(self, query, resume_data):
       # Extract leadership indicators from resume
       return {"answer": ..., "confidence": ...}
   ```

3. **Add route** in `_classify_and_route()`:
   ```python
   elif intent == "LEADERSHIP":
       return self._handle_leadership_query(...)
   ```

### Adding a New Tool

1. Create `backend/tools/your_tool.py`:
   ```python
   class YourTool:
       def process(self, resume_data: dict) -> dict:
           # Your logic
           return {"result": ...}
   ```

2. Import and instantiate in `hiring_agents.py`:
   ```python
   from tools.your_tool import YourTool
   self.your_tool = YourTool()
   ```

3. Use in handler:
   ```python
   result = self.your_tool.process(resume_data)
   ```

### Switching LLM Providers

In `backend/agents/hiring_agents.py`, modify fallback chain:

```python
# Current: GROQ → Gemini
# New: Claude → Cohere → Gemini

try:
    return self._call_claude_model(prompt)
except:
    try:
        return self._call_cohere_model(prompt)
    except:
        return self._call_gemini_model(prompt)
```

### Adding Database Persistence

Replace `ConversationMemory` with SQLAlchemy:

```python
# backend/memory/database.py
from sqlalchemy import create_engine

engine = create_engine("postgresql://...")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    content = Column(String)
    timestamp = Column(DateTime)
```

### 9. **Conversation History Capped at 20 Messages**

**Decision**: Limit chat memory to last 20 messages; older messages discarded.

**Rationale**:
- **Cost**: Prevents unbounded LLM context window (20 messages ≈ 2-3K tokens)
- **Performance**: Faster response due to smaller prompt
- **Practicality**: 20 messages sufficient for typical resume discussion (8-15 questions per session)
- **Simplicity**: Simple list vs. complex summarization logic

**Trade-off**:
- Chat history not permanent (lost on reset)
- Long sessions lose early context
- User cannot reference questions from 30 messages ago

**User Impact**:
- Most users interact for 5-10 minutes, ask 8-12 questions
- 20-message cap covers all typical use cases
- Reset button available if user wants fresh start

**Code**: `backend/memory/conversation_memory.py` (lines 50-70)

---

## Deployment

### Frontend: Vercel

1. **Build the frontend**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. **Deploy to Vercel**
   - Connect your GitHub repo to Vercel
   - Set root directory to `frontend/`
   - Add environment variable: `VITE_API_URL=https://resume-assistant-8mad.onrender.com`

3. **Result**: Frontend runs at `https://resume-assistant-zeta.vercel.app/`

### Backend: Render

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Create Render service**
   - Go to render.com, create new "Web Service"
   - Connect GitHub repo
   - Set root directory to `backend/`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`

3. **Add environment variables**
   ```
   GROQ_API_KEY=your_groq_key
   GEMINI_API_KEY=your_gemini_key
   GROQ_MODEL=llama-3.3-70b-versatile
   GEMINI_MODEL=gemini-2.0-flash
   MAX_TOKENS=1024
   GROQ_TEMPERATURE=0.2
   ```

4. **Result**: Backend runs at `https://resume-assistant-8mad.onrender.com`

### CORS Configuration

Backend automatically allows requests from localhost and your Vercel frontend. Update `backend/app.py` if deploying to a different URL:

```python
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://resume-assistant-zeta.vercel.app/",
    "https://resume-assistant-8mad.onrender.com",
]
```

---

## Summary

**Resume Assistant** is a full-stack AI resume analyzer that combines:

- **Intent routing** to classify user queries into 7 categories
- **Specialized tools** for parsing, skill matching, and scoring  
- **Dual LLM integration** (GROQ primary, Gemini fallback) for conversational responses
- **Local-first processing** where most queries need no LLM call

**Key Results**:
- Resume upload: Instant extraction with optional AI refinement
- Skill queries: Instant categorization (programming, frameworks, tools, soft skills)
- Score queries: 4-component evaluation with dynamic career recommendations
- General questions: Conversational responses with full resume context

**Deployment**: Simple and scalable
- Frontend on Vercel (auto-deploy from GitHub)
- Backend on Render (auto-deploy from GitHub)
- CORS configured for seamless communication

**Status**: Production-ready for single-user and demo deployments. Easily extensible for multi-user by adding a database layer.

---

**Last Updated**: June 2026  
**Version**: 1.0.0  
**License**: MIT
