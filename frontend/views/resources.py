import streamlit as st

def render_resources_view():
    st.markdown("""
        <div class="page-header">
            <span class="page-eyebrow">Optimization Guidelines</span>
            <h1 class="page-title">ATS Resume Optimization Guidelines</h1>
            <p class="page-subtitle">Standardized formatting rules and impact formulas to maximize ATS compliance and candidate match precision.</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="card">
            <div class="card-header">
                <div>
                    <h3 class="card-title">1. Standardized Section Headers</h3>
                    <p class="card-subtitle">ATS parser taxonomy rules</p>
                </div>
            </div>
            <p style="color:#6B7280; font-size:13.5px; margin:0; line-height:1.6;">
                ATS keyword parsers rely on canonical section titles: <code style="background:#F1F5F9; padding:2px 6px; border-radius:4px; color:#1E3A8A;">SUMMARY</code>, <code style="background:#F1F5F9; padding:2px 6px; border-radius:4px; color:#1E3A8A;">EXPERIENCE</code>, <code style="background:#F1F5F9; padding:2px 6px; border-radius:4px; color:#1E3A8A;">PROJECTS</code>, <code style="background:#F1F5F9; padding:2px 6px; border-radius:4px; color:#1E3A8A;">EDUCATION</code>, and <code style="background:#F1F5F9; padding:2px 6px; border-radius:4px; color:#1E3A8A;">SKILLS</code>. Avoid non-standard labels such as <em>"What I've Done"</em> or <em>"Career Highlights"</em>.
            </p>
        </div>

        <div class="card">
            <div class="card-header">
                <div>
                    <h3 class="card-title">2. Quantifiable Impact Formula (XYZ Method)</h3>
                    <p class="card-subtitle">Google recommended bullet formulation</p>
                </div>
            </div>
            <p style="color:#6B7280; font-size:13.5px; margin:0 0 10px 0; line-height:1.6;">
                Format every accomplishment bullet using the structured impact formula: <strong>"Accomplished [X], as measured by [Y], by doing [Z]."</strong>
            </p>
            <div style="background:#F8FAFC; padding:12px 14px; border-radius:8px; border:1px solid #E5E7EB; font-family:'SFMono-Regular',Consolas,Monaco,monospace; font-size:12.5px; color:#15803D;">
                Example: "Reduced API response latency by 42% (Y) by refactoring database indexing and implementing Redis caching (Z)."
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <div>
                    <h3 class="card-title">3. Contact Information & Privacy Standard</h3>
                    <p class="card-subtitle">Candidate privacy and location filter compliance</p>
                </div>
            </div>
            <p style="color:#6B7280; font-size:13.5px; margin:0; line-height:1.6;">
                Omit full physical street addresses or zip codes on your candidate resume document. Specifying <strong>"City, State"</strong> satisfies location filters while protecting candidate privacy.
            </p>
        </div>
    """, unsafe_allow_html=True)
