import streamlit as st
from services.api_client import analyze_resume_api, download_pdf_report_api

def render_scorer_view():
    # Enterprise Page Header
    st.markdown("""
        <div class="page-header">
            <span class="page-eyebrow">Evaluation Engine</span>
            <h1 class="page-title">ATS Resume Scorer</h1>
            <p class="page-subtitle">
                Upload your candidate document and target job description to run an automated ATS compliance audit.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # ── Upload Section (Card Container) ──────────────────────────────────
    st.markdown("""
        <div class="card" style="padding: 22px;">
            <div class="card-header">
                <div>
                    <h3 class="card-title">Document Inputs</h3>
                    <p class="card-subtitle">Upload resume and paste job description</p>
                </div>
            </div>
    """, unsafe_allow_html=True)

    col_up, col_jd = st.columns([1, 1], gap="medium")

    with col_up:
        uploaded_file = st.file_uploader(
            "Resume Upload",
            type=["pdf", "docx"],
            help="Text-selectable PDF or DOCX file.",
            key="scorer_file_uploader"
        )

    with col_jd:
        job_desc = st.text_area(
            "Target Job Description (Optional)",
            height=130,
            placeholder="Paste target job description text to evaluate keyword alignment and skill gaps...",
            key="scorer_job_desc"
        )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if st.button("Run Analysis", type="primary", use_container_width=True, key="scorer_run_btn"):
        if not uploaded_file:
            st.error("Please upload a resume document to continue.")
        else:
            with st.spinner("Analyzing document against ATS metrics..."):
                try:
                    file_bytes = uploaded_file.getvalue()
                    result = analyze_resume_api(file_bytes, uploaded_file.name, job_desc)
                    st.session_state['latest_analysis'] = result
                    st.session_state['_scorer_filename'] = uploaded_file.name
                except Exception as exc:
                    st.error(f"Analysis failed: {exc}")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Results Section ──────────────────────────────────────────────────
    res = st.session_state.get('latest_analysis')
    if not res:
        return

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    overall_score = res.get("ATS_score", 0) or res.get("ats_score", 0)
    interpretation = res.get("interpretation", "")
    filename = st.session_state.get('_scorer_filename', 'Resume')

    if overall_score >= 80:
        score_color = "#15803D"
        tier = "Strong Alignment"
    elif overall_score >= 60:
        score_color = "#B45309"
        tier = "Moderate Alignment"
    else:
        score_color = "#B91C1C"
        tier = "Needs Optimization"

    # ── Score Card Container ─────────────────────────────────────────────
    st.markdown("<div class='card' style='padding: 24px;'>", unsafe_allow_html=True)
    c_gauge, c_info = st.columns([1, 2], gap="large")

    with c_gauge:
        st.markdown(f"""
            <div class="score-circle" style="border-color:{score_color};">
                <div class="score-num" style="color:{score_color};">{overall_score:.0f}</div>
                <div class="score-label">ATS Score</div>
            </div>
        """, unsafe_allow_html=True)

    with c_info:
        st.markdown(f"""
            <div style="padding: 4px 0;">
                <span class="section-label" style="color:{score_color}; font-weight:700;">{tier} · {filename}</span>
                <h3 style="color:#111827; margin:6px 0 12px 0; font-size:1.2rem; font-weight:700; line-height:1.4;">
                    {interpretation}
                </h3>
            </div>
        """, unsafe_allow_html=True)

        pdf_bytes = download_pdf_report_api(res)
        if pdf_bytes:
            st.download_button(
                label="Download PDF Report",
                data=pdf_bytes,
                file_name=f"ATS_Report_{filename}.pdf",
                mime="application/pdf",
                key="download_pdf_report_btn"
            )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Results Tabs ─────────────────────────────────────────────────────
    tab_scores, tab_skills, tab_jd, tab_issues = st.tabs([
        "Score Breakdown",
        "Skill Validation",
        "Keyword Alignment",
        "Issues & Recommendations"
    ])

    # ── Tab 1: Score Breakdown ───────────────────────────────────────────
    with tab_scores:
        st.markdown("<div class='card' style='margin-top: 12px;'>", unsafe_allow_html=True)
        cs = res.get("component_scores", {})
        if hasattr(cs, "__dict__"):
            cs = cs.__dict__

        dims = [
            ("Formatting & Structure",   "formatting",       20),
            ("Keyword Density",          "keywords",         25),
            ("Content Quality",          "content",          25),
            ("Skill Proof Validation",   "skill_validation", 15),
            ("ATS Filter Compatibility", "ats_compatibility",15),
        ]

        col_b1, col_b2 = st.columns(2, gap="large")

        for i, (label, key, max_val) in enumerate(dims):
            raw = float(cs.get(key, 0))
            pct = raw / max_val
            col = col_b1 if i % 2 == 0 else col_b2
            with col:
                st.markdown(f"""
                    <div class="score-bar-wrap">
                        <div class="score-bar-header">
                            <span class="score-bar-title">{label}</span>
                            <span class="score-bar-value">{raw:.1f} / {max_val}</span>
                        </div>
                        <div class="score-bar-track">
                            <div class="score-bar-fill" style="width:{min(pct*100,100):.1f}%; background-color:{score_color};"></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Tab 2: Skill Validation ──────────────────────────────────────────
    with tab_skills:
        st.markdown("<div class='card' style='margin-top: 12px;'>", unsafe_allow_html=True)
        svd = res.get("skill_validation_details", {})
        if hasattr(svd, "__dict__"):
            svd = svd.__dict__

        val_pct  = svd.get("validation_pct", 0)
        val_cnt  = svd.get("validated_count", 0)
        total    = svd.get("total", 0)

        st.markdown(f"""
            <div style="margin-bottom: 20px;">
                <span class="section-label">Skill Evidence Verification</span>
                <div style="display:flex; align-items:baseline; gap:12px;">
                    <span style="font-size:2rem; font-weight:800; color:#111827;">{val_pct}%</span>
                    <span style="color:#6B7280; font-size:13.5px;">{val_cnt} of {total} listed skills substantiated by project or work experience</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        col_v, col_u = st.columns(2, gap="large")

        with col_v:
            st.markdown('<span class="section-label" style="color:#15803D;">Verified Skills</span>', unsafe_allow_html=True)
            validated = svd.get("validated", [])
            if validated:
                tags_html = ""
                for item in validated:
                    skill_name = item.get("skill") if isinstance(item, dict) else str(item)
                    projects   = item.get("projects", []) if isinstance(item, dict) else []
                    evidence   = projects[0] if projects else "Experience"
                    tags_html += f'<span class="skill-tag-valid" title="Evidence: {evidence}">{skill_name}</span>'
                st.markdown(f"<div style='line-height:2.2;'>{tags_html}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='color:#6B7280; font-size:13px;'>No verified skills identified.</p>", unsafe_allow_html=True)

        with col_u:
            st.markdown('<span class="section-label" style="color:#B91C1C;">Unverified Skills</span>', unsafe_allow_html=True)
            unvalidated = svd.get("unvalidated", [])
            if unvalidated:
                tags_html = "".join(f'<span class="skill-tag-invalid">{s}</span>' for s in unvalidated)
                st.markdown(f"<div style='line-height:2.2;'>{tags_html}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='color:#6B7280; font-size:13px;'>All listed skills have supporting project evidence.</p>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Tab 3: Keyword Alignment & JD Match ──────────────────────────────
    with tab_jd:
        st.markdown("<div class='card' style='margin-top: 12px;'>", unsafe_allow_html=True)
        jd_match = res.get("jd_match_analysis") or res.get("jd_comparison")

        if jd_match:
            if hasattr(jd_match, "__dict__"):
                jd_match = jd_match.__dict__

            match_score = jd_match.get("match_percentage", 0)
            sem_sim     = jd_match.get("semantic_similarity", 0)

            st.markdown(f"""
                <div style="margin-bottom: 20px;">
                    <span class="section-label">Job Description Match</span>
                    <div style="display:flex; align-items:baseline; gap:14px; flex-wrap:wrap;">
                        <span style="font-size:2rem; font-weight:800; color:#111827;">{match_score:.1f}%</span>
                        <span style="color:#6B7280; font-size:13.5px;">keyword match · {sem_sim*100:.0f}% semantic similarity</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            col_m, col_mis = st.columns(2, gap="large")

            with col_m:
                st.markdown('<span class="section-label" style="color:#15803D;">Matched Keywords</span>', unsafe_allow_html=True)
                matched = jd_match.get("matched_keywords", [])
                if matched:
                    html = "".join(f'<span class="kw-matched">{kw}</span>' for kw in matched)
                    st.markdown(f"<div style='line-height:2.2;'>{html}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<p style='color:#6B7280; font-size:13px;'>No matched keywords found.</p>", unsafe_allow_html=True)

            with col_mis:
                st.markdown('<span class="section-label" style="color:#B91C1C;">Missing Keywords</span>', unsafe_allow_html=True)
                missing = jd_match.get("missing_keywords", [])
                if missing:
                    html = "".join(f'<span class="kw-missing">{kw}</span>' for kw in missing)
                    st.markdown(f"<div style='line-height:2.2;'>{html}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<p style='color:#6B7280; font-size:13px;'>No missing keywords — strong alignment.</p>", unsafe_allow_html=True)

            skills_gap = jd_match.get("skills_gap", [])
            if skills_gap:
                st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
                st.markdown('<span class="section-label">Skills Gap</span>', unsafe_allow_html=True)
                html = "".join(f'<span class="skill-tag">{s}</span>' for s in skills_gap)
                st.markdown(f"<div style='line-height:2.2;'>{html}</div>", unsafe_allow_html=True)

        else:
            st.markdown("""
                <div style="text-align:center; padding: 18px 0;">
                    <p style="color:#6B7280; font-size:13.5px; margin:0;">
                        No job description provided. Paste a target job description above and click Run Analysis to evaluate keyword alignment and skill gaps.
                    </p>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Tab 4: Issues & Recommendations ─────────────────────────────────
    with tab_issues:
        issues = res.get("detailed_feedback", [])
        if not issues:
            st.markdown("""
                <div class="card" style="text-align:center; padding: 24px; margin-top: 12px;">
                    <p style="color:#15803D; font-size:14px; font-weight:600; margin:0;">
                        No critical formatting or structural issues detected.
                    </p>
                </div>
            """, unsafe_allow_html=True)
            return

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        for issue in issues:
            if hasattr(issue, "__dict__"):
                issue = issue.__dict__

            sev = (issue.get("severity_level") or "Moderate").lower()
            card_cls = "issue-card"
            if sev in ("high", "critical"):
                card_cls += ""
            elif sev in ("moderate", "medium"):
                card_cls += " moderate"
            else:
                card_cls += " low"

            badge_cls = "badge-critical" if sev in ("high", "critical") else (
                "badge-high" if sev in ("moderate", "medium") else "badge-medium"
            )

            example_block = ""
            if issue.get("example_improvement"):
                example_block = f"""
                    <div class="code-block">{issue.get('example_improvement')}</div>
                """

            action_items_html = ""
            actions = issue.get("action_items", [])
            if actions:
                items = "".join(f"<li style='color:#6B7280; font-size:13.5px; margin-bottom:4px;'>{a}</li>" for a in actions)
                action_items_html = f"<ul style='padding-left:18px; margin:8px 0 0 0;'>{items}</ul>"

            st.markdown(f"""
                <div class="{card_cls}">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:6px;">
                        <p class="issue-title">{issue.get('issue_title', '')}</p>
                        <span class="{badge_cls}" style="white-space:nowrap; margin-left:12px;">{sev.capitalize()}</span>
                    </div>
                    <p class="issue-body">{issue.get('explanation', '')}</p>
                    <p class="issue-fix"><strong style="color:#1E3A8A;">Recommendation:</strong> {issue.get('how_to_fix', '')}</p>
                    {action_items_html}
                    {example_block}
                </div>
            """, unsafe_allow_html=True)
