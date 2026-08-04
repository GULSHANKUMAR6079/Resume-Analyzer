import streamlit as st
from services.api_client import analyze_resume_api, fetch_history_api

def render_landing_view():
    # Enterprise Page Header (No emojis, no AI marketing fluff)
    st.markdown("""
        <div class="page-header">
            <span class="page-eyebrow">Enterprise Dashboard</span>
            <h1 class="page-title">Resume Analysis</h1>
            <p class="page-subtitle">
                Upload your resume and job description to generate a detailed ATS compatibility report.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # ── Upload Section (Single Elegant Card) ──────────────────────────────
    st.markdown("""
        <div class="card" style="padding: 24px;">
            <div class="card-header">
                <div>
                    <h3 class="card-title">New Evaluation</h3>
                    <p class="card-subtitle">Select candidate document and target job specification</p>
                </div>
                <div style="font-size: 11px; font-weight: 600; color: #6B7280; background: #F1F5F9; padding: 4px 10px; border-radius: 6px;">
                    PDF / DOCX · Max 5 MB
                </div>
            </div>
    """, unsafe_allow_html=True)

    col_up, col_jd = st.columns([1, 1], gap="medium")

    with col_up:
        uploaded_file = st.file_uploader(
            "Resume Upload",
            type=["pdf", "docx"],
            help="Selectable PDF or Word DOCX document.",
            key="home_file_uploader"
        )

    with col_jd:
        job_desc = st.text_area(
            "Job Description (Optional)",
            height=130,
            placeholder="Paste target job description to evaluate keyword density and skill alignment...",
            key="home_job_desc"
        )

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    if st.button("Run Analysis", type="primary", use_container_width=True, key="home_run_analysis_btn"):
        if not uploaded_file:
            st.error("Please select a resume document to analyze.")
        else:
            with st.spinner("Processing evaluation..."):
                try:
                    file_bytes = uploaded_file.getvalue()
                    result = analyze_resume_api(file_bytes, uploaded_file.name, job_desc)
                    st.session_state['latest_analysis'] = result
                    st.session_state['_scorer_filename'] = uploaded_file.name
                    st.session_state['active_view'] = 'ATS Scorer'
                    st.rerun()
                except Exception as exc:
                    st.error(f"Analysis failed: {exc}")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # ── Enterprise Features Summary Grid ─────────────────────────────────
    st.markdown("""
        <div style="margin-bottom: 20px;">
            <span class="section-label">Core Evaluation Dimensions</span>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-top: 6px;">
                <div class="feature-card">
                    <div class="feature-title">ATS Compatibility</div>
                    <div class="feature-desc">Verifies layout parseability and standard heading structures.</div>
                </div>
                <div class="feature-card">
                    <div class="feature-title">Skill Match</div>
                    <div class="feature-desc">Validates listed candidate skills against project evidence.</div>
                </div>
                <div class="feature-card">
                    <div class="feature-title">Missing Skills</div>
                    <div class="feature-desc">Highlights critical candidate skill gaps relative to the job post.</div>
                </div>
                <div class="feature-card">
                    <div class="feature-title">Resume Formatting</div>
                    <div class="feature-desc">Identifies typography, layout, and document structure issues.</div>
                </div>
                <div class="feature-card">
                    <div class="feature-title">Keyword Analysis</div>
                    <div class="feature-desc">Measures exact and semantic keyword alignment density.</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ── Recent Analysis History Preview ──────────────────────────────────
    try:
        history = fetch_history_api()
    except Exception:
        history = []

    if history:
        st.markdown("""
            <div class="card" style="margin-top: 16px;">
                <div class="card-header">
                    <div>
                        <h3 class="card-title">Recent Analysis History</h3>
                        <p class="card-subtitle">Recent candidate evaluation records</p>
                    </div>
                    <span class="section-label" style="margin:0;">Audit Log</span>
                </div>
        """, unsafe_allow_html=True)

        for item in history[:3]:
            entry_id = item.get("id")
            filename = item.get("filename", "Resume")
            score = item.get("ats_score", 0)
            date = item.get("date", "")[:10]
            analysis_result = item.get("analysis_result", {})

            col_info, col_btn = st.columns([3, 1])
            with col_info:
                st.markdown(f"""
                    <div style="padding: 4px 0;">
                        <span style="font-size: 14px; font-weight: 700; color: #111827;">{filename}</span>
                        <span style="font-size: 12px; color: #6B7280; margin-left: 12px;">{date}</span>
                        <span style="font-size: 13px; font-weight: 700; color: #1E3A8A; margin-left: 16px;">Score: {score:.0f}/100</span>
                    </div>
                """, unsafe_allow_html=True)
            with col_btn:
                if st.button("View Report", key=f"home_load_{entry_id}"):
                    st.session_state['latest_analysis'] = analysis_result
                    st.session_state['_scorer_filename'] = filename
                    st.session_state['active_view'] = 'ATS Scorer'
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
