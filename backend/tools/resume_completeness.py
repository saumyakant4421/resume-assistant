from typing import Dict, Any, List


class ResumeCompletenessTool:
    """Check resume quality and surface missing high-value sections."""

    SUMMARY_KEYWORDS = ["summary", "professional summary", "profile"]
    PROJECT_KEYWORDS = ["project", "projects"]
    CERTIFICATION_KEYWORDS = ["certification", "certifications", "certificate"]
    LINK_KEYWORDS = ["linkedin", "github", "portfolio", "website"]

    def run(self, resume: Dict[str, Any]) -> Dict[str, Any]:
        """Return a completeness assessment of the resume."""

        raw_text = str(resume.get("raw_text", "")).lower()
        missing_data: List[str] = []

        if not any(keyword in raw_text for keyword in self.SUMMARY_KEYWORDS):
            missing_data.append("summary")

        if not any(keyword in raw_text for keyword in self.PROJECT_KEYWORDS):
            missing_data.append("project descriptions")

        if not any(keyword in raw_text for keyword in self.CERTIFICATION_KEYWORDS):
            missing_data.append("certifications")

        if not any(keyword in raw_text for keyword in self.LINK_KEYWORDS):
            missing_data.append("links")

        score = max(0.0, 10.0 - (len(missing_data) * 2.0))

        if missing_data:
            answer = f"Resume is missing {', '.join(missing_data)}."
        else:
            answer = "Resume has the major structural sections expected for a strong screening profile."

        return {
            "answer": answer,
            "confidence": 0.92 if missing_data else 0.98,
            "source": "resume",
            "missing_data": missing_data,
            "completeness_score": round(score, 2),
            "checked_sections": ["summary", "projects", "certifications", "links"],
        }