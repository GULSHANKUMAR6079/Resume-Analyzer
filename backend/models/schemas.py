from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class ComponentScores(BaseModel):
    formatting: float = Field(..., description="Formatting score out of 20")
    keywords: float = Field(..., description="Keywords score out of 25")
    content: float = Field(..., description="Content quality score out of 25")
    skill_validation: float = Field(..., description="Skill validation score out of 15")
    ats_compatibility: float = Field(..., description="ATS compatibility score out of 15")

class ValidatedSkillItem(BaseModel):
    skill: str
    projects: List[str] = Field(default_factory=list)
    similarity: float = 0.0

class SkillValidationDetails(BaseModel):
    validated: List[Dict] = Field(default_factory=list)
    unvalidated: List[str] = Field(default_factory=list)
    total: int = 0
    validated_count: int = 0
    validation_pct: float = 0.0

class JDComparison(BaseModel):
    match_percentage: float = 0.0
    semantic_similarity: float = 0.0
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    skills_gap: List[str] = Field(default_factory=list)

class IssueDetail(BaseModel):
    issue_title: str
    severity_level: str  # High, Moderate, Low
    ats_impact: str      # High, Medium, Low
    explanation: str
    where_it_appears: str
    how_to_fix: str
    action_items: List[str] = Field(default_factory=list)
    example_improvement: Optional[str] = None

class AnalysisResponse(BaseModel):
    ATS_score: float = Field(..., description="Overall ATS Compatibility score out of 100")
    ats_score: float = Field(..., description="Retro-compatibility overall score")
    component_scores: ComponentScores
    issues_summary: List[str] = Field(default_factory=list)
    detailed_feedback: List[IssueDetail] = Field(default_factory=list)
    jd_match_analysis: Optional[JDComparison] = None
    jd_comparison: Optional[JDComparison] = None
    skill_validation_details: SkillValidationDetails
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    interpretation: str = ""
    keyword_match: float = 0.0
    experience_months: int = 0
