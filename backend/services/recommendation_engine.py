from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

class Priority(Enum):
    CRITICAL = 'critical'
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'

@dataclass
class Recommendation:
    title: str
    description: str
    priority: Priority
    impact_score: float
    category: str
    action_items: List[str]

def generate_all_recommendations(
    skill_validation_results: Dict,
    grammar_results: Dict,
    location_results: Dict,
    score_results: Dict,
    sections: Dict[str, str],
    keyword_analysis: Optional[Dict] = None,
    resume_keywords: Optional[List[str]] = None,
) -> Dict:
    all_recs = []

    # 1. Skill Validation Recs
    unvalidated = skill_validation_results.get('unvalidated_skills', [])
    val_pct = skill_validation_results.get('validation_percentage', 0.0)
    if unvalidated:
        priority = Priority.CRITICAL if val_pct < 0.5 else Priority.HIGH
        all_recs.append(Recommendation(
            title="Validate Listed Technical Skills",
            description=f"{len(unvalidated)} skills lack project or work experience proof.",
            priority=priority,
            impact_score=7.0 if val_pct < 0.5 else 5.0,
            category="skill_validation",
            action_items=[f"Add project proof for '{s}'" for s in unvalidated[:4]]
        ))

    # 2. Location Privacy Recs
    if location_results.get('privacy_risk') == 'high':
        all_recs.append(Recommendation(
            title="Protect Contact Location Privacy",
            description="Full street address or zip code detected. Unnecessary detail for ATS systems.",
            priority=Priority.HIGH,
            impact_score=4.0,
            category="location",
            action_items=["Remove street address and zip code; keep only 'City, State'"]
        ))

    # 3. Keyword Match Recs
    if keyword_analysis:
        missing = keyword_analysis.get('missing_keywords', [])
        match_pct = keyword_analysis.get('match_percentage', 0.0)
        if missing:
            prio = Priority.CRITICAL if match_pct < 50 else Priority.HIGH
            all_recs.append(Recommendation(
                title="Include Missing Job Description Keywords",
                description=f"{len(missing)} target keywords missing. Current match score is {match_pct:.0f}%.",
                priority=prio,
                impact_score=8.0 if match_pct < 50 else 6.0,
                category="keywords",
                action_items=[f"Incorporate '{kw}' into experience bullets" for kw in missing[:5]]
            ))

    prioritized = sorted(all_recs, key=lambda r: r.impact_score, reverse=True)
    return {
        'all_recommendations': prioritized,
        'total_count': len(prioritized),
        'estimated_improvement': min(30.0, sum(r.impact_score for r in prioritized)),
    }
