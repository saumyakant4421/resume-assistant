import json
import os
from typing import Any, Dict

from google import genai
from google.genai import types
try:
    import requests
    HAS_REQUESTS = True
except Exception:
    HAS_REQUESTS = False

from memory.conversation_memory import memory
from prompts.system_prompt import SYSTEM_PROMPT
from tools.candidate_scorer import CandidateScorer
from tools.resume_completeness import ResumeCompletenessTool
from tools.skill_matcher import SkillMatcher


class HiringAgent:
    """Main agent for processing hiring-related queries."""

    def __init__(self):
        self.skill_matcher = SkillMatcher()
        self.candidate_scorer = CandidateScorer()
        self.resume_completeness = ResumeCompletenessTool()
        # Prefer GROQ if configured, otherwise fall back to Gemini
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

        self.client = None
        self.client_source = None

        if self.groq_key:
            # GROQ configured; mark as groq client available. Concrete HTTP/SDK calls
            # will be implemented when endpoint/SDK details are provided.
            self.client = {"type": "groq", "api_key": self.groq_key}
            self.client_source = "groq"
        elif self.api_key:
            # Gemini (Google) client
            self.client = genai.Client(api_key=self.api_key)
            self.client_source = "gemini"
        else:
            self.client = None
            self.client_source = None

    def process(
        self,
        query: str,
        intent: str,
        resume_data: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Route the query to the correct tool or the Gemini fallback."""

        try:
            if intent == "SKILL":
                return self._handle_skill_query(query, resume_data)

            if intent == "EVALUATE":
                return self._handle_evaluate_query(query, resume_data)

            if intent == "COMPLETENESS":
                return self._handle_completeness_query(query, resume_data)

            if intent == "SUMMARY":
                return self._handle_summary_query(query, resume_data)

            return self._handle_general_query(query, resume_data, context)

        except Exception as e:
            return {
                "answer": f"Error processing query: {str(e)}",
                "confidence": 0.0,
                "source": "inference",
                "missing_data": ["Unable to process query"],
            }

    def _log_internal_decision(self, intent: str, tool_used: str, reason: str) -> None:
        """Store routing decisions and tool usage internally."""

        memory.add_decision_log(intent=intent, tool_used=tool_used, reason=reason)
        memory.add_tool_usage(tool_name=tool_used, intent=intent, reason=reason)

    def _resolve_subject(self, query: str, resume_data: Dict[str, Any]) -> str:
        """Resolve the current subject from the query or memory."""

        query_lower = query.lower()
        if any(phrase in query_lower for phrase in ["that skill", "this skill", "how strong", "how good is it", "it"]):
            last_subject = memory.get_last_subject()
            if last_subject:
                return last_subject

        for skill in resume_data.get("skills", []):
            if skill.lower() in query_lower:
                return skill

        return ""

    def _handle_skill_query(self, query: str, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle skill-related queries using the SkillMatcher tool."""

        resume_skills = resume_data.get("skills", [])
        query_lower = query.lower()
        self._log_internal_decision("SKILL", "SkillMatcher", "Skill-related query routed to skill tool")

        if not resume_skills:
            return {
                "answer": "No skills mentioned in resume. Not mentioned in resume.",
                "confidence": 1.0,
                "source": "resume",
                "missing_data": ["Skills section"],
            }

        generic_skill_question = any(
            phrase in query_lower
            for phrase in [
                "what skills",
                "which skills",
                "list skills",
                "skills does",
                "skills have",
                "all skills",
                "technical skills",
                "strongest skills",
                "best skills",
                "top skills",
                "key skills",
                "core skills",
                "most relevant skills",
                "main skills",
                "highlight skills",
            ]
        )

        if generic_skill_question:
            return self._handle_skill_summary_query(query, resume_skills)

        match_result = self.skill_matcher.run(resume_skills, query)

        if match_result["found"]:
            found_skills = match_result["skills"]
            skill_names = [skill["skill"] for skill in found_skills]
            if skill_names:
                memory.set_last_subject(skill_names[0])

            return {
                "answer": f"Yes, the candidate has the following skill(s): {', '.join(skill_names)}",
                "confidence": match_result["confidence"],
                "source": "resume",
                "missing_data": [],
            }

        available = ", ".join(resume_skills[:5])
        answer = f"The queried skill(s) are not mentioned in the resume. Available skills: {available}"
        if len(resume_skills) > 5:
            answer += f" ... and {len(resume_skills) - 5} more"

        return {
            "answer": answer,
            "confidence": 0.9,
            "source": "resume",
            "missing_data": ["Specific skill not found"],
        }

    def _handle_skill_summary_query(self, query: str, resume_skills: list) -> Dict[str, Any]:
        """Return a ranked summary for queries asking for strongest/top/key skills."""

        if not resume_skills:
            return {
                "answer": "No skills mentioned in resume.",
                "confidence": 1.0,
                "source": "resume",
                "missing_data": ["Skills section"],
            }

        categorized = self.skill_matcher.get_all_skills(resume_skills)
        categories = categorized.get("categories", {})

        strongest = []
        for bucket in ["programming", "frameworks", "tools", "soft_skills", "other"]:
            for skill in categories.get(bucket, []):
                if skill not in strongest:
                    strongest.append(skill)

        # If nothing was categorized, fall back to the original order.
        if not strongest:
            strongest = resume_skills[:]

        top_skills = strongest[:5]

        parts = ["Key skills from the resume:"]
        parts.append(f"- Top skills: {', '.join(top_skills)}")

        if categories.get("programming"):
            parts.append(f"- Programming: {', '.join(categories['programming'][:4])}")
        if categories.get("frameworks"):
            parts.append(f"- Frameworks: {', '.join(categories['frameworks'][:4])}")
        if categories.get("tools"):
            parts.append(f"- Tools/Cloud: {', '.join(categories['tools'][:4])}")
        if categories.get("soft_skills"):
            parts.append(f"- Soft skills: {', '.join(categories['soft_skills'][:4])}")

        if top_skills:
            memory.set_last_subject(top_skills[0])

        return {
            "answer": "\n".join(parts),
            "confidence": 1.0,
            "source": "resume",
            "missing_data": [],
        }

    def _handle_evaluate_query(self, query: str, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle evaluation queries using CandidateScorer tool."""

        scoring_result = self.candidate_scorer.run(resume_data)
        self._log_internal_decision("EVALUATE", "CandidateScorer", "Candidate evaluation requested")

        answer = (
            "Candidate Evaluation:\n"
            f"Overall Score: {scoring_result['overall']}/10 ({scoring_result['rating']})\n"
            f"Technical Skills: {scoring_result['technical_score']}/10\n"
            f"Experience: {scoring_result['experience_score']}/10\n"
            f"Education: {scoring_result['education_score']}/10\n"
            f"Resume Completeness: {scoring_result['completeness_score']}/10\n"
            f"Skills: {scoring_result['scores']['technical_skills']['count']} | "
            f"Experience: {scoring_result['scores']['experience']['count']} | "
            f"Education: {scoring_result['scores']['education']['count']}"
        )

        return {
            "answer": answer,
            "confidence": 0.95,
            "source": "resume",
            "missing_data": [],
        }

    def _handle_completeness_query(self, query: str, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resume quality and completeness queries."""

        result = self.resume_completeness.run(resume_data)
        self._log_internal_decision("COMPLETENESS", "ResumeCompletenessTool", "Resume quality analysis requested")

        return {
            "answer": result["answer"],
            "confidence": result["confidence"],
            "source": result["source"],
            "missing_data": result["missing_data"],
        }

    def _handle_summary_query(self, query: str, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle summary queries."""

        name = resume_data.get("name", "Unknown")
        skills = resume_data.get("skills", [])
        experience = resume_data.get("experience", [])
        education = resume_data.get("education", [])

        self._log_internal_decision("SUMMARY", "ResumeParser", "Summary query routed to resume parser output")

        missing_data = []
        if not name:
            missing_data.append("Name")
        if not skills:
            missing_data.append("Skills")
        if not experience:
            missing_data.append("Experience")
        if not education:
            missing_data.append("Education")

        answer = f"Resume Summary for {name if name else 'Candidate'}:\n"

        if skills:
            answer += f"Skills ({len(skills)}): {', '.join(skills[:3])}"
            if len(skills) > 3:
                answer += f" ... and {len(skills) - 3} more\n"
            else:
                answer += "\n"
        else:
            answer += "Skills: Not mentioned in resume\n"

        if experience:
            answer += f"Experience: {len(experience)} position(s) listed\n"
        else:
            answer += "Experience: Not mentioned in resume\n"

        if education:
            answer += f"Education: {len(education)} entries\n"
        else:
            answer += "Education: Not mentioned in resume\n"

        return {
            "answer": answer,
            "confidence": 0.95,
            "source": "resume",
            "missing_data": missing_data,
        }

    def _handle_general_query(
        self,
        query: str,
        resume_data: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle general queries using the Gemini model or a deterministic fallback."""

        follow_up_subject = self._resolve_subject(query, resume_data)
        query_lower = query.lower()
        is_follow_up = any(phrase in query_lower for phrase in ["that skill", "this skill", "how strong", "how good is it", "it"])

        if is_follow_up and follow_up_subject:
            self._log_internal_decision("GENERAL", "SkillMatcher", f"Follow-up question resolved to {follow_up_subject}")
            resume_skills = [skill.lower() for skill in resume_data.get("skills", [])]
            if follow_up_subject.lower() in resume_skills:
                memory.set_last_subject(follow_up_subject)
                return {
                    "answer": f"{follow_up_subject} is mentioned in the resume. The resume does not quantify proficiency, so the safest answer is that it is listed but not measured.",
                    "confidence": 0.9,
                    "source": "resume",
                    "missing_data": ["Skill proficiency level"],
                }

            return {
                "answer": f"{follow_up_subject} is not mentioned in the resume.",
                "confidence": 1.0,
                "source": "resume",
                "missing_data": [follow_up_subject],
            }

        if self.client is None:
            note = "No LLM key configured - set GEMINI_API_KEY or GROQ_API_KEY in .env"
            self._log_internal_decision("GENERAL", "FallbackComposer", note)
            chat_history = context.get("history", [])
            return self._fallback_general_response(query, resume_data, chat_history)

        resume_context = self._build_resume_context(resume_data)
        chat_history = context.get("history", [])
        # Route to the configured LLM provider (GROQ preferred)
        if self.client_source == "groq":
            self._log_internal_decision("GENERAL", "groq", "General query routed to GROQ provider")
            prompt = self._build_prompt(query, resume_context, chat_history)
            try:
                response_text = self._call_groq_model(prompt)
                memory.add_tool_usage(tool_name="GROQAgent", intent="GENERAL", reason="General query answered by GROQ")
                return self._parse_agent_response(response_text, resume_data)
            except Exception as e:
                self._log_internal_decision("GENERAL", "groq", f"GROQ call failed: {str(e)}")
                # Fall back to deterministic response when GROQ fails
                return self._fallback_general_response(query, resume_data, chat_history)

        self._log_internal_decision("GENERAL", self.model_name, "General query routed to Gemini")
        prompt = self._build_prompt(query, resume_context, chat_history)

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=1024,
                    temperature=0.2,
                ),
            )

            response_text = getattr(response, "text", None) or ""
            memory.add_tool_usage(tool_name="GeminiAgent", intent="GENERAL", reason="General query answered by Gemini")
            return self._parse_agent_response(response_text, resume_data)

        except json.JSONDecodeError:
            return {
                "answer": response_text,
                "confidence": 0.7,
                "source": "inference",
                "missing_data": [],
            }
        except Exception as e:
            error_msg = str(e)
            # If it's a quota/rate limit error, fall back to deterministic response
            if "429" in error_msg or "quota" in error_msg.lower() or "RESOURCE_EXHAUSTED" in error_msg:
                chat_history = context.get("history", [])
                return self._fallback_general_response(query, resume_data, chat_history)
            
            return {
                "answer": f"Error querying LLM: {error_msg}",
                "confidence": 0.0,
                "source": "inference",
                "missing_data": ["LLM error"],
            }

    def _fallback_general_response(self, query: str, resume_data: Dict[str, Any], chat_history: list = None) -> Dict[str, Any]:
        """Provide a deterministic fallback when no LLM client is configured."""

        if chat_history is None:
            chat_history = []

        summary_parts = []
        missing_data = []

        # Add context awareness from conversation history
        if chat_history and len(chat_history) > 1:
            summary_parts.append("=== CONVERSATION CONTEXT ===")
            for msg in chat_history[-3:]:  # Show last 3 messages for context
                role = "You" if msg.get("role") == "user" else "Assistant"
                content = msg.get("content", "")[:60]  # Truncate long responses
                summary_parts.append(f"{role}: {content}...")
            summary_parts.append("")

        # Add current query context
        query_lower = query.lower()
        if any(word in query_lower for word in ["experience", "work", "job", "career"]):
            experience = resume_data.get("experience", [])
            if experience:
                summary_parts.append(f"Experience: {len(experience)} position(s) found")
                for i, exp in enumerate(experience[:2], 1):
                    summary_parts.append(f"  {i}. {exp.get('entry', '')[:80]}")
            else:
                summary_parts.append("Experience: Not mentioned in resume")
                missing_data.append("Experience")
        
        elif any(word in query_lower for word in ["education", "degree", "studied", "university", "college"]):
            education = resume_data.get("education", [])
            if education:
                summary_parts.append(f"Education: {len(education)} entry(ies) found")
                for i, edu in enumerate(education[:2], 1):
                    summary_parts.append(f"  {i}. {edu.get('entry', '')[:80]}")
            else:
                summary_parts.append("Education: Not mentioned in resume")
                missing_data.append("Education")
        
        elif any(word in query_lower for word in ["skill", "expertise", "proficient", "know"]):
            skills = resume_data.get("skills", [])
            if skills:
                summary_parts.append(f"Skills: {', '.join(skills[:10])}")
            else:
                summary_parts.append("Skills: Not mentioned in resume")
                missing_data.append("Skills")
        
        else:
            # Default comprehensive response
            name = resume_data.get("name", "")
            if name:
                summary_parts.append(f"Candidate: {name}")
            else:
                missing_data.append("Name")

            skills = resume_data.get("skills", [])
            if skills:
                summary_parts.append(f"Skills: {', '.join(skills[:5])}")
            else:
                summary_parts.append("Skills: Not mentioned in resume")
                missing_data.append("Skills")

            experience = resume_data.get("experience", [])
            if experience:
                summary_parts.append(f"Experience entries: {len(experience)}")
            else:
                summary_parts.append("Experience: Not mentioned in resume")
                missing_data.append("Experience")

            education = resume_data.get("education", [])
            if education:
                summary_parts.append(f"Education entries: {len(education)}")
            else:
                summary_parts.append("Education: Not mentioned in resume")
                missing_data.append("Education")

        # Add note about limited mode
        summary_parts.append("\n⚠️ NOTE: Gemini AI is disabled. Set GEMINI_API_KEY in .env for intelligent responses.")

        return {
            "answer": "\n".join(summary_parts),
            "confidence": 0.6 if missing_data else 0.75,
            "source": "resume" if not missing_data else "inference",
            "missing_data": missing_data,
        }

    def _build_resume_context(self, resume_data: Dict[str, Any]) -> str:
        """Build formatted resume context for LLM."""

        context = "=== RESUME DATA ===\n"

        if resume_data.get("name"):
            context += f"Name: {resume_data['name']}\n"

        if resume_data.get("skills"):
            context += f"Skills: {', '.join(resume_data['skills'])}\n"

        if resume_data.get("experience"):
            context += f"Experience ({len(resume_data['experience'])} entries):\n"
            for exp in resume_data["experience"][:3]:
                context += f"  - {exp.get('entry', 'Not specified')}\n"

        if resume_data.get("education"):
            context += f"Education ({len(resume_data['education'])} entries):\n"
            for edu in resume_data["education"][:3]:
                context += f"  - {edu.get('entry', 'Not specified')}\n"

        return context

    def _build_prompt(self, query: str, resume_context: str, chat_history: list) -> str:
        """Build a comprehensive prompt for Gemini with full resume context and conversation history."""

        # Include full conversation history (not just last 5)
        history_lines = []
        if chat_history:
            history_lines.append("=== CONVERSATION HISTORY ===")
            for msg in chat_history:
                if msg.get("role") in ["user", "assistant"]:
                    role = "USER" if msg.get("role") == "user" else "ASSISTANT"
                    content = msg.get('content', '')
                    if content:
                        history_lines.append(f"\n{role}:\n{content}")
        
        history_block = "\n".join(history_lines) if history_lines else "=== NO PREVIOUS CONVERSATION ==="

        return (
            f"{resume_context}\n\n"
            f"{history_block}\n\n"
            f"=== NEW USER QUERY ===\n{query}\n\n"
            "Based on the resume, conversation history, and the new query above,\n"
            "provide a helpful response. Return ONLY valid JSON in this exact format:\n"
            "{\n"
            '  "answer": "your detailed response here",\n'
            '  "confidence": 0.0,\n'
            '  "source": "resume" or "inference",\n'
            '  "missing_data": []\n'
            "}\n\n"
            "Rules:\n"
            "1. Use conversation history to provide context-aware responses\n"
            "2. Never fabricate information not in the resume\n"
            "3. If information is missing, state 'Not mentioned in resume'\n"
            "4. Confidence should be 1.0 for direct resume facts, lower for inferences"
        )

    def _parse_agent_response(self, response_text: str, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate agent response."""

        try:
            json_str = response_text

            if "```" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                if start != -1 and end > start:
                    json_str = response_text[start:end]

            parsed = json.loads(json_str)

            if "answer" not in parsed:
                parsed["answer"] = response_text

            if "confidence" not in parsed:
                parsed["confidence"] = 0.5
            elif not isinstance(parsed["confidence"], (int, float)):
                parsed["confidence"] = 0.5
            else:
                parsed["confidence"] = min(1.0, max(0.0, parsed["confidence"]))

            if "source" not in parsed:
                parsed["source"] = "inference"
            elif parsed["source"] not in ["resume", "inference"]:
                parsed["source"] = "inference"

            if "missing_data" not in parsed:
                parsed["missing_data"] = []
            elif not isinstance(parsed["missing_data"], list):
                parsed["missing_data"] = []

            return parsed

        except json.JSONDecodeError:
            return {
                "answer": response_text,
                "confidence": 0.6,
                "source": "inference",
                "missing_data": [],
            }

    def _call_groq_model(self, prompt: str) -> str:
        """Minimal GROQ HTTP client wrapper. Expects `GROQ_API_URL` and `GROQ_API_KEY` in env.

        This is a best-effort implementation; adjust payload/response parsing per your GROQ API.
        """
        if not self.groq_key:
            raise RuntimeError("GROQ_API_KEY not configured")

        # Prefer the Responses API which accepts free-form `input` and returns
        # a structured `output` array. Default endpoint follows Groq docs.
        groq_url = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/responses")
        groq_model = os.getenv("GROQ_MODEL", os.getenv("GROQ_DEFAULT_MODEL", "llama-3.3-70b-versatile"))
        max_output_tokens = int(os.getenv("MAX_TOKENS", "1024"))
        temperature = float(os.getenv("GROQ_TEMPERATURE", "0.2"))

        headers = {"Authorization": f"Bearer {self.groq_key}", "Content-Type": "application/json"}
        # Build payload for Responses API
        payload = {
            "model": groq_model,
            "input": prompt,
            "max_output_tokens": max_output_tokens,
            "temperature": temperature,
        }

        if HAS_REQUESTS:
            resp = requests.post(groq_url, json=payload, headers=headers, timeout=20)
            resp.raise_for_status()
            data = resp.json()
        else:
            # Fallback to urllib to avoid external dependency
            import urllib.request
            import urllib.error

            data_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(groq_url, data=data_bytes, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    raw = resp.read()
                    try:
                        data = json.loads(raw.decode("utf-8"))
                    except Exception:
                        data = raw.decode("utf-8")
            except urllib.error.HTTPError as e:
                # Provide helpful error text
                raise RuntimeError(f"GROQ HTTP error: {e.code} {e.reason}")

        # Parse documented Responses API shape first
        if isinstance(data, dict):
            # Responses API: `output` -> list -> each item has `content` list -> content items with `type` and `text`
            out = data.get("output") or data.get("outputs") or data.get("choices")
            if isinstance(out, list) and len(out) > 0:
                # Iterate outputs and prefer the first message/content with output_text
                for item in out:
                    if not isinstance(item, dict):
                        continue
                    content = item.get("content")
                    if isinstance(content, list) and len(content) > 0:
                        texts = []
                        for c in content:
                            if isinstance(c, dict) and "text" in c:
                                texts.append(c["text"])
                            elif isinstance(c, dict) and c.get("type") == "output_text" and "text" in c:
                                texts.append(c["text"])
                            else:
                                texts.append(str(c))
                        if texts:
                            return "\n".join(texts)

                # Try choices -> message -> content (chat completions compatibility)
                choices = data.get("choices")
                if isinstance(choices, list) and len(choices) > 0:
                    choice = choices[0]
                    message = choice.get("message") or {}
                    if isinstance(message, dict):
                        # message.content may be a string or dict/list
                        mc = message.get("content")
                        if isinstance(mc, str):
                            return mc
                        if isinstance(mc, dict):
                            return json.dumps(mc)
                        if isinstance(mc, list):
                            # join text fields
                            parts = []
                            for m in mc:
                                if isinstance(m, dict) and "text" in m:
                                    parts.append(m["text"])
                                else:
                                    parts.append(str(m))
                            return "\n".join(parts)

            # Fallback: if top-level `text` exists
            if "text" in data and isinstance(data["text"], str):
                return data["text"]

            # Last resort: return pretty JSON
            return json.dumps(data)

        return str(data)