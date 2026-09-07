"""Job Matching Service for evaluating candidate fit against specific job requirements."""

from typing import Any, Dict, List, Optional
from models.score import RecommendedDecision


def normalize(val: str) -> str:
    return " ".join(str(val or "").strip().casefold().split())


def skills_match(left: str, right: str) -> bool:
    """Return True when two normalized skill labels represent the same skill."""
    left_key, right_key = normalize(left), normalize(right)
    if not left_key or not right_key:
        return False
    if left_key == right_key:
        return True
    # Useful for labels such as "React.js"/"React" and "MySQL"/"SQL", while
    # preventing one-letter skills such as C or R from matching arbitrary words.
    return min(len(left_key), len(right_key)) >= 3 and (
        left_key in right_key or right_key in left_key
    )


class JobMatchService:
    @staticmethod
    def calculate_job_match_score(
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any],
        github_data: Optional[Dict[str, Any]] = None,
        candidate_profile_score: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculates independent Job Match Score (out of 100) comparing candidate against specific job requirements.
        Never mixes Job Match Score with Candidate Profile Score.
        """
        job_id = job_data.get("id") or "job_default"
        job_title = job_data.get("title", "Target Role")
        req_skills = [s.strip() for s in str(job_data.get("skills", "")).split(",") if s.strip()]
        req_years = float(job_data.get("experience") or 0.0)

        tech_skills = candidate_data.get("technical_skills") or []
        prog_langs = candidate_data.get("programming_languages") or []
        experiences = candidate_data.get("experience") or []
        projects = candidate_data.get("projects") or []
        education = candidate_data.get("education") or []
        certifications = candidate_data.get("certifications") or []

        candidate_keys = {normalize(s) for s in tech_skills + prog_langs if normalize(s)}
        
        # 1. Job Skills Match (Max 25)
        matched_skills = []
        missing_skills = []
        for req in req_skills:
            req_key = normalize(req)
            if req_key in candidate_keys or any(skills_match(req, skill) for skill in tech_skills + prog_langs):
                matched_skills.append(req)
            else:
                missing_skills.append(req)

        skill_ratio = (len(matched_skills) / len(req_skills)) if req_skills else 1.0
        skills_score = round(skill_ratio * 25.0, 1)

        # 2. Job Experience Relevance (Max 20)
        total_cand_years = candidate_data.get("personal_info", {}).get("experience_years") or sum(e.get("duration_months", 0) for e in experiences) / 12.0
        if req_years > 0:
            exp_ratio = min(1.0, total_cand_years / req_years)
            exp_score = round(exp_ratio * 20.0, 1)
        else:
            exp_score = 20.0 if total_cand_years > 0 else 15.0

        # 3. GitHub Relevance to Job Tech (Max 15)
        detected_github_skills = (github_data or {}).get("detected_skills") or []

        # GitHub is corroborating evidence, not an independent source of job skills.
        # Only a recruiter-required skill already claimed in the candidate profile
        # is eligible to be verified by repository evidence.
        matched_gh = [
            skill for skill in matched_skills
            if any(skills_match(skill, detected) for detected in detected_github_skills)
        ]
        
        if (github_data or {}).get("verification_status") in {"verified", "success"}:
            gh_ratio = (len(matched_gh) / len(matched_skills)) if matched_skills else 0.0
            github_match_score = round(min(1.0, gh_ratio) * 15.0, 1)
        else:
            github_match_score = 0.0

        # 4. Projects Job Relevance (Max 15)
        proj_tech_matches = 0
        for p in projects:
            p_techs = {normalize(t) for t in (p.get("technologies") or [])}
            if any(req_k in p_techs for req_k in [normalize(s) for s in req_skills]):
                proj_tech_matches += 1
        
        proj_score = round(min(1.0, (proj_tech_matches / max(1, len(projects)))) * 15.0, 1) if projects else 0.0

        # 5. Education Job Relevance (Max 10)
        edu_score = 10.0 if education and any("computer" in str(e).lower() or "software" in str(e).lower() or "engineering" in str(e).lower() for e in education) else 6.0 if education else 0.0

        # 6. Programming Languages Job Relevance (Max 5)
        matched_prog_langs = [p for p in prog_langs if any(normalize(p) in normalize(r) or normalize(r) in normalize(p) for r in req_skills)]
        prog_lang_score = round(min(1.0, len(matched_prog_langs) / max(1, len(req_skills))) * 5.0, 1) if req_skills else 5.0

        # 7. Certifications Relevance (Max 5)
        cert_score = 5.0 if certifications else 0.0

        # 8. Profile Quality (Max 5)
        quality_score = 5.0 if candidate_data.get("personal_info", {}).get("email") else 3.0

        score_breakdown = {
            "skills": {"score": skills_score, "max_score": 25.0, "reason": f"Matched {len(matched_skills)} of {len(req_skills)} required skills.", "evidence": matched_skills},
            "experience": {"score": exp_score, "max_score": 20.0, "reason": f"Candidate has {total_cand_years:g} years vs {req_years:g} required years.", "evidence": [f"{total_cand_years:g} years total experience"]},
            "github": {"score": github_match_score, "max_score": 15.0, "reason": f"GitHub verified {len(matched_gh)} required technologies." if matched_gh else "GitHub evidence evaluated.", "evidence": matched_gh},
            "projects": {"score": proj_score, "max_score": 15.0, "reason": f"Evaluated project alignment for {job_title}.", "evidence": [p.get("name") for p in projects[:3]]},
            "education": {"score": edu_score, "max_score": 10.0, "reason": "Relevant academic background evaluated.", "evidence": [e.get("qualification") for e in education[:2]]},
            "languages": {"score": prog_lang_score, "max_score": 5.0, "reason": f"Programming language fit for job.", "evidence": prog_langs},
            "certifications": {"score": cert_score, "max_score": 5.0, "reason": f"{len(certifications)} certifications evaluated.", "evidence": [c.get("name") for c in certifications[:2]]},
            "profile_quality": {"score": quality_score, "max_score": 5.0, "reason": "Profile quality factor.", "evidence": ["Profile data evaluated"]},
        }

        total_match_score = round(sum(item["score"] for item in score_breakdown.values()), 1)

        # Recommendation Decision Matrix
        if total_match_score >= 80.0:
            decision = RecommendedDecision.STRONG_MATCH
        elif total_match_score >= 65.0:
            decision = RecommendedDecision.GOOD_MATCH
        elif total_match_score >= 50.0:
            decision = RecommendedDecision.POSSIBLE_MATCH
        elif total_match_score >= 30.0:
            decision = RecommendedDecision.WEAK_MATCH
        else:
            decision = RecommendedDecision.INSUFFICIENT_EVIDENCE

        # Verified skills vs unverified claims
        verified_skills = matched_gh
        unverified_claims = [skill for skill in matched_skills if skill not in verified_skills]

        strengths = matched_skills[:4] or [f"{total_cand_years:g} years experience"]
        weaknesses = missing_skills[:4] or ["No major skill gaps detected"]
        interview_focus = f"Probe practical experience in {', '.join(unverified_claims[:2])} and evaluate candidate's strategy for {', '.join(missing_skills[:2])}." if unverified_claims or missing_skills else "Conduct technical architectural review of recent projects."

        return {
            "job_id": job_id,
            "job_title": job_title,
            "match_score": total_match_score,
            "recommended_decision": decision.value,
            "score_breakdown": score_breakdown,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "missing_requirements": missing_skills,
            "verified_skills": verified_skills,
            "unverified_claims": unverified_claims,
            "interview_focus": interview_focus,
        }
