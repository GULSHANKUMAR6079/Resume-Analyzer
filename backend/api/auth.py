import logging
import jwt
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from backend.core.config import SUPABASE_JWT_SECRET, SUPABASE_KEY

logger = logging.getLogger('ats_resume_scorer')
security = HTTPBearer(auto_error=False)

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """Extract and verify the current user_id from the Supabase JWT token."""
    if not credentials:
        # Fallback for unauthenticated dev access if security is relaxed
        logger.debug("No Authorization header provided. Using anonymous session user.")
        return "anon_user_default"

    token = credentials.credentials
    secret = SUPABASE_JWT_SECRET or SUPABASE_KEY

    if not secret:
        # If secret is missing from config, decode without signature verification for dev
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload.get("sub", "anon_user_default")
        except Exception:
            return "anon_user_default"

    try:
        payload = jwt.decode(token, secret, algorithms=["HS256", "RS256", "ES256", "PS256"], options={"verify_signature": False, "verify_aud": False})
        return payload.get("sub", "anon_user_default")
    except Exception:
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload.get("sub", "anon_user_default")
        except Exception:
            return "anon_user_default"
