from pydantic import BaseModel, Field
from typing import List, Optional


class EvaluationRoleFit(BaseModel):
    role: str = Field(..., description="Recommended career role")
    fit_percent: float = Field(..., ge=0.0, le=100.0, description="Role fit percentage")
    reasons: List[str] = Field(default_factory=list, description="Why this role fits")


class EvaluationInsights(BaseModel):
    score_reasons: dict[str, List[str]] = Field(default_factory=dict, description="Reasoning behind each score")
    role_fits: List[EvaluationRoleFit] = Field(default_factory=list, description="Recommended career roles")
    top_recommendation: str = Field(default="", description="Highest-fit career role")


class ResumeData(BaseModel):
    """Structured resume data extracted from uploaded file."""
    name: str = Field(default="", description="Candidate name")
    skills: List[str] = Field(default_factory=list, description="List of skills")
    experience: List[dict] = Field(default_factory=list, description="Work experience entries")
    education: List[dict] = Field(default_factory=list, description="Education entries")
    raw_text: str = Field(default="", description="Raw extracted text from resume")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "skills": ["Python", "FastAPI", "Machine Learning"],
                "experience": [{"title": "Engineer", "company": "Tech Corp", "duration": "2+ years"}],
                "education": [{"degree": "BS", "field": "Computer Science"}],
                "raw_text": "..."
            }
        }


class ChatRequest(BaseModel):
    """User chat query request."""
    query: str = Field(..., description="User question about the resume")


class AgentResponse(BaseModel):
    """Structured agent response following required format."""
    answer: str = Field(..., description="The answer to the user's query")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    source: str = Field(..., description="Source: 'resume' or 'inference'")
    missing_data: List[str] = Field(default_factory=list, description="Missing data fields")
    evaluation: Optional[EvaluationInsights] = Field(default=None, description="Detailed evaluation insights")
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "The candidate has experience with Python and FastAPI",
                "confidence": 0.95,
                "source": "resume",
                "missing_data": []
            }
        }