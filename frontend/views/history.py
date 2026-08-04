import streamlit as st
from services.api_client import fetch_history_api, delete_history_api

def render_history_view():
    st.markdown("""
        <div class="page-header">
            <span class="page-eyebrow">Audit Records</span>
            <h1 class="page-title">Analysis History</h1>
            <p class="page-subtitle">Review past candidate evaluation records, re-examine feedback, or export audit reports.</p>
        </div>
    """, unsafe_allow_html=True)

    with st.spinner("Fetching evaluation records..."):
        try:
            history = fetch_history_api()
        except Exception as exc:
            st.error(f"Failed to load evaluation history: {exc}")
            return

    if not history:
        st.markdown("""
            <div class="card" style="text-align:center; padding:32px;">
                <p style="color:#6B7280; font-size:14px; margin:0;">
                    No evaluation records found. Analyze candidate resumes on the Dashboard to build your evaluation log.
                </p>
            </div>
        """, unsafe_allow_html=True)
        return

    st.markdown("""
        <div class="card" style="padding:0; overflow:hidden;">
            <table class="enterprise-table">
                <thead>
                    <tr>
                        <th style="width:35%;">Resume Document</th>
                        <th style="width:20%;">Evaluation Date</th>
                        <th style="width:20%;">ATS Score</th>
                        <th style="width:25%;">Actions</th>
                    </tr>
                </thead>
                <tbody>
    """, unsafe_allow_html=True)

    for item in history:
        entry_id = item.get("id")
        filename = item.get("filename", "Resume")
        score = item.get("ats_score", 0)
        date = item.get("date", "")[:10]
        analysis_result = item.get("analysis_result", {})

        if score >= 80:
            score_badge = f'<span style="color:#15803D; font-weight:700;">{score:.0f} / 100 (Strong)</span>'
        elif score >= 60:
            score_badge = f'<span style="color:#B45309; font-weight:700;">{score:.0f} / 100 (Moderate)</span>'
        else:
            score_badge = f'<span style="color:#B91C1C; font-weight:700;">{score:.0f} / 100 (Needs Fix)</span>'

        c1, c2, c3, c4 = st.columns([3.5, 2, 2, 2.5])

        with c1:
            st.markdown(f"<div style='padding:12px 0 0 14px; font-weight:600; color:#111827;'>{filename}</div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div style='padding:12px 0 0 0; color:#6B7280; font-size:13px;'>{date}</div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div style='padding:12px 0 0 0;'>{score_badge}</div>", unsafe_allow_html=True)
        with c4:
            b_col1, b_col2 = st.columns(2)
            with b_col1:
                if st.button("View", key=f"hist_load_{entry_id}"):
                    st.session_state['latest_analysis'] = analysis_result
                    st.session_state['_scorer_filename'] = filename
                    st.session_state['active_view'] = 'ATS Scorer'
                    st.rerun()
            with b_col2:
                if st.button("Delete", key=f"hist_del_{entry_id}"):
                    if delete_history_api(entry_id):
                        st.success("Record deleted.")
                        st.rerun()

        st.markdown("<div style='height:1px; background-color:#E5E7EB; margin:4px 0;'></div>", unsafe_allow_html=True)

    st.markdown("</tbody></table></div>", unsafe_allow_html=True)
