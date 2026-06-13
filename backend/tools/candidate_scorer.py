from typing import Dict, Any


class CandidateScorer:
    """Score and evaluate candidate based on resume data."""
    
    def run(self, resume: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score candidate on multiple dimensions.
        
        Args:
            resume: Resume data dict with skills, experience, education
            
        Returns:
            Scoring breakdown with overall score
        """
        skills = resume.get("skills", [])
        experience = resume.get("experience", [])
        education = resume.get("education", [])

        technical_score = self._score_technical_skills(skills)
        experience_score = self._score_experience(experience)
        education_score = self._score_education(education)
        completeness_score = self._score_completeness(resume)

        filled_fields = sum([
            1 if resume.get("name") else 0,
            1 if skills else 0,
            1 if experience else 0,
            1 if education else 0,
        ])

        scores = {
            "technical_skills": {
                "score": round(technical_score, 2),
                "count": len(skills),
                "description": f"Has {len(skills)} skill entries",
            },
            "experience": {
                "score": round(experience_score, 2),
                "count": len(experience),
                "description": f"Has {len(experience)} experience entries",
            },
            "education": {
                "score": round(education_score, 2),
                "count": len(education),
                "description": f"Has {len(education)} education entries",
            },
            "completeness": {
                "score": round(completeness_score, 2),
                "description": "Checks for summary, projects, certifications, and links",
            },
        }

        overall = round(
            technical_score * 0.40 +
            experience_score * 0.35 +
            education_score * 0.15 +
            completeness_score * 0.10,
            2,
        )

        completeness_percentage = round((filled_fields / 4) * 100, 2)

        return {
            "overall": overall,
            "overall_score": overall,
            "technical_score": round(technical_score, 2),
            "experience_score": round(experience_score, 2),
            "education_score": round(education_score, 2),
            "completeness_score": round(completeness_score, 2),
            "scores": scores,
            "completeness_percentage": completeness_percentage,
            "max_score": 10.0,
            "rating": self._get_rating(overall),
            "summary": self._get_summary(overall, completeness_percentage)
        }

    def _score_technical_skills(self, skills: list) -> float:
        """Score technical skills with a capped normalization."""
        unique_skills = len({skill.lower() for skill in skills if skill})
        return min((unique_skills / 15) * 10, 10.0)

    def _score_experience(self, experience: list) -> float:
        """Score experience by number of entries."""
        entry_count = len(experience)
        return min((entry_count / 5) * 10, 10.0)

    def _score_education(self, education: list) -> float:
        """Score education by number of entries."""
        entry_count = len(education)
        return min((entry_count / 3) * 10, 10.0)

    def _score_completeness(self, resume: Dict[str, Any]) -> float:
        """Score how complete the resume structure is."""
        raw_text = str(resume.get("raw_text", "")).lower()
        signals = [
            any(keyword in raw_text for keyword in ["summary", "professional summary", "profile"]),
            any(keyword in raw_text for keyword in ["project", "projects"]),
            any(keyword in raw_text for keyword in ["certification", "certifications", "certificate"]),
            any(keyword in raw_text for keyword in ["linkedin", "github", "portfolio", "website"]),
        ]
        return (sum(1 for signal in signals if signal) / len(signals)) * 10
    
    def _get_rating(self, score: float) -> str:
        """Get rating based on score."""
        if score >= 8.5:
            return "Excellent"
        elif score >= 7.0:
            return "Very Good"
        elif score >= 5.5:
            return "Good"
        elif score >= 4.0:
            return "Fair"
        else: 
            return "Needs Improvement"
    
    def _get_summary(self, overall_score: float, completeness: float) -> str:
        """Get evaluation summary."""
        parts = []
        
        if overall_score >= 8.5:
            parts.append("Strong candidate profile")
        elif overall_score >= 7.0:
            parts.append("Solid candidate profile")
        elif overall_score >= 5.5:
            parts.append("Adequate candidate profile")
        else:
            parts.append("Limited candidate profile")
        
        if completeness >= 80:
            parts.append("with comprehensive resume information")
        elif completeness >= 50:
            parts.append("with partial resume information")
        else:
            parts.append("with minimal resume information")
        
        return " ".join(parts)