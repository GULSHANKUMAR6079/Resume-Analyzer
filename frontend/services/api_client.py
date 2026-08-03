import requests
import streamlit as st
from typing import Dict, Optional

import os

# Dynamic BACKEND_URL with environment variable and Streamlit secrets fallback
BACKEND_URL = os.getenv("BACKEND_URL")
if not BACKEND_URL:
    try:
        BACKEND_URL = st.secrets.get("BACKEND_URL")
    except Exception:
        BACKEND_URL = None

if not BACKEND_URL:
    BACKEND_URL = "http://localhost:8000/api/v1"

# Ensure BACKEND_URL ends with /api/v1 and has no trailing slash
BACKEND_URL = BACKEND_URL.rstrip('/')
if not BACKEND_URL.endswith('/api/v1'):
    BACKEND_URL = f"{BACKEND_URL}/api/v1"

def get_auth_headers() -> Dict[str, str]:
    headers = {}
    token = st.session_state.get('access_token')
    if token:
        headers['Authorization'] = f"Bearer {token}"
    return headers

def analyze_resume_api(file_bytes: bytes, filename: str, job_description: str = "") -> Dict:
    url = f"{BACKEND_URL}/analyze-resume"
    files = {
        'resume': (filename, file_bytes, 'application/octet-stream')
    }
    data = {
        'job_description': job_description
    }

    try:
        response = requests.post(
            url,
            files=files,
            data=data,
            headers=get_auth_headers(),
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as exc:
        if response is not None and response.status_code == 422:
            raise ValueError(f"Document parsing error: {response.json().get('detail')}")
        raise RuntimeError(f"Backend API error: {exc}")

def download_pdf_report_api(analysis_data: Dict) -> Optional[bytes]:
    url = f"{BACKEND_URL}/generate-pdf"
    try:
        response = requests.post(
            url,
            json=analysis_data,
            headers=get_auth_headers(),
            timeout=30
        )
        response.raise_for_status()
        return response.content
    except Exception:
        return None

def fetch_history_api() -> list:
    url = f"{BACKEND_URL}/history"
    try:
        response = requests.get(url, headers=get_auth_headers(), timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception:
        return []

def delete_history_api(analysis_id: str) -> bool:
    url = f"{BACKEND_URL}/history/{analysis_id}"
    try:
        response = requests.delete(url, headers=get_auth_headers(), timeout=15)
        return response.status_code == 200
    except Exception:
        return False
