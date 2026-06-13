from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from tempfile import NamedTemporaryFile
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from models.schemas import ResumeData, ChatRequest, AgentResponse
from memory.conversation_memory import memory
from agents.hiring_agents import HiringAgent
from tools.resume_parser import ResumeParser
from agents.intent_router import IntentRouter


def _get_allowed_origins() -> list[str]:
    """Build the CORS allowlist from environment variables and local defaults."""

    origins: list[str] = []

    # Explicit production origins for the Vercel deployments.
    origins.extend([
        "https://resume-assistant-git-main-saumya-kants-projects.vercel.app",
        "https://resume-assistant-i15qzkzv6-saumya-kants-projects.vercel.app",
    ])

    for env_name in ("FRONTEND_ORIGINS", "FRONTEND_URL"):
        raw_value = os.getenv(env_name, "")
        if not raw_value:
            continue

        for origin in raw_value.split(","):
            cleaned_origin = origin.strip()
            if cleaned_origin:
                origins.append(cleaned_origin)

    origins.extend([
        "http://localhost:5173",
        "http://localhost:3000",
    ])

    return list(dict.fromkeys(origins))

app = FastAPI(
    title="Resume Assistant API",
    description="AI-powered resume analysis and candidate evaluation system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
try:
    parser = ResumeParser()
    router = IntentRouter()
    agent = HiringAgent()
except Exception as e:
    raise RuntimeError(f"Failed to initialize components: {str(e)}")

# Store uploaded resume
current_resume: Optional[ResumeData] = None


@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload and parse a resume (PDF or text).
    Extracts structured data: name, skills, experience, education.
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        suffix = os.path.splitext(file.filename)[1] or ".txt"

        # Save file temporarily using a Windows-safe temp path.
        with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_path = temp_file.name
            content = await file.read()
            temp_file.write(content)
        
        # Parse resume
        resume_data = parser.parse(temp_path)
        
        # Save to memory
        memory.save_resume(resume_data.model_dump())
        
        global current_resume
        current_resume = resume_data
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return {
            "status": "success",
            "message": "Resume uploaded and parsed successfully",
            "data": resume_data.model_dump()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=AgentResponse)
async def chat(request: ChatRequest):
    """
    Process user query and return structured response.
    Uses intent detection to route to appropriate tool or LLM.
    """
    try:
        if not current_resume:
            raise HTTPException(status_code=400, detail="No resume uploaded. Please upload a resume first.")
        
        query = request.query.strip()
        if not query:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Add user message to memory
        memory.add_message("user", query)
        
        # Detect intent and record the internal routing decision.
        decision = router.classify(query)
        intent = decision["intent"]
        memory.set_intent(intent)
        memory.add_decision_log(intent=decision["intent"], tool_used=decision["tool_used"], reason=decision["reason"])
        
        # Get context
        context = memory.get_context()
        
        # Route to agent
        response = agent.process(
            query=query,
            intent=intent,
            resume_data=current_resume.dict(),
            context=context
        )
        
        # Add assistant message to memory
        memory.add_message("assistant", response["answer"])
        
        return AgentResponse(**response)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory")
async def get_memory():
    """Get current conversation memory (for debugging)."""
    return memory.get_context()


@app.post("/reset")
async def reset_conversation():
    """Reset conversation memory and resume."""
    global current_resume
    memory.reset()
    current_resume = None
    return {"status": "success", "message": "Conversation reset"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "Resume Assistant Backend"}
