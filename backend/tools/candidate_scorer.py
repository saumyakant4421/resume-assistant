import json
import os
from typing import Dict, Any, List

try:
    import requests
    HAS_REQUESTS = True
except Exception:
    HAS_REQUESTS = False


class CandidateScorer:
    """Score and evaluate candidate based on resume data."""

    DEFAULT_ROLE_PROFILES = [
        {
            "role": "Software / Full-Stack Developer",
            "keywords": [
                "python", "javascript", "typescript", "react", "node", "fastapi", "flask",
                "api", "rest", "sql", "docker", "git", "web", "frontend", "backend",
            ],
        },
        {
            "role": "Data Analyst / Data Scientist",
            "keywords": [
                "python", "sql", "pandas", "numpy", "machine learning", "statistics", "analytics",
                "excel", "tableau", "power bi", "data", "model", "visualization", "dashboard",
            ],
        },
        {
            "role": "DevOps / Cloud Engineer",
            "keywords": [
                "aws", "gcp", "azure", "docker", "kubernetes", "linux", "ci/cd", "jenkins",
                "terraform", "deployment", "cloud", "devops", "monitoring", "automation",
            ],
        },
        {
            "role": "Product / Project Coordinator",
            "keywords": [
                "project management", "agile", "scrum", "leadership", "communication", "coordination",
                "planning", "stakeholder", "delivery", "roadmap", "documentation", "organization",
            ],
        },
        {
            "role": "Sales / Client Relations",
            "keywords": [
                "salesforce", "client relations", "relationship management", "communication", "sales",
                "account management", "outlook", "english", "customer", "service", "negotiation",
            ],
        },
    ]

    ROLE_EXPANSION_PROMPT = (
        "You are a career mapping assistant. Based on a resume, infer the most relatable career paths. "
        "Return ONLY valid JSON with this exact shape:\n"
        "{\n"
        '  "role_fits": [\n'
        '    {"role": "string", "fit_percent": 0.0, "reasons": ["string"]}\n'
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        "- Return 3 to 5 roles max.\n"
        "- Prefer realistic, specific, modern roles.\n"
        "- Avoid generic titles like 'Generalist'.\n"
        "- Use the resume context to justify the percentages.\n"
        "- Percentages must be between 0 and 100.\n"
    )
    
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
        score_reasons = self._build_score_reasons(resume, skills, experience, education)
        role_fits = self._build_role_fits(resume)

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
            "score_reasons": score_reasons,
            "role_fits": role_fits,
            "top_recommendation": role_fits[0]["role"] if role_fits else "",
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

    def _build_score_reasons(
        self,
        resume: Dict[str, Any],
        skills: List[str],
        experience: List[Dict[str, Any]],
        education: List[Dict[str, Any]],
    ) -> Dict[str, List[str]]:
        """Explain why each score landed where it did."""

        reasons = {
            "technical": [],
            "experience": [],
            "education": [],
            "completeness": [],
        }

        unique_skills = len({skill.lower() for skill in skills if skill})
        if unique_skills:
            reasons["technical"].append(f"Detected {unique_skills} distinct skill signal(s) in the resume.")
            reasons["technical"].append("Technical score rises with broader, clearly named skill coverage.")
        else:
            reasons["technical"].append("No clearly listed skills were found, so technical depth is limited.")

        if experience:
            reasons["experience"].append(f"Found {len(experience)} experience entr{'y' if len(experience) == 1 else 'ies'}.")
            reasons["experience"].append("Experience score rewards multiple role entries and visible career progression.")
        else:
            reasons["experience"].append("No experience section was detected in the resume.")

        if education:
            reasons["education"].append(f"Found {len(education)} education entr{'y' if len(education) == 1 else 'ies'}.")
            reasons["education"].append("Education score improves when degrees, schools, or certifications are explicitly listed.")
        else:
            reasons["education"].append("No education section was detected in the resume.")

        raw_text = str(resume.get("raw_text", "")).lower()
        completeness_hits = []
        if any(keyword in raw_text for keyword in ["summary", "professional summary", "profile"]):
            completeness_hits.append("summary/profile section")
        if any(keyword in raw_text for keyword in ["project", "projects"]):
            completeness_hits.append("project details")
        if any(keyword in raw_text for keyword in ["certification", "certifications", "certificate"]):
            completeness_hits.append("certifications")
        if any(keyword in raw_text for keyword in ["linkedin", "github", "portfolio", "website"]):
            completeness_hits.append("links or portfolio")

        if completeness_hits:
            reasons["completeness"].append(f"Resume includes: {', '.join(completeness_hits)}.")
        else:
            reasons["completeness"].append("The resume looks sparse in supporting sections like summary, projects, certifications, or links.")

        return reasons

    def _build_role_fits(self, resume: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Estimate which career roles fit the candidate best."""

        groq_role_fits = self._build_role_fits_with_groq(resume)
        if groq_role_fits:
            return groq_role_fits

        skills_text = " ".join(resume.get("skills", [])).lower()
        experience_text = " ".join(
            (item or {}).get("entry", "") if isinstance(item, dict) else str(item)
            for item in resume.get("experience", [])
        ).lower()
        education_text = " ".join(
            (item or {}).get("entry", "") if isinstance(item, dict) else str(item)
            for item in resume.get("education", [])
        ).lower()
        combined_text = f"{skills_text} {experience_text} {education_text} {str(resume.get('raw_text', '')).lower()}"

        role_fits: List[Dict[str, Any]] = []
        for profile in self.DEFAULT_ROLE_PROFILES:
            keyword_matches = []
            for keyword in profile["keywords"]:
                if keyword in combined_text:
                    keyword_matches.append(keyword)

            match_ratio = len(keyword_matches) / len(profile["keywords"])
            fit_percent = round(min(match_ratio * 100, 100.0), 2)

            reasons = []
            if keyword_matches:
                reasons.append(f"Matched {len(keyword_matches)} role signal(s): {', '.join(keyword_matches[:5])}.")
            else:
                reasons.append("No strong keyword overlap detected for this role.")

            role_fits.append({
                "role": profile["role"],
                "fit_percent": fit_percent,
                "reasons": reasons,
            })

        role_fits.sort(key=lambda item: item["fit_percent"], reverse=True)
        return role_fits[:3]

    def _build_role_fits_with_groq(self, resume: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Use GROQ to infer dynamic career roles when available."""

        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            return []

        groq_url = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/responses")
        model = os.getenv("GROQ_ROLE_MODEL", os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"))
        max_output_tokens = int(os.getenv("MAX_TOKENS", "768"))
        temperature = float(os.getenv("GROQ_TEMPERATURE", "0.2"))

        skills = resume.get("skills", [])
        experience = resume.get("experience", [])
        education = resume.get("education", [])

        resume_lines = [
            f"Name: {resume.get('name', '')}",
            f"Skills: {', '.join(skills)}",
            "Experience:",
        ]

        for item in experience[:6]:
            entry = item.get("entry", "") if isinstance(item, dict) else str(item)
            if entry:
                resume_lines.append(f"- {entry}")

        resume_lines.append("Education:")
        for item in education[:4]:
            entry = item.get("entry", "") if isinstance(item, dict) else str(item)
            if entry:
                resume_lines.append(f"- {entry}")

        payload = {
            "model": model,
            "input": f"{self.ROLE_EXPANSION_PROMPT}\n\nResume:\n" + "\n".join(resume_lines),
            "max_output_tokens": max_output_tokens,
            "temperature": temperature,
            "text": {"format": {"type": "json_object"}},
        }
        headers = {
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json",
        }

        try:
            if HAS_REQUESTS:
                response = requests.post(groq_url, json=payload, headers=headers, timeout=20)
                response.raise_for_status()
                data = response.json()
            else:
                import urllib.request

                request = urllib.request.Request(
                    groq_url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(request, timeout=20) as response:
                    data = json.loads(response.read().decode("utf-8"))

            text_response = self._extract_groq_text(data)
            if not text_response:
                return []

            parsed = json.loads(text_response)
            role_fits = parsed.get("role_fits", []) if isinstance(parsed, dict) else []
            return self._normalize_role_fits(role_fits)
        except Exception:
            return []

    def _extract_groq_text(self, data: Any) -> str:
        """Extract assistant text from a GROQ Responses API payload."""

        if not isinstance(data, dict):
            return ""

        out = data.get("output")
        if isinstance(out, list):
            for item in out:
                if not isinstance(item, dict):
                    continue
                content = item.get("content")
                if isinstance(content, list):
                    texts = []
                    for c in content:
                        if isinstance(c, dict) and c.get("type") == "output_text" and "text" in c:
                            texts.append(c["text"])
                        elif isinstance(c, dict) and "text" in c:
                            texts.append(c["text"])
                    if texts:
                        return "\n".join(texts)

        if isinstance(data.get("text"), str):
            return data["text"]

        return ""

    def _normalize_role_fits(self, role_fits: Any) -> List[Dict[str, Any]]:
        """Validate and normalize Groq-generated role fit recommendations."""

        if not isinstance(role_fits, list):
            return []

        normalized: List[Dict[str, Any]] = []
        for item in role_fits:
            if not isinstance(item, dict):
                continue

            role = str(item.get("role", "")).strip()
            if not role:
                continue

            try:
                fit_percent = float(item.get("fit_percent", 0.0))
            except (TypeError, ValueError):
                fit_percent = 0.0

            reasons = item.get("reasons", [])
            if not isinstance(reasons, list):
                reasons = []

            normalized.append({
                "role": role,
                "fit_percent": round(max(0.0, min(fit_percent, 100.0)), 2),
                "reasons": [str(reason).strip() for reason in reasons if str(reason).strip()][:3],
            })

        normalized.sort(key=lambda item: item["fit_percent"], reverse=True)
        return normalized[:5]
    
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