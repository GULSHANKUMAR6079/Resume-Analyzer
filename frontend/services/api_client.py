import requests
import streamlit as st
from typing import Dict, Optional

import os

def get_backend_url() -> str:
    """Retrieve backend URL dynamically from env or st.secrets."""
    url = os.getenv("BACKEND_URL", "")
    if not url:
        try:
            url = str(st.secrets.get("BACKEND_URL", ""))
        except Exception:
            url = ""
    if not url:
        url = "http://localhost:8000/api/v1"
    
    url = url.rstrip('/')
    if not url.endswith('/api/v1'):
        url = f"{url}/api/v1"
    return url

def get_auth_headers() -> Dict[str, str]:
    headers = {}
    token = st.session_state.get('access_token')
    if token:
        headers['Authorization'] = f"Bearer {token}"
    return headers

def analyze_resume_api(file_bytes: bytes, filename: str, job_description: str = "") -> Dict:
    backend_base = get_backend_url()
    url = f"{backend_base}/analyze-resume"
    files = {
        'resume': (filename, file_bytes, 'application/octet-stream')
    }
    data = {
        'job_description': job_description
    }

    response = None
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
            try:
                detail = response.json().get('detail', 'Validation error')
            except Exception:
                detail = response.text
            raise ValueError(f"Document parsing error: {detail}")
        raise RuntimeError(f"Backend connection error to '{url}': {exc}")

def download_pdf_report_api(analysis_data: Dict) -> Optional[bytes]:
    url = f"{get_backend_url()}/generate-pdf"
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
    url = f"{get_backend_url()}/history"
    try:
        response = requests.get(url, headers=get_auth_headers(), timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception:
        return []

def delete_history_api(analysis_id: str) -> bool:
    url = f"{get_backend_url()}/history/{analysis_id}"
    try:
        response = requests.delete(url, headers=get_auth_headers(), timeout=15)
        return response.status_code == 200
    except Exception:
        return False
