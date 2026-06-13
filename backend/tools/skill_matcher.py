from typing import List, Dict, Any


class SkillMatcher:
    """Match and validate skills from resume against queries."""
    
    def run(self, resume_skills: List[str], query: str) -> Dict[str, Any]:
        """
        Check if skills mentioned in query exist in resume.
        
        Args:
            resume_skills: List of skills from resume
            query: User query
            
        Returns:
            Dict with found status, matching skills, and confidence
        """
        if not resume_skills:
            return {
                "found": False,
                "skills": [],
                "confidence": 0.0
            }
        
        query_lower = query.lower()
        found_skills = []
        
        for skill in resume_skills:
            skill_lower = skill.lower()
            
            # Exact match
            if skill_lower in query_lower:
                found_skills.append({
                    "skill": skill,
                    "match_type": "exact"
                })
            # Partial match (substring)
            elif self._is_substring_match(skill_lower, query_lower):
                found_skills.append({
                    "skill": skill,
                    "match_type": "partial"
                })
        
        if found_skills:
            confidence = min(len(found_skills) / len(resume_skills), 1.0)
            return {
                "found": True,
                "skills": found_skills,
                "confidence": confidence,
                "total_resume_skills": len(resume_skills)
            }
        
        return {
            "found": False,
            "skills": [],
            "confidence": 0.0,
            "total_resume_skills": len(resume_skills)
        }
    
    def _is_substring_match(self, skill: str, query: str) -> bool:
        """Check if skill is a meaningful substring of query."""
        words = query.split()
        
        for word in words:
            if len(skill) > 2 and skill in word:
                return True
        
        return False
    
    def get_all_skills(self, resume_skills: List[str]) -> Dict[str, Any]:
        """Get all skills in a structured format."""
        return {
            "skills": resume_skills,
            "count": len(resume_skills),
            "categories": self._categorize_skills(resume_skills)
        }
    
    def _categorize_skills(self, skills: List[str]) -> Dict[str, List[str]]:
        """Categorize skills by type."""
        categories = {
            "programming": [],
            "frameworks": [],
            "tools": [],
            "soft_skills": [],
            "other": []
        }
        
        programming_keywords = ["python", "java", "javascript", "c++", "c#", "sql", "ruby", "php", "golang", "rust", "typescript"]
        framework_keywords = ["react", "angular", "vue", "django", "flask", "fastapi", "spring", "node", "express"]
        tool_keywords = [
            "git", "docker", "kubernetes", "aws", "azure", "gcp", "jenkins", "jira", "linux",
            "ms office", "microsoft office", "outlook", "salesforce", "tfs", "excel", "word", "powerpoint",
        ]
        soft_keywords = [
            "communication", "leadership", "teamwork", "project management", "agile",
            "client relations", "relationship management", "english", "presentation",
        ]
        
        for skill in skills:
            skill_lower = skill.lower()
            
            if any(kw in skill_lower for kw in programming_keywords):
                categories["programming"].append(skill)
            elif any(kw in skill_lower for kw in framework_keywords):
                categories["frameworks"].append(skill)
            elif any(kw in skill_lower for kw in tool_keywords):
                categories["tools"].append(skill)
            elif any(kw in skill_lower for kw in soft_keywords):
                categories["soft_skills"].append(skill)
            else:
                categories["other"].append(skill)
        
        return categories