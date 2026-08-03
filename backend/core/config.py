import os
from pathlib import Path

# Load .env from project root explicitly
try:
    from dotenv import load_dotenv
    _ENV_PATH = Path(__file__).resolve().parents[2] / '.env'
    load_dotenv(_ENV_PATH)
except ImportError:
    pass

# API Metadata
APP_TITLE = 'ATS RESUME ANALYZER API'
APP_VERSION = '2.1.0'
APP_DESCRIPTION = 'Ultra-fast enterprise-grade ATS resume analysis engine using NLP + ML'

# Allowed CORS Origins
ALLOWED_ORIGINS = [
    'https://appapppy-ktwxupi73vqhjzweksze9d.streamlit.app/',
    'http://localhost:8501',
    'http://127.0.0.1:8501',
    'http://localhost:3000',
    '*',
]

# File Size & Extension Constraints
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

SUPPORTED_MIME_TYPES = {
    'application/pdf': 'pdf',
    'application/msword': 'doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
}

SUPPORTED_EXTENSIONS = {'.pdf', '.doc', '.docx'}

# NLP & ML Models
SPACY_MODEL_PRIMARY = os.getenv("SPACY_MODEL_PRIMARY", "en_core_web_md")
SPACY_MODEL_SECONDARY = os.getenv("SPACY_MODEL_SECONDARY", "en_core_web_sm")
SENTENCE_TRANSFORMER_MODEL = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")

# Score Component Maximums
SCORE_WEIGHTS = {
    "formatting": 20.0,
    "keywords": 25.0,
    "content": 25.0,
    "skill_validation": 15.0,
    "ats_compatibility": 15.0,
}

JD_KEYWORD_WEIGHT = 0.6
JD_SEMANTIC_WEIGHT = 0.4

# Credentials & Service Keys
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', '')
SUPABASE_JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET', '')
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
