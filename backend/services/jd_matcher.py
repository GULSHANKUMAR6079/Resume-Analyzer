from typing import List, Dict
import numpy as np
import spacy
from sentence_transformers import SentenceTransformer
from rapidfuzz import fuzz

def normalize_skill(skill: str) -> str:
    return skill.lower().replace('-', '').replace('.', '').strip()

def fuzzy_match_keywords(resume_terms: List[str], jd_terms: List[str], threshold: int = 80) -> Dict:
    matched = []
    missing = []
    resume_norm = {normalize_skill(t) for t in resume_terms}

    for jd_term in jd_terms:
        jd_norm = normalize_skill(jd_term)
        if jd_norm in resume_norm:
            matched.append(jd_term)
            continue

        best_score = max(
            (fuzz.token_sort_ratio(jd_norm, r_norm) for r_norm in resume_norm),
            default=0
        )
        if best_score >= threshold:
            matched.append(jd_term)
        else:
            missing.append(jd_term)

    return {'matched': matched, 'missing': missing}

def calculate_semantic_similarity(
    resume_text: str, jd_text: str, embedder: Optional[SentenceTransformer] = None
) -> float:
    if not resume_text or not jd_text:
        return 0.0
    if embedder is not None:
        try:
            resume_emb = embedder.encode(resume_text[:5000], convert_to_tensor=False)
            jd_emb = embedder.encode(jd_text[:5000], convert_to_tensor=False)
            sim = np.dot(resume_emb, jd_emb) / (np.linalg.norm(resume_emb) * np.linalg.norm(jd_emb))
            return float(np.clip(sim, 0.0, 1.0))
        except Exception:
            pass
    # Fast lightweight RapidFuzz fallback (0 MB RAM overhead)
    from rapidfuzz import fuzz
    ratio = fuzz.token_set_ratio(resume_text[:3000].lower(), jd_text[:3000].lower())
    return float(np.clip(ratio / 100.0, 0.0, 1.0))

def analyze_skills_gap(
    resume_skills: List[str], jd_text: str, nlp: spacy.Language
) -> List[str]:
    if not jd_text or not nlp:
        return []
    doc = nlp(jd_text[:5000])
    jd_skills = set()

    for ent in doc.ents:
        if ent.label_ in ['PRODUCT', 'ORG', 'LANGUAGE']:
            jd_skills.add(ent.text.lower())

    for chunk in doc.noun_chunks:
        ct = chunk.text.lower().strip()
        if 1 <= len(ct.split()) <= 3:
            jd_skills.add(ct)

    resume_norm = {normalize_skill(s) for s in resume_skills}
    gap = []
    for jd_skill in jd_skills:
        j_norm = normalize_skill(jd_skill)
        if j_norm in resume_norm:
            continue
        best_score = max((fuzz.token_sort_ratio(j_norm, rs) for rs in resume_norm), default=0)
        if best_score < 75:
            gap.append(jd_skill)

    return sorted(gap)[:15]

def compare_resume_with_jd(
    resume_text: str,
    resume_keywords: List[str],
    resume_skills: List[str],
    jd_text: str,
    jd_keywords: List[str],
    embedder: Optional[SentenceTransformer] = None,
    nlp: Optional[spacy.Language] = None,
) -> Dict:
    semantic_sim = calculate_semantic_similarity(resume_text, jd_text, embedder)
    fuzzy_res = fuzzy_match_keywords(resume_keywords + resume_skills, jd_keywords)
    matched_kws = fuzzy_res['matched']
    missing_kws = fuzzy_res['missing']
    skills_gap = analyze_skills_gap(resume_skills, jd_text, nlp)

    match_pct = 0.0
    if jd_keywords:
        kw_overlap = len(matched_kws) / len(jd_keywords)
        match_pct = (kw_overlap * 0.6 + semantic_sim * 0.4) * 100.0

    return {
        'match_percentage': float(np.clip(match_pct, 0.0, 100.0)),
        'semantic_similarity': semantic_sim,
        'matched_keywords': matched_kws[:20],
        'missing_keywords': missing_kws[:15],
        'skills_gap': skills_gap,
    }
