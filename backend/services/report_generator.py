import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from typing import Dict

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), '..', 'templates')
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

def format_date(value, fmt='%B %d, %Y at %I:%M %p'):
    if not value:
        return ''
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return dt.strftime(fmt)
    except Exception:
        return value

env.filters['format_date'] = format_date

def generate_html_reports(analysis_data: Dict) -> Dict[str, str]:
    now = datetime.now().isoformat()
    overall_score = analysis_data.get('ATS_score', 0) or analysis_data.get('ats_score', 0)
    interpretation = analysis_data.get('interpretation', '')
    cs = analysis_data.get('component_scores', {})
    if hasattr(cs, '__dict__'):
        cs = cs.__dict__

    component_scores = {
        'formatting': float(cs.get('formatting', 0)),
        'keywords': float(cs.get('keywords', 0)),
        'content': float(cs.get('content', 0)),
        'skill_validation': float(cs.get('skill_validation', 0)),
        'ats_compatibility': float(cs.get('ats_compatibility', 0)),
    }

    def pct(score, max_score):
        return min(100, max(0, round(score / max_score * 100)))

    component_pct = {
        'formatting': pct(component_scores['formatting'], 20),
        'keywords': pct(component_scores['keywords'], 25),
        'content': pct(component_scores['content'], 25),
        'skill_validation': pct(component_scores['skill_validation'], 15),
        'ats_compatibility': pct(component_scores['ats_compatibility'], 15),
    }

    raw_fb = analysis_data.get('detailed_feedback', [])
    detailed_feedback = [
        fb if isinstance(fb, dict) else (fb.model_dump() if hasattr(fb, 'model_dump') else fb.__dict__)
        for fb in raw_fb
    ]

    svd_raw = analysis_data.get('skill_validation_details') or {}
    if hasattr(svd_raw, 'model_dump'):
        svd_raw = svd_raw.model_dump()

    jd_raw = analysis_data.get('jd_match_analysis') or analysis_data.get('jd_comparison')
    if hasattr(jd_raw, 'model_dump'):
        jd_raw = jd_raw.model_dump()

    score_color = '#16a34a' if overall_score >= 80 else ('#d97706' if overall_score >= 60 else '#dc2626')

    context = {
        'timestamp': now,
        'overall_score': overall_score,
        'score_color': score_color,
        'interpretation': interpretation,
        'component_scores': component_scores,
        'component_pct': component_pct,
        'strengths': analysis_data.get('strengths', []),
        'all_feedback': detailed_feedback,
        'validated_skills': svd_raw.get('validated', []),
        'unvalidated_skills': svd_raw.get('unvalidated', []),
        'jd_analysis': jd_raw,
    }

    try:
        return {
            'summary': env.get_template('summary.html').render(**context),
            'skill_report': env.get_template('action_items.html').render(**context),
            'jd_report': env.get_template('quick_actions.html').render(**context),
            'recommendations': env.get_template('jd_comparison.html').render(**context),
        }
    except Exception:
        # Fallback inline HTML generator if template files are being loaded dynamically
        fallback_html = f"""
        <html><head><style>body{{font-family:Arial;padding:30px;color:#1e293b;}} h1{{color:#4f46e5;}}</style></head>
        <body>
        <h1>ATS Resume Analysis Report</h1>
        <p><strong>Overall Score:</strong> {overall_score}/100</p>
        <p><strong>Interpretation:</strong> {interpretation}</p>
        <h3>Score Breakdown</h3>
        <ul>
            <li>Formatting: {component_scores['formatting']}/20</li>
            <li>Keywords: {component_scores['keywords']}/25</li>
            <li>Content Quality: {component_scores['content']}/25</li>
            <li>Skill Validation: {component_scores['skill_validation']}/15</li>
            <li>ATS Compatibility: {component_scores['ats_compatibility']}/15</li>
        </ul>
        </body></html>
        """
        return {'summary': fallback_html, 'skill_report': fallback_html, 'jd_report': fallback_html, 'recommendations': fallback_html}
