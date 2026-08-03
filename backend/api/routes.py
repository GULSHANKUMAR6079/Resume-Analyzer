import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response

from backend.api.auth import get_current_user
from backend.models.schemas import AnalysisResponse, ComponentScores, JDComparison, SkillValidationDetails

logger = logging.getLogger('ats_resume_scorer')
router = APIRouter(prefix='/api/v1', tags=['Analysis'])

@router.post('/analyze-resume', response_model=AnalysisResponse)
async def analyze_resume(
    request: Request,
    resume: UploadFile = File(..., description='Resume document — PDF or DOCX, max 5 MB'),
    job_description: str = Form('', description='Optional target job description text'),
    user_id: str = Depends(get_current_user),
):
    nlp = request.app.state.nlp
    embedder = getattr(request.app.state, 'embedder', None)
    if embedder is None:
        try:
            logger.info("Initializing SentenceTransformer embedder on demand...")
            from sentence_transformers import SentenceTransformer
            from backend.core.config import SENTENCE_TRANSFORMER_MODEL
            embedder = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
            request.app.state.embedder = embedder
        except Exception as exc:
            logger.warning(f"Could not load SentenceTransformer ({exc}) — falling back to RapidFuzz fuzzy matching.")
            embedder = None

    # 1. Read and parse document text
    try:
        file_bytes = await resume.read()
        filename = resume.filename or 'resume'

        from backend.services.resume_parser import parse_resume_file
        resume_text, _metadata = parse_resume_file(file_bytes, filename)
        logger.info(f"Successfully extracted '{filename}': {len(resume_text)} characters")

    except Exception as exc:
        logger.error(f"File parsing error: {exc}")
        raise HTTPException(status_code=422, detail=f"Could not read uploaded document: {exc}")

    # 2. Run Groq LLM parsing & Vectorized NLP scoring pipeline
    try:
        from backend.services.groq_parser import parse_resume_async, parse_job_description_async
        from backend.services.ats_scorer import (
            calculate_overall_score,
            detect_location_info,
            validate_skills_with_projects,
        )
        from backend.services.jd_matcher import compare_resume_with_jd
        from backend.services.feedback_engine import analyze_issues, generate_issues_summary

        # Async LLM Parse
        parsed_resume = await parse_resume_async(resume_text)
        skills = parsed_resume.get('skills', [])
        projects = parsed_resume.get('projects', [])
        keywords = parsed_resume.get('keywords', [])
        action_verbs = parsed_resume.get('action_verbs', [])

        experience_months = sum(
            int(e.get('duration_months', 0))
            for e in parsed_resume.get('experience', []) if isinstance(e, dict)
        )

        contact_info = {
            'email': parsed_resume.get('email'),
            'phone': parsed_resume.get('phone'),
            'linkedin': parsed_resume.get('linkedin'),
            'github': parsed_resume.get('github'),
        }

        # Vectorized skill validation
        skill_validation = validate_skills_with_projects(
            skills=skills,
            projects=projects,
            experience_entries=parsed_resume.get('experience', []),
            embedder=embedder,
        )

        # Active spaCy NER Location Detection
        location_results = detect_location_info(resume_text, nlp)
        grammar_results = {'penalty_applied': 0.0, 'total_errors': 0}

        # JD Analysis
        jd_comparison_result = None
        jd_keywords = None
        if job_description and job_description.strip():
            parsed_jd = await parse_job_description_async(job_description.strip())
            jd_keywords = list(set(
                parsed_jd.get('keywords', []) +
                parsed_jd.get('required_skills', []) +
                parsed_jd.get('preferred_skills', [])
            ))
            jd_comp_dict = compare_resume_with_jd(
                resume_text=resume_text,
                resume_keywords=keywords,
                resume_skills=skills,
                jd_text=job_description.strip(),
                jd_keywords=jd_keywords,
                embedder=embedder,
                nlp=nlp,
            )
            jd_comparison_result = JDComparison(
                match_percentage=round(float(jd_comp_dict.get('match_percentage', 0.0)), 1),
                semantic_similarity=round(float(jd_comp_dict.get('semantic_similarity', 0.0)), 3),
                matched_keywords=jd_comp_dict.get('matched_keywords', [])[:20],
                missing_keywords=jd_comp_dict.get('missing_keywords', [])[:15],
                skills_gap=jd_comp_dict.get('skills_gap', [])[:10],
            )

        # Score aggregation
        scores = calculate_overall_score(
            text=resume_text,
            parsed_resume=parsed_resume,
            skills=skills,
            keywords=keywords,
            action_verbs=action_verbs,
            skill_validation_results=skill_validation,
            grammar_results=grammar_results,
            location_results=location_results,
            jd_keywords=jd_keywords,
            experience_months=experience_months,
        )

        detailed_fb = analyze_issues(
            resume_text=resume_text,
            parsed_resume=parsed_resume,
            skills=skills,
            projects=projects,
            action_verbs=action_verbs,
            skill_validation=skill_validation,
            scores=scores,
            contact_info=contact_info,
        )
        issues_summary = generate_issues_summary(detailed_fb)

        svd_raw = skill_validation.get('validated_skills', [])
        unvalidated_raw = skill_validation.get('unvalidated_skills', [])
        total_skills = len(svd_raw) + len(unvalidated_raw)
        val_pct = round((len(svd_raw) / total_skills * 100) if total_skills > 0 else 0, 1)

        skill_val_details = SkillValidationDetails(
            validated=[{'skill': item['skill'], 'projects': item.get('projects', [])} for item in svd_raw],
            unvalidated=unvalidated_raw,
            total=total_skills,
            validated_count=len(svd_raw),
            validation_pct=val_pct,
        )

        response = AnalysisResponse(
            ATS_score=scores['overall_score'],
            ats_score=scores['overall_score'],
            component_scores=ComponentScores(
                formatting=scores['formatting_score'],
                keywords=scores['keywords_score'],
                content=scores['content_score'],
                skill_validation=scores['skill_validation_score'],
                ats_compatibility=scores['ats_compatibility_score'],
            ),
            issues_summary=issues_summary,
            detailed_feedback=detailed_fb,
            jd_match_analysis=jd_comparison_result,
            jd_comparison=jd_comparison_result,
            skill_validation_details=skill_val_details,
            keyword_match=jd_comparison_result.match_percentage if jd_comparison_result else 0.0,
            missing_keywords=jd_comparison_result.missing_keywords if jd_comparison_result else [],
            matched_keywords=jd_comparison_result.matched_keywords if jd_comparison_result else list(keywords[:20]),
            skills=skills[:25],
            strengths=[
                "Dedicated Experience section included",
                "Skills section clearly lists technical stack",
                f"{len(svd_raw)} skills backed by project evidence"
            ],
            interpretation=scores.get('overall_interpretation', ''),
            experience_months=experience_months,
        )

    except Exception as exc:
        logger.error(f"Analysis pipeline execution failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Analysis pipeline error: {exc}")

    # 3. Async DB save (non-blocking)
    try:
        from backend.database.supabase_db import save_analysis
        await save_analysis(user_id, filename, response.model_dump())
    except Exception as exc:
        logger.warning(f"Failed to persist analysis history: {exc}")

    return response

@router.get('/health')
async def health_check(request: Request):
    return {
        'status': 'healthy',
        'nlp_loaded': request.app.state.nlp is not None,
        'embedder_loaded': request.app.state.embedder is not None,
    }

@router.get('/history')
async def get_history(user_id: str = Depends(get_current_user)):
    from backend.database.supabase_db import get_user_history
    try:
        return await get_user_history(user_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not load user history: {exc}")

@router.delete('/history/{analysis_id}')
async def delete_history_entry(analysis_id: str, user_id: str = Depends(get_current_user)):
    from backend.database.supabase_db import delete_analysis
    success = await delete_analysis(analysis_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Analysis history record not found")
    return {'status': 'deleted', 'id': analysis_id}

@router.post('/generate-pdf')
async def generate_pdf(data: AnalysisResponse, user_id: str = Depends(get_current_user)):
    from backend.services.report_generator import generate_html_reports
    from backend.services.pdf_export import generate_combined_pdf
    try:
        html_docs = generate_html_reports(data.model_dump())
        pdf_bytes = generate_combined_pdf(html_docs)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=ats_report.pdf"}
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF report generation failed: {exc}")
