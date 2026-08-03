import streamlit as st
from services.api_client import fetch_history_api, delete_history_api, download_pdf_report_api

def render_history_view():
    # UI CHANGE: Structured page header for evaluation history records
    st.markdown("""
        <div class="page-header">
            <span class="page-eyebrow">Records</span>
            <h2 class="page-title">Analysis History</h2>
            <p class="page-subtitle">Review past resume evaluations, re-examine feedback, or export audit reports.</p>
        </div>
    """, unsafe_allow_html=True)

    with st.spinner("Fetching evaluation records..."):
        history = fetch_history_api()

    if not history:
        st.info("No past resume evaluation records found.")
        return

    for item in history:
        entry_id = item.get("id")
        filename = item.get("filename", "Resume")
        score = item.get("ats_score", 0)
        date = item.get("date", "")[:10]
        analysis_result = item.get("analysis_result", {})

        # UI CHANGE: Clean record summary card layout with crisp typography
        st.markdown(f"""
            <div class="card" style="margin-bottom:12px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <h4 style="margin:0 0 2px 0; color:#111827; font-size:14px; font-weight:600;">{filename}</h4>
                        <small style="color:#6B7280; font-size:12px;">Evaluated on {date}</small>
                    </div>
                    <div style="font-size:22px; font-weight:700; color:#2563EB;">{score:.0f} / 100</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        col_act1, col_act2 = st.columns([1, 1])
        with col_act1:
            if st.button(f"Load Analysis: {filename}", key=f"load_{entry_id}"):
                st.session_state['latest_analysis'] = analysis_result
                st.session_state['active_view'] = 'ATS Scorer'
                st.rerun()

        with col_act2:
            if st.button("Delete Record", key=f"del_{entry_id}"):
                if delete_history_api(entry_id):
                    st.success("Record deleted.")
                    st.rerun()
