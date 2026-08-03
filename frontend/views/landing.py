import streamlit as st

def render_landing_view():
    # UI CHANGE: Hero Section with enterprise typography and clean layout spacing
    st.markdown("""
        <div class="hero-container">
            <span class="hero-eyebrow">AI-POWERED RESUME INTELLIGENCE</span>
            <h1 class="hero-title">Know exactly where your resume stands.</h1>
            <p class="hero-sub">
                Upload your resume document alongside target job descriptions to analyze ATS compatibility, 
                extract skill proof gaps, and surface actionable formatting feedback in seconds.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # CTA Button Container — Retains exact session state action
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        if st.button("Analyze My Resume", use_container_width=True):
            st.session_state['active_view'] = 'ATS Scorer'
            st.rerun()

    st.markdown("<div class='divider' style='margin: 36px 0 32px 0;'></div>", unsafe_allow_html=True)

    # UI CHANGE: Clean stat metrics pill grid matching enterprise dashboard style
    st.markdown("""
        <div style="display:flex; gap:16px; justify-content:center; flex-wrap:wrap;">
            <div class="stat-pill">
                <div class="stat-pill-value">5</div>
                <div class="stat-pill-label">Dimensions</div>
            </div>
            <div class="stat-pill">
                <div class="stat-pill-value">70B</div>
                <div class="stat-pill-label">LLM Engine</div>
            </div>
            <div class="stat-pill">
                <div class="stat-pill-value">&lt; 2s</div>
                <div class="stat-pill-label">Latency</div>
            </div>
            <div class="stat-pill">
                <div class="stat-pill-value">PDF</div>
                <div class="stat-pill-label">Export</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
