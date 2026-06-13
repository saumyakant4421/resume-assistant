class IntentRouter:
    """Detect user intent from query."""
    
    SKILL_KEYWORDS = ["skill", "skills", "proficient", "expertise", "experienced", "programming language", "tool", "technology"]
    EXPERIENCE_KEYWORDS = ["experience", "worked", "job", "employment", "position", "role", "company", "years", "duration"]
    EDUCATION_KEYWORDS = ["education", "degree", "university", "college", "graduated", "studied", "major"]
    EVALUATE_KEYWORDS = ["evaluate", "score", "rate", "assess", "quality", "suitable", "fit", "match"]
    COMPLETENESS_KEYWORDS = ["complete", "completeness", "missing", "gap", "quality", "certification", "certifications", "project", "projects", "links", "portfolio"]
    SUMMARY_KEYWORDS = ["summary", "summarize", "brief", "overview", "highlights"]

    def classify(self, query: str) -> dict:
        """Return a routing decision with tool and reason."""
        intent = self.detect(query)

        tool_map = {
            "SKILL": "SkillMatcher",
            "EXPERIENCE": "ResumeParser",
            "EDUCATION": "ResumeParser",
            "EVALUATE": "CandidateScorer",
            "COMPLETENESS": "ResumeCompletenessTool",
            "SUMMARY": "ResumeParser",
            "GENERAL": "GeminiAgent",
        }

        reason_map = {
            "SKILL": "User asked about candidate skills",
            "EXPERIENCE": "User asked about work history",
            "EDUCATION": "User asked about education details",
            "EVALUATE": "User asked for scoring or assessment",
            "COMPLETENESS": "User asked about resume quality or missing sections",
            "SUMMARY": "User asked for a resume summary",
            "GENERAL": "No narrow intent matched, so use the LLM with context",
        }

        return {
            "intent": intent,
            "tool_used": tool_map[intent],
            "reason": reason_map[intent],
        }
    
    def detect(self, query: str) -> str:
        """
        Detect intent from user query.
        Returns one of: SKILL, EXPERIENCE, EDUCATION, EVALUATE, COMPLETENESS, SUMMARY, GENERAL
        """
        query_lower = query.lower()
        
        # Check for resume completeness / quality intent first (highest priority for quality queries)
        for keyword in self.COMPLETENESS_KEYWORDS:
            if keyword in query_lower:
                return "COMPLETENESS"
        
        # Check for evaluate intent (second priority for scoring)
        for keyword in self.EVALUATE_KEYWORDS:
            if keyword in query_lower:
                return "EVALUATE"
        
        # Check for skill intent
        for keyword in self.SKILL_KEYWORDS:
            if keyword in query_lower:
                return "SKILL"
        
        # Check for experience intent
        for keyword in self.EXPERIENCE_KEYWORDS:
            if keyword in query_lower:
                return "EXPERIENCE"
        
        # Check for education intent
        for keyword in self.EDUCATION_KEYWORDS:
            if keyword in query_lower:
                return "EDUCATION"
        
        # Check for summary intent
        for keyword in self.SUMMARY_KEYWORDS:
            if keyword in query_lower:
                return "SUMMARY"
        
        # Default to general
        return "GENERAL"