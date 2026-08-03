import re
from typing import List, Dict, Optional
from backend.models.schemas import IssueDetail

def analyze_issues(
    resume_text: str,
    parsed_resume: Dict,
    skills: List[str],
    projects: List[Dict],
    action_verbs: List[str],
    skill_validation: Dict,
    scores: Dict,
    contact_info: Optional[Dict] = None,
) -> List[IssueDetail]:

    detected: List[IssueDetail] = []
    exp_entries = [e for e in parsed_resume.get('experience', []) if isinstance(e, dict)]
    edu_entries = [e for e in parsed_resume.get('education', []) if isinstance(e, dict)]
    proj_entries = [p for p in parsed_resume.get('projects', []) if isinstance(p, dict)]
    summary = (parsed_resume.get('professional_summary') or '').strip()
    experience_text = '\n'.join(e.get('description', '') for e in exp_entries).strip()

    resume_lower = resume_text.lower()
    has_projects_signal = any(kw in resume_lower for kw in [
        'project', 'github.com', 'deployed', 'built a', 'developed a',
        'created a', 'implemented a', 'live demo', 'tech stack',
    ])

    # 1. Missing Projects
    if not proj_entries and len(projects) == 0 and not has_projects_signal:
        detected.append(IssueDetail(
            issue_title="Missing Projects Section",
            severity_level="High",
            ats_impact="High",
            explanation="No dedicated Projects section detected. Recruiters look for applied evidence of listed skills.",
            where_it_appears="Resume structure — no 'Projects' header found",
            how_to_fix="Add a 'Projects' section featuring 2-3 key technical projects with measurable outcomes.",
            action_items=[
                "Add a 'PROJECTS' section after your Experience section",
                "Describe 2-3 projects with title, tech stack, and impact metrics",
                "Link to GitHub or live demo URLs"
            ],
            example_improvement="PROJECTS\n• E-Commerce Platform — Built full-stack site with React and Node.js. Handled 500+ orders/month."
        ))

    # 2. Missing Experience
    has_exp_signal = any(kw in resume_lower for kw in [
        'intern', 'internship', 'employed', 'company', 'role', 'engineer', 'developer'
    ])
    if not exp_entries and not has_exp_signal:
        detected.append(IssueDetail(
            issue_title="Missing Experience Section",
            severity_level="High",
            ats_impact="High",
            explanation="No work history found. Even for entry-level candidates, internships or freelance work demonstrate impact.",
            where_it_appears="Resume structure — no 'Experience' header found",
            how_to_fix="Add an 'Experience' or 'Internships' section detailing your past roles and achievements.",
            action_items=[
                "Add an 'EXPERIENCE' section",
                "Include Role Title — Company Name (Dates)",
                "Add 2-4 bullet points starting with action verbs"
            ],
            example_improvement="EXPERIENCE\nSoftware Engineering Intern — XYZ Corp (Jun 2025 – Aug 2025)\n• Developed REST APIs with FastAPI serving 10K requests/day"
        ))

    # 3. Missing Education
    has_edu_signal = any(kw in resume_lower for kw in ['b.tech', 'bachelor', 'master', 'university', 'college', 'gpa', 'degree'])
    if not edu_entries and not has_edu_signal:
        detected.append(IssueDetail(
            issue_title="Missing Education Section",
            severity_level="Moderate",
            ats_impact="Medium",
            explanation="No education credentials detected. Most ATS filters check for degree and university details.",
            where_it_appears="Resume structure — no 'Education' header found",
            how_to_fix="Add an 'Education' section listing your degree, institution, and graduation year.",
            action_items=[
                "Add an 'EDUCATION' section",
                "Format: Degree Name — University Name (Graduation Year)"
            ],
            example_improvement="EDUCATION\nB.Tech in Computer Science — IIT Delhi (2021–2025)"
        ))

    # 4. Unvalidated Skills
    unvalidated = skill_validation.get('unvalidated_skills', [])
    validated = skill_validation.get('validated_skills', [])
    total_skills = len(unvalidated) + len(validated)

    if total_skills > 0 and len(unvalidated) > len(validated):
        detected.append(IssueDetail(
            issue_title="Most Skills Lack Supporting Evidence",
            severity_level="Moderate",
            ats_impact="High",
            explanation=f"{len(unvalidated)} of your {total_skills} skills are not demonstrated in any project or experience section.",
            where_it_appears=f"Skills lacking proof: {', '.join(unvalidated[:6])}",
            how_to_fix="Add project or experience bullet points demonstrating how you used these skills.",
            action_items=[
                f"Mention '{skill}' inside a project or role bullet point" for skill in unvalidated[:4]
            ] + ["Remove skills you cannot substantiate with actual work"],
            example_improvement=f"Add to a project bullet:\n'Implemented microservices using {unvalidated[0] if unvalidated else 'Docker'} reducing deploy time by 30%.'"
        ))

    # 5. Weak Action Verbs
    description_lines = [
        l.strip() for e in exp_entries for l in e.get('description', '').split('\n') if l.strip()
    ]
    if len(description_lines) > 3 and len(action_verbs) < 3:
        detected.append(IssueDetail(
            issue_title="Bullet Points Lack Strong Action Verbs",
            severity_level="Moderate",
            ats_impact="Medium",
            explanation=f"Only {len(action_verbs)} bullet points start with strong action verbs.",
            where_it_appears="Experience section bullet point openings",
            how_to_fix="Start every bullet point with strong past-tense verbs (e.g. Developed, Led, Engineered, Reduced).",
            action_items=[
                "Replace weak openings like 'Responsible for' or 'Worked on'",
                "Use impact verbs: Developed, Engineered, Optimized, Automated, Built"
            ],
            example_improvement="Before: Responsible for backend development\nAfter: Engineered high-throughput REST APIs using FastAPI"
        ))

    # 6. No Metrics / Quantifiable Achievements
    number_pattern = r'\d+[%+]?|\$\d+'
    has_metrics = bool(re.findall(number_pattern, experience_text)) if experience_text else False
    if experience_text and not has_metrics:
        detected.append(IssueDetail(
            issue_title="No Quantifiable Achievements Found",
            severity_level="Moderate",
            ats_impact="Medium",
            explanation="Your bullet points lack numbers, percentages, or metrics to measure your real impact.",
            where_it_appears="Experience section bullet content",
            how_to_fix="Add metrics (e.g. % performance increase, latency reduced, users served) to at least 50% of bullets.",
            action_items=[
                "Ask yourself: 'How much?', 'How many?', 'By what percentage?' for each achievement",
                "Examples: 'Served 10K+ daily users', 'Improved query performance by 40%'"
            ],
            example_improvement="Before: Improved database performance\nAfter: Reduced SQL query latency by 45% using Redis caching"
        ))

    return detected

def generate_issues_summary(detected_issues: List[IssueDetail]) -> List[str]:
    return [issue.issue_title for issue in detected_issues]
