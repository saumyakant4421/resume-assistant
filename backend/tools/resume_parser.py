import pdfplumber
import re
import json
import os
from typing import List, Dict, Any
from models.schemas import ResumeData


class ResumeParser:
    """Parse resumes (PDF or text) and extract structured data."""
    
    def parse(self, file_path: str) -> ResumeData:
        """Parse resume file and extract structured data."""
        
        # Extract raw text
        if file_path.lower().endswith('.pdf'):
            raw_text = self._extract_pdf(file_path)
        else:
            # Assume text file
            raw_text = self._extract_text(file_path)
        
        if not raw_text:
            raise ValueError("Could not extract text from resume")
        
        # Extract structured data
        name = self._extract_name(raw_text)
        skills = self._extract_skills(raw_text)
        experience = self._extract_experience(raw_text)
        education = self._extract_education(raw_text)

        # If the resume is ambiguous or section parsing is weak, let GROQ infer a cleaner structure.
        groq_data = self._extract_with_groq(raw_text)
        if groq_data:
            name = groq_data.get("name", name) or name
            skills = groq_data.get("skills", skills) or skills
            experience = groq_data.get("experience", experience) or experience
            education = groq_data.get("education", education) or education

        experience = self._normalize_experience_entries(experience)
        education = self._normalize_education_entries(education)
        
        return ResumeData(
            name=name,
            skills=skills,
            experience=experience,
            education=education,
            raw_text=raw_text
        )
    
    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error reading PDF: {str(e)}")
    
    def _extract_text(self, file_path: str) -> str:
        """Extract text from text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            raise ValueError(f"Error reading text file: {str(e)}")
    
    def _extract_name(self, text: str) -> str:
        """Extract candidate name (usually first line or after header)."""
        lines = text.split('\n')
        
        # Try to find name in first few lines
        for i, line in enumerate(lines[:5]):
            line = line.strip()
            if line and len(line) < 50 and not any(x in line.lower() for x in ['experience', 'skills', 'education', 'email', 'phone']):
                return line
        
        return ""
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills section - handles various formats."""
        skills = []
        text_lower = text.lower()
        
        # Find skills section with flexible keywords
        skill_keywords = ['skill', 'skills', 'technical skills', 'core competencies', 'competencies', 'expertise']
        skills_idx = -1
        skill_keyword_len = 0
        
        for keyword in skill_keywords:
            idx = text_lower.find(keyword)
            if idx != -1:
                skills_idx = idx
                skill_keyword_len = len(keyword)
                break
        
        if skills_idx == -1:
            return skills
        
        # Find the end of skills section (next major section)
        next_section_markers = ['experience', 'education', 'project', 'award', 'certification', 'publication']
        skills_end = len(text)
        for marker in next_section_markers:
            idx = text_lower.find(marker, skills_idx + skill_keyword_len + 10)
            if idx != -1 and idx < skills_end:
                skills_end = idx
        
        # Extract skills section
        skills_section = text[skills_idx:skills_end]
        lines = skills_section.split('\n')[1:20]  # First 20 lines after "Skills"
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 1 and len(line) < 100:
                # Skip lines that are section headers
                if any(x in line.lower() for x in next_section_markers):
                    break
                
                # Clean up the line
                line = re.sub(r'^[-•*]\s*', '', line)  # Remove bullets
                line = re.sub(r'^\d+\.\s*', '', line)  # Remove numbering
                line = re.sub(r'\s+', ' ', line)  # Normalize spaces
                line = line.strip()
                
                if line and line not in skills and len(line) > 1:
                    skills.append(line)
        
        return skills[:20]  # Limit to 20 skills
    
    def _extract_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience - handles various formats."""
        experience = []
        text_lower = text.lower()
        
        # Find experience section with flexible keywords
        exp_keywords = ['experience', 'professional experience', 'work experience', 'employment', 'career']
        exp_idx = -1
        exp_keyword_len = 0
        
        for keyword in exp_keywords:
            idx = text_lower.find(keyword)
            if idx != -1:
                exp_idx = idx
                exp_keyword_len = len(keyword)
                break
        
        if exp_idx == -1:
            return experience
        
        # Find the end of experience section (next major section or end of text)
        next_section_markers = ['education', 'skill', 'certification', 'project', 'award', 'publication']
        exp_end = len(text)
        for marker in next_section_markers:
            idx = text_lower.find(marker, exp_idx + exp_keyword_len + 10)
            if idx != -1 and idx < exp_end:
                exp_end = idx
        
        # Extract the experience section
        exp_section = text[exp_idx:exp_end]
        lines = exp_section.split('\n')[1:]
        
        # Parse experience entries more flexibly.
        # New entries typically start with a title/company/date line. Bullets and
        # continuation lines are appended to the current experience entry.
        job_indicators = [
            'engineer', 'manager', 'developer', 'analyst', 'consultant', 'director',
            'specialist', 'architect', 'lead', 'senior', 'junior', 'staff', 'associate',
            'advisor', 'representative', 'officer', 'coordinator', 'administrator'
        ]
        current_entry = ""

        for raw_line in lines:
            line = raw_line.strip()

            if not line or len(line) < 2:
                continue

            if any(x in line.lower() for x in next_section_markers):
                break

            is_bullet = line.startswith(("•", "-", "*"))
            has_job_title = any(indicator in line.lower() for indicator in job_indicators)
            has_company_hint = any(sep in line for sep in [" at ", " | ", " - ", ", "])
            has_date_hint = bool(re.search(r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d{4})\b', line.lower()))

            # Start a new entry when we see a likely job title/company/date line.
            if has_job_title and (has_company_hint or has_date_hint or len(line) < 160):
                if current_entry:
                    experience.append({"entry": current_entry.strip()})
                current_entry = re.sub(r'^[•\-*]\s*', '', line)
                continue

            # Otherwise, append bullet/continuation content to the current entry.
            if current_entry:
                cleaned = re.sub(r'^[•\-*]\s*', '', line)
                current_entry = f"{current_entry} {cleaned}".strip()
            elif is_bullet:
                current_entry = re.sub(r'^[•\-*]\s*', '', line)

        if current_entry:
            experience.append({"entry": current_entry.strip()})
        
        return experience[:15]  # Limit to 15 entries
    
    def _extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education - handles various formats."""
        education = []
        text_lower = text.lower()
        
        # Find education section with flexible keywords
        edu_keywords = ['education', 'academic', 'degree', 'university', 'college']
        edu_idx = -1
        edu_keyword_len = 0
        
        for keyword in edu_keywords:
            idx = text_lower.find(keyword)
            if idx != -1:
                edu_idx = idx
                edu_keyword_len = len(keyword)
                break
        
        if edu_idx == -1:
            return education
        
        # Find the end of education section
        next_section_markers = ['experience', 'skill', 'certification', 'project', 'award', 'publication']
        edu_end = len(text)
        for marker in next_section_markers:
            idx = text_lower.find(marker, edu_idx + edu_keyword_len + 10)
            if idx != -1 and idx < edu_end:
                edu_end = idx
        
        # Extract education section
        edu_section = text[edu_idx:edu_end]
        lines = edu_section.split('\n')[1:]
        
        # Parse education entries - look for degree/university combinations.
        # We combine adjacent lines into a single entry when they belong together.
        degree_keywords = ['bs', 'ba', 'ms', 'ma', 'phd', 'mba', 'degree', 'diploma', 'certificate',
                          'bachelor', 'master', 'doctorate', 'associate', 'graduate']
        school_keywords = ['university', 'college', 'school', 'institute', 'academy']

        current_entry = ""
        
        for raw_line in lines:
            line = raw_line.strip()
            
            # Skip empty lines
            if not line or len(line) < 5:
                continue
            
            # Skip if it contains other section keywords
            if any(x in line.lower() for x in next_section_markers):
                break
            
            # Look for education entries
            has_degree = any(keyword in line.lower() for keyword in degree_keywords)
            has_school = any(keyword in line.lower() for keyword in school_keywords)

            if has_school and has_degree:
                if current_entry:
                    education.append({"entry": current_entry.strip()})
                current_entry = line
                continue

            if has_school or has_degree:
                if current_entry:
                    # Keep the current education item compact and append only once.
                    current_entry = f"{current_entry} {line}".strip()
                else:
                    current_entry = line
                continue

            # Append date/location/honors lines to the current education item.
            if current_entry and len(line) < 120:
                current_entry = f"{current_entry} {line}".strip()

        if current_entry:
            education.append({"entry": current_entry.strip()})
        
        return education[:10]  # Limit to 10 entries

    def _extract_with_groq(self, text: str) -> Dict[str, Any]:
        """Optionally use GROQ to infer a cleaner structured resume layout.

        This is best-effort and only runs when GROQ_API_KEY is configured.
        If the Groq call fails, local parsing is used instead.
        """

        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            return {}

        groq_url = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/responses")
        model = os.getenv("GROQ_PARSE_MODEL", os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"))
        max_output_tokens = int(os.getenv("MAX_TOKENS", "1024"))
        temperature = float(os.getenv("GROQ_TEMPERATURE", "0.0"))

        prompt = (
            "You are extracting structured data from a resume.\n"
            "Return ONLY valid JSON with this exact shape: \n"
            "{\n"
            '  "name": "string",\n'
            '  "skills": ["string"],\n'
            '  "experience": [{"entry": "string"}],\n'
            '  "education": [{"entry": "string"}]\n'
            "}\n\n"
            "Rules:\n"
            "- Combine multi-line job entries into one experience item per real role.\n"
            "- Combine degree, school, year, honors into one education item per real credential.\n"
            "- Do not count headings or line fragments as entries.\n"
            "- If a section is missing, return an empty array.\n\n"
            "Resume text:\n"
            f"{text}"
        )

        payload = {
            "model": model,
            "input": prompt,
            "max_output_tokens": max_output_tokens,
            "temperature": temperature,
            "text": {"format": {"type": "json_object"}},
        }
        headers = {
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json",
        }

        try:
            try:
                import requests
                resp = requests.post(groq_url, json=payload, headers=headers, timeout=20)
                resp.raise_for_status()
                data = resp.json()
            except Exception:
                import urllib.request
                import urllib.error

                req = urllib.request.Request(
                    groq_url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = json.loads(resp.read().decode("utf-8"))

            text_response = self._extract_groq_text(data)
            if not text_response:
                return {}

            parsed = json.loads(text_response)
            if not isinstance(parsed, dict):
                return {}

            parsed.setdefault("name", "")
            parsed.setdefault("skills", [])
            parsed.setdefault("experience", [])
            parsed.setdefault("education", [])

            if not isinstance(parsed["skills"], list):
                parsed["skills"] = []
            if not isinstance(parsed["experience"], list):
                parsed["experience"] = []
            if not isinstance(parsed["education"], list):
                parsed["education"] = []

            # Normalize list items into the {"entry": ...} shape used by the app.
            parsed["experience"] = [item if isinstance(item, dict) and "entry" in item else {"entry": str(item)} for item in parsed["experience"]]
            parsed["education"] = [item if isinstance(item, dict) and "entry" in item else {"entry": str(item)} for item in parsed["education"]]
            parsed["skills"] = [str(item).strip() for item in parsed["skills"] if str(item).strip()]

            return parsed
        except Exception:
            return {}

    def _extract_groq_text(self, data: Any) -> str:
        """Extract assistant text from Groq Responses API payload."""

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

        # Compatibility with chat-completion-like shapes.
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            message = (choices[0] or {}).get("message", {}) if isinstance(choices[0], dict) else {}
            content = message.get("content") if isinstance(message, dict) else ""
            if isinstance(content, str):
                return content

        if isinstance(data.get("text"), str):
            return data["text"]

        return ""

    def _normalize_experience_entries(self, entries: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Merge role detail fragments into the preceding real experience entry."""

        normalized: List[Dict[str, str]] = []
        job_indicators = [
            'engineer', 'manager', 'developer', 'analyst', 'consultant', 'director',
            'architect', 'lead', 'senior', 'junior', 'staff', 'associate',
            'advisor', 'representative', 'officer', 'coordinator', 'administrator', 'intern',
        ]

        for item in entries:
            entry = (item or {}).get("entry", "") if isinstance(item, dict) else str(item)
            entry = re.sub(r'\s+', ' ', entry).strip()
            if not entry:
                continue

            lower = entry.lower()
            has_job_title = any(indicator in lower for indicator in job_indicators)
            has_company_hint = ' at ' in lower or ' - ' in entry or ' | ' in entry or bool(re.search(r'\b[A-Z]{2,}\b', entry))
            has_date_hint = bool(re.search(r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d{4})\b', lower))
            looks_like_role = has_job_title or has_company_hint or has_date_hint
            looks_like_fragment = not looks_like_role

            if normalized and looks_like_fragment:
                normalized[-1]["entry"] = f"{normalized[-1]['entry']} {entry}".strip()
            else:
                normalized.append({"entry": entry})

        return normalized

    def _normalize_education_entries(self, entries: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Merge education fragments into a single coherent education entry when possible."""

        normalized: List[Dict[str, str]] = []
        degree_keywords = ['bs', 'ba', 'ms', 'ma', 'phd', 'mba', 'degree', 'diploma', 'certificate',
                          'bachelor', 'master', 'doctorate', 'associate', 'graduate']
        school_keywords = ['university', 'college', 'school', 'institute', 'academy']

        for item in entries:
            entry = (item or {}).get("entry", "") if isinstance(item, dict) else str(item)
            entry = re.sub(r'\s+', ' ', entry).strip()
            if not entry:
                continue

            lower = entry.lower()
            looks_like_academic = any(keyword in lower for keyword in degree_keywords) or any(keyword in lower for keyword in school_keywords)

            if normalized and not looks_like_academic and len(entry) < 120:
                normalized[-1]["entry"] = f"{normalized[-1]['entry']} {entry}".strip()
            else:
                normalized.append({"entry": entry})

        return normalized