import re
import spacy
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Optional, Tuple

ZIP_CODE_PATTERN = r'\b\d{5}(?:-\d{4})?\b'
STREET_ADDRESS_PATTERN = (
    r'\b\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+'
    r'(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Circle|Cir|Way|Place|Pl)\b'
)

def _tier_score(n: float, tiers: list) -> float:
    for threshold, pts in tiers:
        if n >= threshold:
            return pts
    return 0.0

def detect_location_info(text: str, nlp: spacy.Language) -> Dict:
    """Active spaCy NER + regex location detection & privacy risk engine."""
    locations = []

    # 1. spaCy NER GPE (Geopolitical entity) and LOC (Location)
    if nlp:
        doc = nlp(text[:8000])
        for ent in doc.ents:
            if ent.label_ in ['GPE', 'LOC']:
                locations.append({'text': ent.text, 'type': ent.label_.lower(), 'start': ent.start_char})

    # 2. Street address regex
    for match in re.finditer(STREET_ADDRESS_PATTERN, text, re.IGNORECASE):
        locations.append({'text': match.group(), 'type': 'address', 'start': match.start()})

    # 3. Zip code regex
    for match in re.finditer(ZIP_CODE_PATTERN, text):
        locations.append({'text': match.group(), 'type': 'zip', 'start': match.start()})

    has_address = any(loc['type'] == 'address' for loc in locations)
    has_zip = any(loc['type'] == 'zip' for loc in locations)

    if has_address and has_zip:
        privacy_risk, penalty = 'high', 5.0
    elif has_address or has_zip:
        privacy_risk, penalty = 'high', 4.0
    elif len(locations) > 3:
        privacy_risk, penalty = 'medium', 3.0
    elif locations:
        privacy_risk, penalty = 'low', 2.0
    else:
        privacy_risk, penalty = 'none', 0.0

    recommendations = []
    if not locations:
        recommendations.append("No privacy concerns detected.")
    if has_address:
        recommendations.append("Remove full street addresses — ATS systems don't need this and it's a privacy risk.")
    if has_zip:
        recommendations.append("Remove zip codes — this level of location detail is unnecessary.")
    if privacy_risk in ('low', 'medium') and not has_address and not has_zip:
        recommendations.append("Consider keeping only 'City, State' in your contact header.")

    return {
        'location_found': len(locations) > 0,
        'detected_locations': locations,
        'privacy_risk': privacy_risk,
        'recommendations': recommendations,
        'penalty_applied': penalty,
    }

def validate_skills_with_projects(
    skills: List[str],
    projects: List[Dict],
    experience_entries: List[Dict],
    embedder: Optional[SentenceTransformer] = None,
    threshold: float = 0.6,
) -> Dict:
    """Ultra-fast skill validation using SentenceTransformers or rapidfuzz fallback."""
    if not skills:
        return {
            'validated_skills': [],
            'unvalidated_skills': [],
            'validation_percentage': 0.0,
            'skill_project_mapping': {},
            'validation_score': 0.0,
        }

    # Build section texts list
    texts = []
    text_labels = []

    for proj in projects:
        if isinstance(proj, dict):
            p_text = f"{proj.get('title', '')} {proj.get('description', '')}".strip()
            if p_text:
                texts.append(p_text)
                text_labels.append(proj.get('title', 'Project Entry'))

    exp_text = ' '.join(
        f"{e.get('job_title', '')} {e.get('company', '')} {e.get('description', '')}"
        for e in experience_entries if isinstance(e, dict)
    ).strip()

    if exp_text:
        texts.append(exp_text)
        text_labels.append('Experience Section')

    if not texts:
        return {
            'validated_skills': [],
            'unvalidated_skills': skills,
            'validation_percentage': 0.0,
            'skill_project_mapping': {s: [] for s in skills},
            'validation_score': 0.0,
        }

    validated_skills = []
    unvalidated_skills = []
    skill_project_mapping = {}

    # 1. If embedder is active, try matrix similarity
    sim_matrix = None
    if embedder is not None:
        try:
            skill_vecs = embedder.encode(skills, convert_to_tensor=False, show_progress_bar=False)
            text_vecs = embedder.encode(texts, convert_to_tensor=False, show_progress_bar=False)

            skill_vecs = np.atleast_2d(skill_vecs)
            text_vecs = np.atleast_2d(text_vecs)

            skill_norms = np.linalg.norm(skill_vecs, axis=1, keepdims=True) + 1e-9
            text_norms = np.linalg.norm(text_vecs, axis=1, keepdims=True) + 1e-9

            sim_matrix = np.dot(skill_vecs / skill_norms, (text_vecs / text_norms).T)
            sim_matrix = np.clip(sim_matrix, 0.0, 1.0)
        except Exception:
            sim_matrix = None

    # 2. Match skills using vector matrix or RapidFuzz string match
    from rapidfuzz import fuzz

    for idx, skill in enumerate(skills):
        matching_labels = []
        max_sim = 0.0
        skill_lower = skill.lower()

        for text_idx, label in enumerate(text_labels):
            t_lower = texts[text_idx].lower()
            sim_score = float(sim_matrix[idx, text_idx]) if sim_matrix is not None else 0.0

            if skill_lower in t_lower:
                matching_labels.append(label)
                max_sim = 1.0
            elif sim_matrix is not None and sim_score >= threshold:
                matching_labels.append(label)
                max_sim = max(max_sim, sim_score)
            elif sim_matrix is None and fuzz.partial_ratio(skill_lower, t_lower) >= 75:
                matching_labels.append(label)
                max_sim = 0.8

        if matching_labels:
            unique_labels = list(set(matching_labels))
            validated_skills.append({
                'skill': skill,
                'projects': unique_labels,
                'similarity': max_sim
            })
            skill_project_mapping[skill] = unique_labels
        else:
            unvalidated_skills.append(skill)
            skill_project_mapping[skill] = []

    val_pct = len(validated_skills) / len(skills) if skills else 0.0
    val_score = val_pct * 15.0

    return {
        'validated_skills': validated_skills,
        'unvalidated_skills': unvalidated_skills,
        'validation_percentage': val_pct,
        'skill_project_mapping': skill_project_mapping,
        'validation_score': val_score,
    }

def _calc_formatting_score(parsed_resume: Dict, text: str) -> float:
    score = 0.0
    exp_entries = [e for e in parsed_resume.get('experience', []) if isinstance(e, dict)]
    edu_entries = [e for e in parsed_resume.get('education', []) if isinstance(e, dict)]
    skills = parsed_resume.get('skills', [])
    summary = parsed_resume.get('professional_summary', '')
    proj_entries = [p for p in parsed_resume.get('projects', []) if isinstance(p, dict)]

    if exp_entries and any(e.get('job_title') or e.get('description') for e in exp_entries):
        score += 3.0
    if edu_entries:
        score += 2.0
    if len(skills) >= 3:
        score += 2.0
    if len(summary) > 30:
        score += 1.5
    if proj_entries:
        score += 1.5

    bullet_count = sum(
        1 for line in text.split('\n')
        if re.match(r'^\s*[•\-\*\◦]', line) or re.match(r'^\s*\d+\.', line)
    )
    score += _tier_score(bullet_count, [(15, 5.0), (10, 4.0), (5, 3.0), (3, 2.0), (1, 1.0)])

    filled = sum(1 for has_it in [
        bool(exp_entries), bool(edu_entries), bool(skills),
        bool(summary.strip()), bool(proj_entries),
    ] if has_it)
    score += _tier_score(filled, [(4, 5.0), (3, 4.0), (2, 3.0), (1, 2.0)])

    return min(20.0, max(0.0, score))

def _calc_keywords_score(
    resume_keywords: List[str],
    skills: List[str],
    jd_keywords: Optional[List[str]] = None,
) -> float:
    score = 0.0
    score += _tier_score(len(resume_keywords), [(20, 10.0), (15, 8.0), (10, 6.0), (5, 4.0), (3, 2.0)])
    score += _tier_score(len(skills), [(15, 10.0), (10, 8.0), (7, 6.0), (5, 4.0), (3, 2.0)])

    if jd_keywords:
        from backend.services.jd_matcher import fuzzy_match_keywords
        all_terms = list(set(resume_keywords + skills))
        fuzzy_res = fuzzy_match_keywords(all_terms, jd_keywords, threshold=80)
        match_pct = len(fuzzy_res['matched']) / len(jd_keywords) if jd_keywords else 0
        score += _tier_score(match_pct, [(0.7, 5.0), (0.5, 4.0), (0.3, 3.0), (0.2, 2.0), (0.1, 1.0)])
    elif len(resume_keywords) >= 10:
        score += 3.0

    return min(25.0, max(0.0, score))

def _calc_content_score(
    text: str,
    action_verbs: List[str],
    grammar_results: Dict,
) -> float:
    score = 0.0
    score += _tier_score(len(action_verbs), [(15, 10.0), (10, 8.0), (7, 6.0), (5, 4.0), (3, 2.0)])

    number_patterns = [
        r'\d+%', r'\$\d+', r'\d+[kKmMbB]',
        r'\d+\s*(?:users|customers|clients|projects|hours|days|months|years)',
        r'(?:increased|decreased|improved|reduced|grew|saved)\s+(?:by\s+)?\d+',
    ]
    achievement_count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in number_patterns)
    score += _tier_score(achievement_count, [(10, 5.0), (7, 4.0), (5, 3.0), (3, 2.0), (1, 1.0)])

    grammar_penalty = grammar_results.get('penalty_applied', 0.0)
    score += max(0.0, 10.0 - grammar_penalty / 2.0)

    return min(25.0, max(0.0, score))

def _calc_ats_compatibility_score(
    text: str,
    location_results: Dict,
    parsed_resume: Dict,
) -> float:
    score = 15.0
    score -= location_results.get('penalty_applied', 0.0)

    special_chars = len(re.findall(r'[│┤├┼┴┬╔╗╚╝═║╠╣╦╩╬]', text))
    if special_chars > 20: score -= 2.0
    elif special_chars > 10: score -= 1.0

    exp_entries = [e for e in parsed_resume.get('experience', []) if isinstance(e, dict)]
    edu_entries = [e for e in parsed_resume.get('education', []) if isinstance(e, dict)]
    skills_count = len(parsed_resume.get('skills', []))

    exp_desc_len = sum(len(e.get('description', '')) for e in exp_entries)
    edu_desc_len = sum(len((e.get('degree') or '') + (e.get('institution') or '')) for e in edu_entries)

    short_sections = sum([
        bool(exp_entries) and exp_desc_len < 20,
        bool(edu_entries) and edu_desc_len < 20,
        bool(parsed_resume.get('skills')) and skills_count < 2,
    ])
    if short_sections >= 2: score -= 2.0
    elif short_sections >= 1: score -= 1.0

    if exp_entries and skills_count > 5:
        score += 1.0

    return min(15.0, max(0.0, score))

def calculate_overall_score(
    text: str,
    parsed_resume: Dict,
    skills: List[str],
    keywords: List[str],
    action_verbs: List[str],
    skill_validation_results: Dict,
    grammar_results: Dict,
    location_results: Dict,
    jd_keywords: Optional[List[str]] = None,
    experience_months: int = 0,
) -> Dict:

    formatting_score = _calc_formatting_score(parsed_resume, text)
    keywords_score = _calc_keywords_score(keywords, skills, jd_keywords)
    content_score = _calc_content_score(text, action_verbs, grammar_results)
    skill_validation_score = min(15.0, max(0.0, skill_validation_results.get('validation_score', 0.0)))
    ats_compatibility_score = _calc_ats_compatibility_score(text, location_results, parsed_resume)

    formatting_pct = (formatting_score / 20.0) * 100.0
    keywords_pct = (keywords_score / 25.0) * 100.0
    content_pct = (content_score / 25.0) * 100.0
    skill_validation_pct = (skill_validation_score / 15.0) * 100.0
    ats_compatibility_pct = (ats_compatibility_score / 15.0) * 100.0

    skills_keywords_pct = (keywords_pct * 0.6) + (skill_validation_pct * 0.4)
    base_score = (
        skills_keywords_pct * 0.40 +
        content_pct * 0.30 +
        formatting_pct * 0.15 +
        ats_compatibility_pct * 0.15
    )

    penalties = {}
    bonuses = {}
    score = base_score

    if grammar_results.get('penalty_applied', 0.0) > 0:
        penalties['grammar'] = grammar_results['penalty_applied']
    if location_results.get('penalty_applied', 0.0) > 0:
        penalties['location_privacy'] = location_results['penalty_applied']

    val_pct = skill_validation_results.get('validation_percentage', 0.0)
    if val_pct >= 0.9:
        bonuses['excellent_skill_validation'] = 2.0
        score += 2.0
    elif val_pct >= 0.8:
        bonuses['good_skill_validation'] = 1.0
        score += 1.0

    overall_score = min(100.0, max(0.0, score))
    interpretation = _generate_score_interpretation(overall_score)

    return {
        'overall_score': round(overall_score, 1),
        'formatting_score': round(formatting_score, 1),
        'keywords_score': round(keywords_score, 1),
        'content_score': round(content_score, 1),
        'skill_validation_score': round(skill_validation_score, 1),
        'ats_compatibility_score': round(ats_compatibility_score, 1),
        'overall_interpretation': interpretation,
        'penalties': penalties,
        'bonuses': bonuses,
    }

def _generate_score_interpretation(score: float) -> str:
    if score >= 90: return 'Excellent! Your resume is highly optimized for ATS filters.'
    elif score >= 80: return 'Great! Your resume will perform strongly with most ATS systems.'
    elif score >= 70: return 'Good! Your resume is ATS-friendly with minor optimization opportunities.'
    elif score >= 60: return 'Fair. Revisions are needed to ensure robust ATS compatibility.'
    elif score >= 50: return 'Below Average. Key section and keyword improvements required.'
    else: return 'Poor. Major revisions needed to pass automated ATS screening.'
