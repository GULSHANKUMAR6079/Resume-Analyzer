import os
import sys
import streamlit as st

# Ensure the frontend/ dir itself is on sys.path so sibling packages
# (views/, services/) are importable without the 'frontend.' prefix.
_FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))
if _FRONTEND_DIR not in sys.path:
    sys.path.insert(0, _FRONTEND_DIR)

st.set_page_config(
    page_title="ATS Resume Analyzer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS Stylesheet
css_path = os.path.join(os.path.dirname(__file__), "assets", "styles.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
for key, default in [
    ('access_token',  None),
    ('refresh_token', None),
    ('user_id',       'anon_user'),
    ('user_email',    None),
    ('auth_error',    None),
    ('auth_info',     None),
    ('active_view',   'Home'),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------------------------------------------------------------------
# Google OAuth PKCE callback — exchange ?code= for a real session
# ---------------------------------------------------------------------------
if not st.session_state.access_token and "code" in st.query_params:
    from services.supabase_client import exchange_code_for_session
    result = exchange_code_for_session(st.query_params["code"])
    st.query_params.clear()          # clear ?code= so a refresh doesn't re-exchange
    if "error" in result:
        st.session_state.auth_error = f"Google sign-in failed: {result['error']}"
    else:
        st.session_state.access_token  = result["access_token"]
        st.session_state.refresh_token = result["refresh_token"]
        st.session_state.user_id       = result["user_id"]
        st.session_state.user_email    = result["email"]
        st.rerun()

# ---------------------------------------------------------------------------
# Sidebar — Navigation + Auth
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
        <div class="sidebar-brand">
            <div class="sidebar-brand-mark">A</div>
            <div>
                <div class="sidebar-brand-text">ATS Analyzer</div>
                <div class="sidebar-brand-sub">Resume Intelligence</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<div class='divider' style='margin:0 0 14px 0;'></div>", unsafe_allow_html=True)

    st.markdown("<span class='sidebar-heading'>Navigation</span>", unsafe_allow_html=True)

    _nav_values = ["Home", "ATS Scorer", "History", "Resources"]
    nav_option = st.radio(
        "Navigation",
        _nav_values,
        index=_nav_values.index(st.session_state['active_view']),
        label_visibility="collapsed"
    )
    st.session_state['active_view'] = nav_option

    st.markdown("<div class='divider' style='margin:18px 0 14px 0;'></div>", unsafe_allow_html=True)
    st.markdown("<span class='sidebar-heading'>Account</span>", unsafe_allow_html=True)

    from services.supabase_client import (
        sign_in_with_password,
        sign_up_with_password,
        google_oauth_url,
        sign_out,
    )

    if st.session_state.access_token:
        # ── Signed-in state ──────────────────────────────────────────────
        # UI CHANGE: Enterprise account card layout with clean typography
        st.markdown(f"""
            <div class="sidebar-account-card">
                <div style="font-size:11px; color:#9CA3AF; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:2px;">Signed in as</div>
                <div style="font-size:13.5px; color:#111827; font-weight:600;">{st.session_state.user_email}</div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("Sign out", use_container_width=True):
            sign_out()
            for k in ("access_token", "refresh_token", "user_email"):
                st.session_state[k] = None
            st.session_state['user_id'] = 'anon_user'
            st.rerun()

    else:
        # ── Signed-out state ─────────────────────────────────────────────
        if st.session_state.auth_error:
            st.error(st.session_state.auth_error)
            st.session_state.auth_error = None
        if st.session_state.auth_info:
            st.info(st.session_state.auth_info)
            st.session_state.auth_info = None

        tab_in, tab_up = st.tabs(["Sign in", "Sign up"])

        with tab_in:
            with st.form("signin_form", clear_on_submit=False):
                email    = st.text_input("Email",    key="signin_email")
                password = st.text_input("Password", type="password", key="signin_pw")
                submitted = st.form_submit_button("Sign in", use_container_width=True)
            if submitted:
                result = sign_in_with_password(email, password)
                if "error" in result:
                    st.session_state.auth_error = result["error"]
                else:
                    st.session_state.access_token  = result["access_token"]
                    st.session_state.refresh_token = result["refresh_token"]
                    st.session_state.user_id       = result["user_id"]
                    st.session_state.user_email    = result["email"]
                st.rerun()

        with tab_up:
            with st.form("signup_form", clear_on_submit=False):
                email_up    = st.text_input("Email",                  key="signup_email")
                password_up = st.text_input("Password (min 6 chars)", type="password", key="signup_pw")
                submitted_up = st.form_submit_button("Create account", use_container_width=True)
            if submitted_up:
                result = sign_up_with_password(email_up, password_up)
                if "error" in result:
                    st.session_state.auth_error = result["error"]
                elif result.get("pending_confirmation"):
                    st.session_state.auth_info = (
                        f"Check your inbox — confirmation email sent to {result['email']}."
                    )
                else:
                    st.session_state.access_token  = result["access_token"]
                    st.session_state.refresh_token = result["refresh_token"]
                    st.session_state.user_id       = result["user_id"]
                    st.session_state.user_email    = result["email"]
                st.rerun()

        # UI CHANGE: Subtle muted text separator between login form and OAuth button
        st.markdown(
            "<div style='text-align:center; margin:8px 0; color:#6B7280; font-size:12px;'>or</div>",
            unsafe_allow_html=True
        )

        oauth = google_oauth_url()
        if "error" in oauth:
            st.caption(f"Google sign-in unavailable: {oauth['error']}")
        else:
            st.link_button(
                "Continue with Google",
                url=oauth["url"],
                use_container_width=True,
            )

# ---------------------------------------------------------------------------
# Main Content — render active view
# ---------------------------------------------------------------------------
if st.session_state['active_view'] == 'Home':
    from views.landing import render_landing_view
    render_landing_view()

elif st.session_state['active_view'] == 'ATS Scorer':
    from views.scorer import render_scorer_view
    render_scorer_view()

elif st.session_state['active_view'] == 'History':
    from views.history import render_history_view
    render_history_view()

elif st.session_state['active_view'] == 'Resources':
    from views.resources import render_resources_view
    render_resources_view()
