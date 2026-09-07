"""Deterministic Backend Candidate Profile Scoring Service."""

import re
from typing import Any, Dict, List, Optional
from models.score import EvidenceLevel


def _clamp(val: float, maximum: float) -> float:
    return round(max(0.0, min(float(val), float(maximum))), 1)


class ScoringService:
    @staticmethod
    def evaluate_skills(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluates Skills Match (Max 25)."""
        tech_skills = candidate_data.get("technical_skills") or []
        soft_skills = candidate_data.get("soft_skills") or []
        all_skills = list(dict.fromkeys(tech_skills + soft_skills))
        
        # Technical skill breadth & depth (up to 18 pts)
        tech_pts = min(18.0, len(tech_skills) * 2.5)
        # Soft skill evidence (up to 7 pts)
        soft_pts = min(7.0, len(soft_skills) * 2.0)

        total = _clamp(tech_pts + soft_pts, 25.0)
        level = EvidenceLevel.STRONG if total >= 20 else EvidenceLevel.MODERATE if total >= 12 else EvidenceLevel.WEAK

        return {
            "score": total,
            "max_score": 25.0,
            "reason": f"Evaluated from {len(tech_skills)} technical skills and {len(soft_skills)} soft skills.",
            "evidence": [f"Technical Skills: {', '.join(tech_skills[:6])}" if tech_skills else "No technical skills",
                         f"Soft Skills: {', '.join(soft_skills[:4])}" if soft_skills else "No soft skills"],
            "evidence_level": level,
            "confidence": 0.9,
        }

    @staticmethod
    def evaluate_experience(experiences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluates Experience (Max 20):
        - Relevant years of experience: 6
        - Role relevance / responsibility: 5
        - Responsibility level: 3
        - Technology relevance: 3
        - Achievements / business impact: 2
        - Career progression: 1
        """
        if not experiences:
            return {
                "score": 0.0,
                "max_score": 20.0,
                "reason": "No work experience entries provided.",
                "evidence": ["No work experience entries"],
                "evidence_level": EvidenceLevel.UNVERIFIED,
                "confidence": 0.7,
            }

        total_months = sum(e.get("duration_months") or 0 for e in experiences)
        years = round(total_months / 12.0, 1)

        # 1. Years of experience (Max 6)
        years_score = min(6.0, years * 1.2)

        # 2. Role relevance & senior level (Max 5)
        has_senior = any(any(kw in str(e.get("role", "")).lower() for kw in ["senior", "lead", "architect", "manager", "head"]) for e in experiences)
        role_score = 5.0 if has_senior else 4.0 if len(experiences) >= 2 else 3.0

        # 3. Responsibility level (Max 3)
        resps = [r for e in experiences for r in (e.get("responsibilities") or [])]
        resp_score = min(3.0, len(resps) * 0.5)

        # 4. Technology relevance (Max 3)
        techs = [t for e in experiences for t in (e.get("skills_used") or e.get("technologies") or [])]
        tech_score = min(3.0, len(techs) * 0.6)

        # 5. Achievements / business impact (Max 2)
        achieves = [a for e in experiences for a in (e.get("achievements") or [])]
        achieve_score = min(2.0, len(achieves) * 1.0)

        # 6. Career progression (Max 1)
        progression_score = 1.0 if len(experiences) >= 2 else 0.5

        total = _clamp(years_score + role_score + resp_score + tech_score + achieve_score + progression_score, 20.0)
        level = EvidenceLevel.STRONG if (resps and achieves) else EvidenceLevel.MODERATE if resps else EvidenceLevel.WEAK

        return {
            "score": total,
            "max_score": 20.0,
            "reason": f"Evaluated from {years} years of professional experience across {len(experiences)} roles.",
            "evidence": [
                f"{years} total years of experience across {len(experiences)} positions",
                f"Responsibilities documented: {len(resps)} items",
                f"Achievements/impact documented: {len(achieves)} items"
            ],
            "evidence_level": level,
            "confidence": 0.88,
        }

    @staticmethod
    def evaluate_projects(projects: List[Dict[str, Any]], github_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Evaluates Projects (Max 15):
        - Job/professional relevance: 5
        - Technical complexity: 3
        - Evidence of real implementation: 2
        - Technology relevance: 2
        - GitHub verification: 2
        - Results / business impact: 1
        """
        if not projects:
            return {
                "score": 0.0,
                "max_score": 15.0,
                "reason": "No projects listed in candidate profile.",
                "evidence": ["No project records"],
                "evidence_level": EvidenceLevel.UNVERIFIED,
                "confidence": 0.7,
            }

        # Check for GitHub verified projects
        github_repos = (github_data or {}).get("repositories") or []
        github_repo_names = {str(r.get("repository_name") or r.get("name")).lower() for r in github_repos}

        verified_projects = 0
        total_relevance = 0.0
        total_complexity = 0.0
        total_techs = 0

        for p in projects:
            p_name = str(p.get("name", "")).lower()
            p_techs = p.get("technologies") or []
            total_techs += len(p_techs)
            
            # Link project with GitHub repos if matching name or technologies exist
            if p_name in github_repo_names or any(r for r in github_repos if any(t.lower() in [x.lower() for x in r.get("technologies_detected", [])] for t in p_techs)):
                verified_projects += 1
                p["github_verified"] = True

        relevance_score = min(5.0, len(projects) * 2.5)
        complexity_score = min(3.0, total_techs * 0.5)
        implementation_score = min(2.0, len(projects) * 1.0)
        tech_relevance_score = min(2.0, total_techs * 0.5)
        github_link_score = min(2.0, verified_projects * 1.0)
        impact_score = min(1.0, sum(len(p.get("achievements") or []) for p in projects) * 0.5)

        total = _clamp(relevance_score + complexity_score + implementation_score + tech_relevance_score + github_link_score + impact_score, 15.0)
        level = EvidenceLevel.VERIFIED if verified_projects > 0 else EvidenceLevel.STRONG if total_techs >= 3 else EvidenceLevel.MODERATE

        return {
            "score": total,
            "max_score": 15.0,
            "reason": f"Evaluated from {len(projects)} technical projects ({verified_projects} GitHub-verified).",
            "evidence": [
                f"{len(projects)} projects evaluated with {total_techs} technologies used",
                f"{verified_projects} projects verified against GitHub repositories" if verified_projects else "Projects listed in CV/profile"
            ],
            "evidence_level": level,
            "confidence": 0.9 if verified_projects else 0.8,
        }

    @staticmethod
    def evaluate_education(education_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluates Education (Max 10):
        - Relevant degree: 5
        - Degree level: 2
        - Relevant subjects: 1
        - Relevant institution / training: 1
        - Additional education: 1
        """
        if not education_list:
            return {
                "score": 0.0,
                "max_score": 10.0,
                "reason": "No education credentials listed.",
                "evidence": ["No education records"],
                "evidence_level": EvidenceLevel.UNVERIFIED,
                "confidence": 0.7,
            }

        highest_degree_score = 0.0
        degree_level_score = 0.0
        has_tech_field = False
        institution_score = 0.0
        subjects_score = 0.0

        for edu in education_list:
            deg = str(edu.get("qualification") or edu.get("degree") or "").lower()
            field = str(edu.get("field") or "").lower()
            inst = str(edu.get("institution") or "")

            if any(kw in deg or kw in field for kw in ["computer", "software", "engineering", "information", "data", "science", "math", "technology", "b.sc", "b.tech", "m.sc", "m.tech", "phd"]):
                highest_degree_score = max(highest_degree_score, 5.0)
                has_tech_field = True
            elif deg:
                highest_degree_score = max(highest_degree_score, 3.5)

            if "master" in deg or "m.sc" in deg or "m.tech" in deg or "mba" in deg:
                degree_level_score = max(degree_level_score, 2.0)
            elif "bachelor" in deg or "b.sc" in deg or "b.tech" in deg or "degree" in deg:
                degree_level_score = max(degree_level_score, 1.5)
            elif deg:
                degree_level_score = max(degree_level_score, 1.0)

            if inst:
                institution_score = 1.0
            if edu.get("relevant_subjects") or field:
                subjects_score = 1.0

        additional_edu_score = 1.0 if len(education_list) >= 2 else 0.5

        total = _clamp(highest_degree_score + degree_level_score + subjects_score + institution_score + additional_edu_score, 10.0)
        level = EvidenceLevel.STRONG if has_tech_field else EvidenceLevel.MODERATE

        return {
            "score": total,
            "max_score": 10.0,
            "reason": f"Evaluated from {len(education_list)} educational qualifications.",
            "evidence": [f"{edu.get('qualification') or edu.get('degree') or 'Degree'} at {edu.get('institution') or 'University'}" for edu in education_list[:2]],
            "evidence_level": level,
            "confidence": 0.85,
        }

    @staticmethod
    def evaluate_languages(prog_langs: List[str], human_langs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluates Languages (Max 5):
        - Programming languages (3 pts)
        - Human languages (2 pts)
        """
        prog_pts = min(3.0, len(prog_langs) * 1.0)
        human_pts = min(2.0, len(human_langs) * 1.0)

        total = _clamp(prog_pts + human_pts, 5.0)

        return {
            "score": total,
            "max_score": 5.0,
            "reason": f"Evaluated from {len(prog_langs)} programming languages and {len(human_langs)} human languages.",
            "evidence": [
                f"Programming Languages: {', '.join(prog_langs)}" if prog_langs else "No programming languages listed",
                f"Human Languages: {', '.join([h.get('language', '') for h in human_langs if isinstance(h, dict)])}" if human_langs else "No human languages listed"
            ],
            "evidence_level": EvidenceLevel.STRONG if prog_langs else EvidenceLevel.MODERATE,
            "confidence": 0.9,
        }

    @staticmethod
    def evaluate_certifications(certifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluates Certifications / Training (Max 5)."""
        if not certifications:
            return {
                "score": 0.0,
                "max_score": 5.0,
                "reason": "No professional certifications or training records provided.",
                "evidence": ["No certifications listed"],
                "evidence_level": EvidenceLevel.UNVERIFIED,
                "confidence": 0.7,
            }

        verified_count = sum(1 for c in certifications if c.get("credential_url") or c.get("credential_id") or c.get("verification_status") == "verified")
        cert_pts = min(5.0, len(certifications) * 2.0 + verified_count * 1.0)

        total = _clamp(cert_pts, 5.0)
        level = EvidenceLevel.VERIFIED if verified_count > 0 else EvidenceLevel.STRONG if certifications else EvidenceLevel.UNVERIFIED

        return {
            "score": total,
            "max_score": 5.0,
            "reason": f"Evaluated from {len(certifications)} professional certifications ({verified_count} verified credentials).",
            "evidence": [f"{c.get('name')} (Issuer: {c.get('issuer', 'N/A')})" for c in certifications[:3]],
            "evidence_level": level,
            "confidence": 0.9 if verified_count else 0.8,
        }

    @staticmethod
    def evaluate_profile_quality(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates Profile Quality / Professional Evidence (Max 5):
        - Profile completeness
        - Consistency of information
        - Evidence coverage
        - Professional summary quality
        - Availability of verifiable links
        """
        personal = candidate_data.get("personal_info") or {}
        social = candidate_data.get("social_links") or {}
        summary = personal.get("professional_summary") or personal.get("bio") or candidate_data.get("professional_summary") or ""

        # 1. Profile completeness (1.5)
        has_name = bool(personal.get("full_name"))
        has_contact = bool(personal.get("email") or personal.get("phone"))
        has_loc = bool(personal.get("location"))
        completeness_pts = (0.5 if has_name else 0) + (0.5 if has_contact else 0) + (0.5 if has_loc else 0)

        # 2. Verifiable links (1.5)
        links_count = sum(1 for url in [social.get("linkedin_url"), social.get("github_url"), social.get("portfolio_url")] if url)
        links_pts = min(1.5, links_count * 0.5)

        # 3. Professional summary quality (1.0)
        summary_pts = 1.0 if len(summary.split()) >= 15 else 0.5 if summary else 0.0

        # 4. Consistency & evidence coverage (1.0)
        has_tech = bool(candidate_data.get("technical_skills"))
        has_exp = bool(candidate_data.get("experience"))
        coverage_pts = 1.0 if (has_tech and has_exp) else 0.5

        total = _clamp(completeness_pts + links_pts + summary_pts + coverage_pts, 5.0)

        return {
            "score": total,
            "max_score": 5.0,
            "reason": f"Profile completeness quality score ({total}/5 points).",
            "evidence": [
                f"Contact & location details: {'Complete' if has_contact else 'Incomplete'}",
                f"Verifiable professional links: {links_count} provided",
                f"Professional summary: {len(summary.split())} words"
            ],
            "evidence_level": EvidenceLevel.STRONG if total >= 4.0 else EvidenceLevel.MODERATE,
            "confidence": 0.95,
        }

    def calculate_candidate_profile_score(self, candidate_data: Dict[str, Any], github_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculates standalone Candidate Profile Score (out of 100).
        Includes 8 deterministic category scores with exact breakdown out of max weights:
        - Skills: 25
        - Experience: 20
        - GitHub Evidence: 15
        - Projects: 15
        - Education: 10
        - Languages: 5
        - Certifications: 5
        - Profile Quality: 5
        Total = 100
        """
        skills_eval = self.evaluate_skills(candidate_data)
        exp_eval = self.evaluate_experience(candidate_data.get("experience") or [])
        
        # GitHub evaluation from GitHub Service or github_data
        if github_data and "github_score" in github_data:
            gh_details = github_data["github_score"]
            github_eval = {
                "score": gh_details.get("score", 0.0),
                "max_score": 15.0,
                "reason": gh_details.get("reason", "Evaluated from GitHub API evidence."),
                "evidence": gh_details.get("evidence", []),
                "evidence_level": EvidenceLevel.VERIFIED if gh_details.get("score", 0) > 0 else EvidenceLevel.UNVERIFIED,
                "confidence": 0.92,
            }
        else:
            github_eval = {
                "score": 0.0,
                "max_score": 15.0,
                "reason": "No verified GitHub profile linked.",
                "evidence": ["No GitHub profile linked"],
                "evidence_level": EvidenceLevel.UNVERIFIED,
                "confidence": 0.7,
            }

        proj_eval = self.evaluate_projects(candidate_data.get("projects") or [], github_data)
        edu_eval = self.evaluate_education(candidate_data.get("education") or [])
        lang_eval = self.evaluate_languages(candidate_data.get("programming_languages") or [], candidate_data.get("human_languages") or [])
        cert_eval = self.evaluate_certifications(candidate_data.get("certifications") or [])
        quality_eval = self.evaluate_profile_quality(candidate_data)

        breakdown = {
            "skills": skills_eval,
            "experience": exp_eval,
            "github": github_eval,
            "projects": proj_eval,
            "education": edu_eval,
            "languages": lang_eval,
            "certifications": cert_eval,
            "profile_quality": quality_eval,
        }

        overall_score = round(sum(item["score"] for item in breakdown.values()), 1)

        return {
            "overall_score": overall_score,
            "score_breakdown": breakdown,
        }
