import streamlit as st

def render_resources_view():
    # UI CHANGE: Structured page header for optimization guidelines
    st.markdown("""
        <div class="page-header">
            <span class="page-eyebrow">Guidelines</span>
            <h2 class="page-title">Resume Optimization Guidelines</h2>
            <p class="page-subtitle">Best practices and industry standards to maximize ATS parsing performance.</p>
        </div>
    """, unsafe_allow_html=True)

    # UI CHANGE: Modern guidelines cards with clean enterprise typography and code callouts
    st.markdown("""
        <div class="card">
            <h3 style="color:#2563EB; font-size:15px; margin:0 0 6px 0;">1. Standard Section Headers</h3>
            <p style="color:#6B7280; font-size:13px; margin:0;">
                ATS parsers look for standard headers: <code>SUMMARY</code>, <code>EXPERIENCE</code>, <code>PROJECTS</code>, <code>EDUCATION</code>, and <code>SKILLS</code>. Avoid non-standard titles such as <em>"What I've Done"</em> or <em>"My Background"</em>.
            </p>
        </div>

        <div class="card">
            <h3 style="color:#2563EB; font-size:15px; margin:0 0 6px 0;">2. Quantifiable Impact Formula</h3>
            <p style="color:#6B7280; font-size:13px; margin:0 0 6px 0;">
                Structure accomplishments using Google's recommended XYZ formula: <strong>"Accomplished [X] as measured by [Y], by doing [Z]."</strong>
            </p>
            <p style="color:#16A34A; font-family:'SFMono-Regular',Consolas,Monaco,monospace; font-size:12px; margin:0; background:#F8FAFC; padding:8px 12px; border-radius:6px; border:1px solid #E5E7EB;">
                Example: "Reduced API response latency by 42% (Y) by refactoring database indexing and implementing Redis caching (Z)."
            </p>
        </div>

        <div class="card">
            <h3 style="color:#2563EB; font-size:15px; margin:0 0 6px 0;">3. Contact Information Privacy</h3>
            <p style="color:#6B7280; font-size:13px; margin:0;">
                Do not include full physical street addresses or zip codes on your resume document. Specifying only <strong>"City, State"</strong> satisfies ATS location filters while protecting candidate privacy.
            </p>
        </div>
    """, unsafe_allow_html=True)
