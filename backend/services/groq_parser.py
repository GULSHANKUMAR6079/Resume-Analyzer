import os
import json
import logging
from typing import Dict, Optional
from groq import AsyncGroq, Groq
from backend.core.config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger('ats_resume_scorer')

_async_client: Optional[AsyncGroq] = None

def get_async_groq_client() -> AsyncGroq:
    global _async_client
    if _async_client is None:
        api_key = os.getenv('GROQ_API_KEY') or GROQ_API_KEY
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
        _async_client = AsyncGroq(api_key=api_key)
    return _async_client

RESUME_SYSTEM_PROMPT = (
    "You are an expert AI resume parser. Extract key structured information from the resume "
    "and return ONLY a valid JSON object matching the required schema. Ensure the key 'json' is understood."
)

RESUME_USER_PROMPT = """Extract the following fields from this resume text and return as a valid JSON object:
{{
  "name": "Full Name",
  "email": "email address or null",
  "phone": "phone number or null",
  "linkedin": "LinkedIn profile URL or null",
  "github": "GitHub profile URL or null",
  "professional_summary": "Full text of the Summary, Profile, About Me, or Objective section. Copy exactly.",
  "skills": ["list", "of", "all", "technical", "and", "soft", "skills"],
  "experience": [
    {{
      "job_title": "Role Title",
      "company": "Company Name",
      "start_date": "Start Date",
      "end_date": "End Date or Present",
      "duration_months": 0,
      "description": "Full bullet point details"
    }}
  ],
  "education": [
    {{
      "degree": "Degree Name",
      "institution": "University / College",
      "year": "Graduation Year"
    }}
  ],
  "certifications": ["List of certifications"],
  "projects": [
    {{
      "title": "Project Title",
      "description": "What was built and results achieved",
      "technologies": ["tech", "used"]
    }}
  ],
  "action_verbs": ["strong action verbs starting bullet points, e.g. Developed, Led, Automated"],
  "keywords": ["important industry terms and technologies for ATS matching"]
}}

Resume Text:
{raw_text}"""

JD_SYSTEM_PROMPT = (
    "You are an expert job description parser. Extract target key requirements "
    "and return ONLY a valid JSON object."
)

JD_USER_PROMPT = """Extract the following fields from this job description and return as a JSON object:
{{
  "job_title": "Target job title",
  "required_skills": ["must-have required skills"],
  "preferred_skills": ["nice-to-have or preferred skills"],
  "experience_required": "years or experience required",
  "education_required": "degree required",
  "key_responsibilities": ["main duties"],
  "keywords": ["critical keywords and domain terms for ATS match"]
}}

Job Description Text:
{raw_text}"""

def _clean_json_response(raw_text: str) -> dict | None:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        first_line_end = cleaned.find("\n")
        if first_line_end != -1:
            cleaned = cleaned[first_line_end + 1:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None

def extract_fallback_resume(raw_text: str) -> Dict:
    """Fast spaCy & regex fallback resume parser if Groq LLM API is unavailable."""
    import re
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', raw_text)
    email = email_match.group(0) if email_match else None
    
    phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', raw_text)
    phone = phone_match.group(0) if phone_match else None

    li = re.search(r'linkedin\.com/in/[\w-]+', raw_text, re.I)
    gh = re.search(r'github\.com/[\w-]+', raw_text, re.I)

    common_skills = [
        "python", "java", "javascript", "typescript", "react", "node", "express",
        "fastapi", "django", "flask", "sql", "postgresql", "mongodb", "aws", "docker",
        "kubernetes", "git", "html", "css", "c++", "c#", "machine learning", "data science",
        "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "rest api", "graphql"
    ]
    t_lower = raw_text.lower()
    found_skills = [s.title() for s in common_skills if s in t_lower]

    return _validate_resume_result({
        "name": raw_text.split('\n')[0].strip() if raw_text else "Candidate",
        "email": email,
        "phone": phone,
        "linkedin": f"https://{li.group(0)}" if li else None,
        "github": f"https://{gh.group(0)}" if gh else None,
        "professional_summary": raw_text[:400],
        "skills": found_skills,
        "experience": [],
        "projects": [],
        "action_verbs": ["Developed", "Built", "Designed", "Managed", "Implemented"],
        "keywords": found_skills,
    })

async def parse_resume_async(raw_text: str) -> Dict:
    api_key = os.getenv('GROQ_API_KEY') or GROQ_API_KEY
    if not api_key or api_key.strip() == "" or "your_groq_api_key" in api_key.lower():
        logger.warning("GROQ_API_KEY not configured. Using spaCy & Regex fallback parser.")
        return extract_fallback_resume(raw_text)

    try:
        client = get_async_groq_client()
        prompt = RESUME_USER_PROMPT.format(raw_text=raw_text[:8000])

        response = await client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {'role': 'system', 'content': RESUME_SYSTEM_PROMPT},
                {'role': 'user', 'content': prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=4096
        )
        content = response.choices[0].message.content.strip()
        parsed = _clean_json_response(content)
        if parsed:
            return _validate_resume_result(parsed)
    except Exception as exc:
        logger.warning(f"Groq LLM parse attempt 1 failed ({exc}). Retrying without response format...")

    try:
        client = get_async_groq_client()
        prompt = RESUME_USER_PROMPT.format(raw_text=raw_text[:8000])
        response = await client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {'role': 'system', 'content': RESUME_SYSTEM_PROMPT},
                {'role': 'user', 'content': prompt}
            ],
            temperature=0.0,
            max_tokens=4096
        )
        parsed = _clean_json_response(response.choices[0].message.content.strip())
        if parsed:
            return _validate_resume_result(parsed)
    except Exception as exc:
        logger.warning(f"Groq LLM parse failed completely ({exc}). Using spaCy & Regex fallback parser.")
    
    return extract_fallback_resume(raw_text)

async def parse_job_description_async(raw_text: str) -> Dict:
    api_key = os.getenv('GROQ_API_KEY') or GROQ_API_KEY
    if not api_key or api_key.strip() == "" or "your_groq_api_key" in api_key.lower():
        logger.warning("GROQ_API_KEY not set. Falling back to basic JD parser.")
        return _validate_jd_result({
            "keywords": [w.strip() for w in raw_text.split() if len(w) > 4][:15]
        })

    try:
        client = get_async_groq_client()
        prompt = JD_USER_PROMPT.format(raw_text=raw_text[:8000])

        response = await client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {'role': 'system', 'content': JD_SYSTEM_PROMPT},
                {'role': 'user', 'content': prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=4096
        )
        content = response.choices[0].message.content.strip()
        parsed = _clean_json_response(content)
        if parsed:
            return _validate_jd_result(parsed)
    except Exception as exc:
        logger.warning(f"Native JSON mode failed for JD: {exc}. Retrying...")

    try:
        client = get_async_groq_client()
        prompt = JD_USER_PROMPT.format(raw_text=raw_text[:8000])
        response = await client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {'role': 'system', 'content': JD_SYSTEM_PROMPT},
                {'role': 'user', 'content': prompt}
            ],
            temperature=0.0,
            max_tokens=2048
        )
        parsed = _clean_json_response(response.choices[0].message.content.strip())
        if parsed:
            return _validate_jd_result(parsed)
    except Exception as exc:
        logger.warning(f"Groq JD parse failed ({exc}).")

    return _validate_jd_result({})

# Sync fallback wrappers for backward compatibility if needed
def parse_resume(raw_text: str) -> Dict:
    import asyncio
    return asyncio.run(parse_resume_async(raw_text))

def parse_job_description(raw_text: str) -> Dict:
    import asyncio
    return asyncio.run(parse_job_description_async(raw_text))

def _validate_resume_result(result: dict) -> dict:
    defaults = {
        "name": "", "email": None, "phone": None, "linkedin": None, "github": None,
        "professional_summary": "", "skills": [], "experience": [], "education": [],
        "certifications": [], "projects": [], "action_verbs": [], "keywords": []
    }
    for k, v in defaults.items():
        if k not in result or result[k] is None:
            result[k] = v
        if isinstance(v, list) and not isinstance(result[k], list):
            result[k] = v

    for exp in result.get("experience", []):
        if isinstance(exp, dict):
            exp.setdefault("job_title", "")
            exp.setdefault("company", "")
            exp.setdefault("start_date", "")
            exp.setdefault("end_date", "")
            exp.setdefault("duration_months", 0)
            exp.setdefault("description", "")

    for proj in result.get("projects", []):
        if isinstance(proj, dict):
            proj.setdefault("title", "")
            proj.setdefault("description", "")
            proj.setdefault("technologies", [])

    return result

def _validate_jd_result(result: dict) -> dict:
    defaults = {
        "job_title": "", "required_skills": [], "preferred_skills": [],
        "experience_required": "", "education_required": "",
        "key_responsibilities": [], "keywords": []
    }
    for k, v in defaults.items():
        if k not in result or result[k] is None:
            result[k] = v
        if isinstance(v, list) and not isinstance(result[k], list):
            result[k] = v
    return result
