import json
import os
import re
import yaml
from typing import Dict, Any, Optional

def load_config() -> Dict[str, Any]:
    """
    Loads configuration settings from config.yaml if it exists.
    """
    base_dir = os.path.dirname(__file__)
    config_candidates = [
        os.path.join(base_dir, "config.yaml"),
        os.path.join(os.path.dirname(base_dir), "config.yaml")
    ]
    for config_path in config_candidates:
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Failed to load config.yaml: {e}")
    return {}

def load_prompt_instructions() -> str:
    """
    Dynamically loads the full 27-rule prompt system instructions from Prompt.py (or Prompt).
    Ensures 100% adherence to all extracted rules, classifications, bullet structures, and ATS matching strategy.
    """
    base_dir = os.path.dirname(__file__)
    file_candidates = [
        os.path.join(base_dir, "Prompt.py"),
        os.path.join(base_dir, "Prompt"),
        os.path.join(os.path.dirname(base_dir), "Prompt.py"),
        os.path.join(os.path.dirname(base_dir), "Prompt")
    ]
    for filepath in file_candidates:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return content
    return "You are an expert ATS Resume Tailoring Bot. Follow strict ATS evidence matching and keyword optimization rules."

class ResumeTailorEngine:
    def __init__(self, api_key: Optional[str] = None, provider: str = "auto"):
        """
        Initialize LLM client with Groq, Google Gemini, or OpenAI API key.
        Autodetects provider if set to 'auto'.
        """
        self.config = load_config()
        
        # Determine provider
        selected_provider = provider if provider != "auto" else self.config.get("provider", "auto")
        
        # Helper to safely retrieve key from Streamlit st.secrets
        def get_st_secret(secret_name: str) -> Optional[str]:
            try:
                import streamlit as st
                if hasattr(st, "secrets") and st.secrets and secret_name in st.secrets:
                    val = st.secrets[secret_name]
                    if isinstance(val, str) and val.strip():
                        return val.strip()
            except Exception:
                pass
            return None

        # Resolve API Key based on provider preference across st.secrets, config.yaml, and os.getenv
        if api_key:
            self.api_key = api_key
        elif selected_provider == "openai":
            self.api_key = (
                get_st_secret("OPENAI_API_KEY") 
                or get_st_secret("openai_api_key") 
                or self.config.get("openai_api_key") 
                or os.getenv("OPENAI_API_KEY") 
                or self.config.get("api_key")
                or get_st_secret("api_key")
            )
        elif selected_provider == "groq":
            self.api_key = (
                get_st_secret("GROQ_API_KEY") 
                or get_st_secret("groq_api_key") 
                or self.config.get("groq_api_key") 
                or os.getenv("GROQ_API_KEY") 
                or self.config.get("api_key")
                or get_st_secret("api_key")
            )
        elif selected_provider == "gemini":
            self.api_key = (
                get_st_secret("GEMINI_API_KEY") 
                or get_st_secret("gemini_api_key") 
                or self.config.get("gemini_api_key") 
                or os.getenv("GEMINI_API_KEY") 
                or self.config.get("api_key")
                or get_st_secret("api_key")
            )
        else:
            self.api_key = (
                get_st_secret("OPENAI_API_KEY")
                or get_st_secret("GROQ_API_KEY")
                or get_st_secret("GEMINI_API_KEY")
                or get_st_secret("openai_api_key")
                or get_st_secret("groq_api_key")
                or get_st_secret("gemini_api_key")
                or get_st_secret("api_key")
                or self.config.get("openai_api_key") 
                or self.config.get("groq_api_key") 
                or self.config.get("api_key") 
                or os.getenv("OPENAI_API_KEY") 
                or os.getenv("GROQ_API_KEY") 
                or os.getenv("GEMINI_API_KEY")
            )
        
        if not self.api_key:
            raise ValueError("API Key is required. Please provide an OpenAI, Groq, or Gemini API Key in Streamlit Cloud Secrets Manager, config.yaml, or .env file.")
        
        # Load full Prompt rules from Prompt.py
        self.base_system_prompt = load_prompt_instructions()

        # Auto-detect provider based on key format if set to auto
        if selected_provider == "auto":
            if self.api_key.startswith("sk-"):
                self.provider = "openai"
            elif self.api_key.startswith("gsk_"):
                self.provider = "groq"
            else:
                self.provider = "gemini"
        else:
            self.provider = selected_provider.lower()
            # If key format clearly indicates another provider, override to prevent mismatch errors
            if self.api_key.startswith("sk-"):
                self.provider = "openai"
            elif self.api_key.startswith("gsk_"):
                self.provider = "groq"

        # Initialize appropriate SDK client
        if self.provider == "gemini":
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
        elif self.provider == "groq":
            import openai
            base_url = self.config.get("groq_base_url") or "https://api.groq.com/openai/v1"
            self.client = openai.OpenAI(api_key=self.api_key, base_url=base_url)
        elif self.provider == "openai":
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def analyze_match(self, jd_text: str, resume_text: str, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Extract keywords, calculate ATS score, and perform gap analysis adhering strictly to Prompt.py rules."""
        if not model_name or model_name == "Auto-Select":
            model_name = self.config.get("model") or ("llama-3.3-70b-versatile" if self.provider == "groq" else ("gpt-4o-mini" if self.provider == "openai" else "gemini-2.5-flash"))

        system_instruction = f"""
{self.base_system_prompt}

============================================================
JSON OUTPUT FORMAT SPECIFICATION FOR ANALYSIS
============================================================
Analyze the provided Job Description (JD) and Candidate Resume adhering strictly to the 27 rules above.
Return a JSON object with this exact structure:
{{
  "job_title": "string",
  "company_name": "string (or Unknown)",
  "overall_ats_score": integer (0 to 100),
  "summary_analysis": "string overview of match quality",
  "keywords": [
    {{
      "keyword": "exact term from JD",
      "category": "Technology | Software | Methodology | Certification | Domain | Tool | Project Management",
      "priority": "P1 | P2 | P3 | P4 | P5",
      "status": "SUPPORTED | PARTIALLY_SUPPORTED | UNSUPPORTED",
      "candidate_evidence": "string snippet from resume or None",
      "recommendation": "string guidance on section placement"
    }}
  ],
  "section_scores": {{
    "summary": integer (0-100),
    "skills": integer (0-100),
    "experience": integer (0-100)
  }},
  "key_strengths": ["string"],
  "critical_gaps": ["string"],
  "actionable_recommendations": ["string"]
}}
"""
        user_prompt = f"JOB DESCRIPTION:\n{jd_text}\n\nCANDIDATE RESUME:\n{resume_text}"

        if self.provider == "gemini":
            from google.genai import types
            gemini_model = model_name if "gemini" in model_name else "gemini-2.5-flash"
            response = self.client.models.generate_content(
                model=gemini_model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.2,
                )
            )
            raw_text = response.text
        else:
            # Works for both Groq and OpenAI clients
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            raw_text = response.choices[0].message.content

        return self._parse_json(raw_text)

    def generate_tailored_resume(
        self, 
        jd_text: str, 
        resume_text: str, 
        mode: str = "Standard Optimization",
        model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates the fully tailored ATS-optimized resume in Markdown format,
        strictly following all 27 prompt rules from Prompt.py.
        """
        if not model_name or model_name == "Auto-Select":
            model_name = self.config.get("model") or ("llama-3.3-70b-versatile" if self.provider == "groq" else ("gpt-4o-mini" if self.provider == "openai" else "gemini-2.5-flash"))

        system_instruction = f"""
{self.base_system_prompt}

============================================================
STRICT RESUME FORMATTING & EDITING RULES
============================================================
1. DO NOT REWRITE THE WHOLE RESUME: Preserve the candidate's core structure and layout.
2. DO NOT TOUCH ANY SECTION HEADINGS: Keep all section headers (e.g. PROFESSIONAL SUMMARY, TECHNICAL SKILLS, PROFESSIONAL EXPERIENCE, EDUCATION, CERTIFICATIONS) 100% UNTOUCHED.
3. SPECIFIC SECTION UPDATE SCOPE:
   a. PROFESSIONAL SUMMARY: Update only the paragraph text inside the professional summary section.
   b. TECHNICAL SKILLS: Update only the skill lists. Do NOT touch or modify bolded side headings (e.g. **Project Management:**, **Tools:**, **Methodologies:**).
   c. EXPERIENCE SECTION: Update ONLY experience bullet points. Do NOT touch company names, job titles, or date formatting.
   d. GENERAL: Change only what is needed for ATS keyword alignment without touching any section headings.

============================================================
JSON OUTPUT FORMAT SPECIFICATION FOR TAILORED RESUME
============================================================
Analyze the Job Description (JD) and Candidate Resume according to all ATS tailoring rules above.
Generate targeted bullet point improvements to maximize ATS keyword alignment while maintaining factual credibility and candidate experience.

Return a JSON object with two fields:
{{
  "tailored_resume": "The ATS-tailored resume text.",
  "bullet_improvements": [
     {{
       "original": "exact original bullet text from candidate resume",
       "tailored": "new optimized bullet text incorporating relevant JD keywords",
       "added_keywords": ["keyword1", "keyword2"],
       "reason": "why this change boosts ATS match score"
     }}
  ]
}}
"""
        user_prompt = f"Tailoring Strategy: {mode}\n\nJOB DESCRIPTION:\n{jd_text}\n\nCANDIDATE RESUME:\n{resume_text}"

        if self.provider == "gemini":
            from google.genai import types
            gemini_model = model_name if "gemini" in model_name else "gemini-2.5-flash"
            response = self.client.models.generate_content(
                model=gemini_model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.1,
                )
            )
            raw_text = response.text
        else:
            # Works for both Groq and OpenAI clients
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            raw_text = response.choices[0].message.content

        parsed_result = self._parse_json(raw_text)

        # Guarantee 100% format preservation by applying line replacements directly onto original resume
        bullet_improvements = parsed_result.get("bullet_improvements", [])
        if bullet_improvements and resume_text:
            format_preserved = apply_format_preserving_tailoring(resume_text, bullet_improvements)
            if format_preserved and len(format_preserved.strip()) > 50:
                parsed_result["tailored_resume"] = format_preserved

        return parsed_result

    def _parse_json(self, raw_text: str) -> Dict[str, Any]:
        """Safely clean markdown formatting and parse JSON response."""
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return json.loads(cleaned.strip())

def normalize_text_for_matching(text: str) -> str:
    """Strips markdown syntax, punctuation, bullet characters, and whitespace for line matching."""
    return re.sub(r"[^a-zA-Z0-9]", "", text).lower()

BULLET_CHAR_REGEX = re.compile(r"^[\s\t]*([•\-*o▪■‣⁃–—\u2022\u25aa\u25a0\u2023\u2043\u2013\u2014\uf0a7\uf0b7\uf0a8]|\d+[\.\)])\s*")

def apply_format_preserving_tailoring(original_resume: str, bullet_improvements: list) -> str:
    """
    Applies tailored line updates directly onto the original resume text,
    preserving 100% of original formatting, section titles, headers, line breaks, bullet symbols, and section gaps.
    """
    if not original_resume or not bullet_improvements:
        return original_resume

    result_lines = original_resume.splitlines(keepends=True)
    
    for item in bullet_improvements:
        if not isinstance(item, dict):
            continue
        orig = item.get("original", "").strip()
        tail = item.get("tailored", "").strip()
        if not orig or not tail or orig == tail:
            continue
            
        norm_orig = normalize_text_for_matching(orig)
        if not norm_orig:
            continue
            
        clean_tail_body = BULLET_CHAR_REGEX.sub("", tail).strip()
        if not clean_tail_body:
            clean_tail_body = tail
            
        replaced = False
        
        for i, line in enumerate(result_lines):
            stripped_line = line.strip()
            if not stripped_line:
                continue
                
            norm_line = normalize_text_for_matching(stripped_line)
            
            # Check if line matches target original bullet (exact or high similarity)
            if norm_orig == norm_line or (len(norm_orig) > 15 and norm_orig in norm_line) or (len(norm_line) > 15 and norm_line in norm_orig):
                # Preserve exact leading whitespace of original line
                prefix_len = len(line) - len(line.lstrip())
                indent = line[:prefix_len]
                
                # Detect original line's bullet character prefix (e.g., "• ", "- ", "* ")
                bullet_prefix = ""
                bullet_match = BULLET_CHAR_REGEX.match(stripped_line)
                if bullet_match:
                    bullet_prefix = bullet_match.group(0)
                elif stripped_line.startswith("# "):
                    bullet_prefix = "# "
                elif stripped_line.startswith("## "):
                    bullet_prefix = "## "
                elif stripped_line.startswith("### "):
                    bullet_prefix = "### "
                elif re.match(r"^^[•\-*o▪■]", orig.strip()):
                    bullet_prefix = "• "

                newline_char = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else "")
                
                # Reconstruct original line preserving exact indent, bullet character, and trailing newline
                result_lines[i] = f"{indent}{bullet_prefix}{clean_tail_body}{newline_char}"
                replaced = True
                break
                
    return "".join(result_lines)
