"""CV Extraction and Complete Candidate Intelligence Analysis Service."""

import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from gemini_rest import generate_json as generate_gemini_json
from repositories.candidate_repository import CandidateRepository
from repositories.analysis_repository import AnalysisRepository
from repositories.github_repository import GithubRepository
from services.github_service import GithubService
from services.scoring_service import ScoringService


def utcnow():
    return datetime.now(timezone.utc)


def identifier():
    return str(uuid.uuid4())


COMMON_PROGRAMMING_LANGUAGES = {
    "python", "java", "javascript", "typescript", "c", "c++", "c#", "go", "golang", "rust",
    "swift", "kotlin", "php", "ruby", "sql", "html", "css", "bash", "shell", "r", "scala",
    "dart", "perl", "haskell", "lua", "matlab", "powershell", "assembly"
}


class CvAnalysisService:
    def __init__(
        self,
        candidate_repo: CandidateRepository,
        analysis_repo: AnalysisRepository,
        github_service: GithubService,
        api_key: str = "",
        model_name: str = "gemini-3.5-flash-lite"
    ):
        self.candidate_repo = candidate_repo
        self.analysis_repo = analysis_repo
        self.github_service = github_service
        self.scoring_service = ScoringService()
        self.api_key = api_key
        self.model_name = model_name

    async def analyze_and_store_cv(
        self,
        user_id: str,
        cv_text: str,
        file_name: str = "",
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract, normalize, verify, score, and permanently store candidate profile."""
        doc_id = document_id or identifier()
        
        prompt = f"""
Extract complete, factual professional information from this CV. Never invent missing details.
Explicitly separate programming_languages (e.g. Python, Java, JavaScript, TypeScript, SQL, HTML, CSS) from human_languages (e.g. English, Tamil, Sinhala, Spanish, French).

Return valid JSON with no markdown:
{{
    "personal_info": {{
        "full_name": "Name",
        "email": "Email",
        "phone": "Phone",
        "location": "City, Country",
        "headline": "Title",
        "bio": "Professional Summary",
        "experience_years": 3.5
    }},
    "professional_summary": "Factual professional summary",
    "programming_languages": ["Python", "JavaScript", "SQL"],
    "human_languages": [
        {{"language": "English", "speaking_level": "Fluent", "reading_level": "Fluent", "writing_level": "Fluent"}},
        {{"language": "Tamil", "speaking_level": "Fluent", "reading_level": "Moderate", "writing_level": "Moderate"}}
    ],
    "technical_skills": ["FastAPI", "React", "Docker", "MongoDB"],
    "soft_skills": ["Communication", "Problem Solving"],
    "experience": [
        {{
            "company": "Company Name",
            "role": "Role Title",
            "start_date": "YYYY-MM",
            "end_date": "YYYY-MM",
            "is_current": false,
            "duration_months": 24,
            "description": "Role summary",
            "responsibilities": ["Responsibility 1"],
            "skills_used": ["Python", "FastAPI"],
            "achievements": ["Achievement 1"]
        }}
    ],
    "projects": [
        {{
            "name": "Project Name",
            "description": "Project details",
            "technologies": ["FastAPI", "MongoDB"],
            "github_url": "https://github.com/...",
            "achievements": ["Built REST API"]
        }}
    ],
    "education": [
        {{
            "qualification": "B.Sc in Computer Science",
            "institution": "University Name",
            "field": "Computer Science",
            "start_year": 2018,
            "end_year": 2022,
            "grade": "First Class"
        }}
    ],
    "certifications": [
        {{
            "name": "AWS Certified Developer",
            "issuer": "Amazon Web Services",
            "issue_date": "2023",
            "credential_url": "https://..."
        }}
    ],
    "social_links": {{
        "linkedin_url": "https://linkedin.com/in/...",
        "github_url": "https://github.com/...",
        "portfolio_url": "https://..."
    }}
}}

CV TEXT:
{cv_text[:30000]}
"""

        extracted = {}
        if self.api_key:
            try:
                extracted = await asyncio.to_thread(generate_gemini_json, self.api_key, self.model_name, prompt)
            except Exception:
                extracted = {}

        # Fallback / normalization for programming vs human languages
        prog_langs = extracted.get("programming_languages") or []
        human_langs = extracted.get("human_languages") or []
        tech_skills = extracted.get("technical_skills") or []
        soft_skills = extracted.get("soft_skills") or []

        # Auto-separate programming languages if mixed into technical skills
        cleaned_tech = []
        for s in tech_skills:
            if str(s).lower() in COMMON_PROGRAMMING_LANGUAGES and s not in prog_langs:
                prog_langs.append(s)
            else:
                cleaned_tech.append(s)

        # Detect GitHub URL in extraction or CV text
        github_url = (extracted.get("social_links") or {}).get("github_url")
        if not github_url:
            import re
            gh_match = re.search(r"https?://(?:www\.)?github\.com/([A-Za-z0-9_.-]+)", cv_text, re.I)
            if gh_match:
                github_url = gh_match.group(0)

        github_data = None
        if github_url:
            try:
                github_data = await self.github_service.verify_and_store_github(
                    user_id,
                    github_url,
                    cv_skills=prog_langs + cleaned_tech
                )
            except Exception:
                github_data = None

        candidate_data = {
            "id": user_id,
            "user_id": user_id,
            "personal_info": extracted.get("personal_info") or {},
            "professional_summary": extracted.get("professional_summary") or "",
            "programming_languages": prog_langs,
            "human_languages": human_langs,
            "technical_skills": cleaned_tech,
            "soft_skills": soft_skills,
            "experience": extracted.get("experience") or [],
            "projects": extracted.get("projects") or [],
            "education": extracted.get("education") or [],
            "certifications": extracted.get("certifications") or [],
            "social_links": extracted.get("social_links") or {},
        }

        # Calculate Candidate Profile Score (out of 100) deterministically
        profile_score_res = self.scoring_service.calculate_candidate_profile_score(candidate_data, github_data)
        candidate_data["profile_score"] = profile_score_res["overall_score"]
        candidate_data["score_breakdown"] = profile_score_res["score_breakdown"]

        # Update candidate profile in MongoDB without creating duplicate candidates
        saved_profile = self.candidate_repo.save_or_update_profile(user_id, candidate_data)

        # Record immutable analysis_run entry in MongoDB for audit history
        run_id = f"run_{user_id}_{int(utcnow().timestamp())}"
        analysis_run_doc = {
            "id": run_id,
            "candidate_id": user_id,
            "job_id": None,
            "cv_document_id": doc_id,
            "document_version": 1,
            "extracted_data_snapshot": candidate_data,
            "verification_results": {
                "github_verified": bool(github_data),
                "github_url": github_url,
            },
            "scoring_rules_version": "2.5",
            "model_version": self.model_name,
            "candidate_profile_score": profile_score_res["overall_score"],
            "individual_score_components": profile_score_res["score_breakdown"],
            "evidence": {
                "programming_languages": prog_langs,
                "human_languages": human_langs,
                "github": (github_data or {}).get("detected_skills", [])
            },
            "analysis_timestamp": utcnow(),
        }
        self.analysis_repo.record_analysis_run(analysis_run_doc)

        return {
            "candidate": saved_profile,
            "candidate_profile_score": profile_score_res["overall_score"],
            "score_breakdown": profile_score_res["score_breakdown"],
            "github_verification": github_data,
            "analysis_run_id": run_id,
        }
