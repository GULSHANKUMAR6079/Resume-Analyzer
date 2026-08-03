import streamlit as st
from services.api_client import analyze_resume_api, download_pdf_report_api

def render_scorer_view():

    # UI CHANGE: Structured page header with enterprise eyebrow and typography
    st.markdown("""
        <div class="page-header">
            <span class="page-eyebrow">Evaluation Engine</span>
            <h2 class="page-title">ATS Resume Scorer</h2>
            <p class="page-subtitle">
                Upload your resume document. Optionally provide a target job description for keyword density and skill gap analysis.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # ── Upload & Job Description Inputs ──────────────────────────────────
    # UI CHANGE: Balanced form input layout with clear field descriptions
    col_up, col_jd = st.columns([1, 1], gap="medium")

    with col_up:
        uploaded_file = st.file_uploader(
            "Resume Document (PDF or DOCX, max 5 MB)",
            type=["pdf", "docx"],
            help="Text-selectable PDF or DOCX file."
        )

    with col_jd:
        job_desc = st.text_area(
            "Target Job Description (Optional)",
            height=130,
            placeholder="Paste target job description text to evaluate keyword alignment and skill gaps..."
        )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Trigger Evaluation Button — Retains exact execution logic
    if st.button("Run Analysis", type="primary", use_container_width=True):
        if not uploaded_file:
            st.error("Please upload a resume document to continue.")
            return

        with st.spinner("Analyzing resume against ATS requirements..."):
            try:
                file_bytes = uploaded_file.getvalue()
                result = analyze_resume_api(file_bytes, uploaded_file.name, job_desc)
                st.session_state['latest_analysis'] = result
                st.session_state['_scorer_filename'] = uploaded_file.name
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                return

    # ── Results Render Section ───────────────────────────────────────────
    res = st.session_state.get('latest_analysis')
    if not res:
        return

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    overall_score = res.get("ATS_score", 0) or res.get("ats_score", 0)
    interpretation = res.get("interpretation", "")
    filename = st.session_state.get('_scorer_filename', 'Resume')

    # UI CHANGE: Enterprise color thresholds (#16A34A success, #D97706 warning, #DC2626 error)
    if overall_score >= 80:
        score_color = "#16A34A"
        tier = "Strong Alignment"
    elif overall_score >= 60:
        score_color = "#D97706"
        tier = "Moderate Match"
    else:
        score_color = "#DC2626"
        tier = "Needs Optimization"

    # ── Score Summary Header ──────────────────────────────────────────────
    # UI CHANGE: Score summary block with high contrast typography and clean layout
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
                <span class="section-label" style="color:{score_color}; font-weight:700;">{tier} — {filename}</span>
                <h3 style="color:#111827; margin:4px 0 10px 0; font-size:1.25rem; font-weight:700;">
                    {interpretation}
                </h3>
            </div>
        """, unsafe_allow_html=True)

        # Download Report PDF Button — Retains exact API call
        pdf_bytes = download_pdf_report_api(res)
        if pdf_bytes:
            st.download_button(
                label="Download PDF Report",
                data=pdf_bytes,
                file_name=f"ATS_Report_{filename}.pdf",
                mime="application/pdf"
            )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Results Tabs ─────────────────────────────────────────────────────
    # UI CHANGE: Clean, high-contrast tab bar layout
    tab_scores, tab_skills, tab_jd, tab_issues = st.tabs([
        "Score Breakdown",
        "Skill Validation",
        "JD Match",
        "Issues & Fixes"
    ])

    # ── Tab: Score Breakdown ─────────────────────────────────────────────
    with tab_scores:
        cs = res.get("component_scores", {})
        if hasattr(cs, "__dict__"):
            cs = cs.__dict__

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

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

    # ── Tab: Skill Validation ────────────────────────────────────────────
    with tab_skills:
        svd = res.get("skill_validation_details", {})
        if hasattr(svd, "__dict__"):
            svd = svd.__dict__

        val_pct  = svd.get("validation_pct", 0)
        val_cnt  = svd.get("validated_count", 0)
        total    = svd.get("total", 0)

        # UI CHANGE: Skill evidence summary with enterprise text colors
        st.markdown(f"""
            <div style="margin: 8px 0 20px 0;">
                <span class="section-label">Skill Evidence Verification</span>
                <div style="display:flex; align-items:baseline; gap:10px;">
                    <span style="font-size:2rem; font-weight:800; color:#111827;">{val_pct}%</span>
                    <span style="color:#6B7280; font-size:14px;">{val_cnt} of {total} skills backed by project evidence</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        col_v, col_u = st.columns(2, gap="large")

        with col_v:
            st.markdown("""
                <span class="section-label" style="color:#16A34A;">Verified Skills</span>
            """, unsafe_allow_html=True)
            validated = svd.get("validated", [])
            if validated:
                tags_html = ""
                for item in validated:
                    skill_name = item.get("skill") if isinstance(item, dict) else str(item)
                    projects   = item.get("projects", []) if isinstance(item, dict) else []
                    evidence   = projects[0] if projects else "Experience"
                    tags_html += f'<span class="skill-tag-valid" title="Evidence: {evidence}">{skill_name}</span>'
                st.markdown(f"<div style='line-height:2;'>{tags_html}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='color:#6B7280; font-size:13px;'>No verified skills found.</p>", unsafe_allow_html=True)

        with col_u:
            st.markdown("""
                <span class="section-label" style="color:#DC2626;">Unverified Skills</span>
            """, unsafe_allow_html=True)
            unvalidated = svd.get("unvalidated", [])
            if unvalidated:
                tags_html = "".join(f'<span class="skill-tag-invalid">{s}</span>' for s in unvalidated)
                st.markdown(f"<div style='line-height:2;'>{tags_html}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='color:#6B7280; font-size:13px;'>All listed skills have supporting evidence.</p>", unsafe_allow_html=True)

    # ── Tab: JD Match ────────────────────────────────────────────────────
    with tab_jd:
        jd_match = res.get("jd_match_analysis") or res.get("jd_comparison")

        if jd_match:
            if hasattr(jd_match, "__dict__"):
                jd_match = jd_match.__dict__

            match_score = jd_match.get("match_percentage", 0)
            sem_sim     = jd_match.get("semantic_similarity", 0)

            # UI CHANGE: Alignment score summary layout
            st.markdown(f"""
                <div style="margin: 8px 0 20px 0;">
                    <span class="section-label">Job Description Alignment</span>
                    <div style="display:flex; align-items:baseline; gap:12px; flex-wrap:wrap;">
                        <span style="font-size:2rem; font-weight:800; color:#111827;">{match_score:.1f}%</span>
                        <span style="color:#6B7280; font-size:14px;">keyword match · {sem_sim*100:.0f}% semantic similarity</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            col_m, col_mis = st.columns(2, gap="large")

            with col_m:
                st.markdown('<span class="section-label" style="color:#16A34A;">Matched Keywords</span>', unsafe_allow_html=True)
                matched = jd_match.get("matched_keywords", [])
                if matched:
                    html = "".join(f'<span class="kw-matched">{kw}</span>' for kw in matched)
                    st.markdown(f"<div style='line-height:2.2;'>{html}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<p style='color:#6B7280; font-size:13px;'>No matched keywords found.</p>", unsafe_allow_html=True)

            with col_mis:
                st.markdown('<span class="section-label" style="color:#DC2626;">Missing Keywords</span>', unsafe_allow_html=True)
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
                st.markdown(f"<div style='line-height:2;'>{html}</div>", unsafe_allow_html=True)

        else:
            # UI CHANGE: Enterprise empty state container
            st.markdown("""
                <div class="card" style="text-align:center; padding: 28px;">
                    <p style="color:#6B7280; font-size:14px; margin:0;">
                        No job description was provided. Paste a target job description above and re-run analysis to view keyword match and skill gap results.
                    </p>
                </div>
            """, unsafe_allow_html=True)

    # ── Tab: Issues & Fixes ─────────────────────────────────────────────
    with tab_issues:
        issues = res.get("detailed_feedback", [])

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        if not issues:
            # UI CHANGE: Success state feedback card
            st.markdown("""
                <div class="card" style="text-align:center; padding:28px;">
                    <p style="color:#16A34A; font-size:14px; font-weight:600; margin:0;">
                        No critical issues detected. Your resume structure looks solid.
                    </p>
                </div>
            """, unsafe_allow_html=True)
            return

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

            # UI CHANGE: Enterprise feedback card with primary blue accent on action fixes
            st.markdown(f"""
                <div class="{card_cls}">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:6px;">
                        <p class="issue-title">{issue.get('issue_title', '')}</p>
                        <span class="{badge_cls}" style="white-space:nowrap; margin-left:12px;">{sev.capitalize()}</span>
                    </div>
                    <p class="issue-body">{issue.get('explanation', '')}</p>
                    <p class="issue-fix"><strong style="color:#2563EB;">Fix:</strong> {issue.get('how_to_fix', '')}</p>
                    {action_items_html}
                    {example_block}
                </div>
            """, unsafe_allow_html=True)
