"""Candidate Management and Profile Intelligence Service."""

from typing import Any, Dict, List, Optional
from repositories.candidate_repository import CandidateRepository
from repositories.analysis_repository import AnalysisRepository
from repositories.github_repository import GithubRepository
from services.scoring_service import ScoringService
from services.job_match_service import JobMatchService


class CandidateService:
    def __init__(
        self,
        candidate_repo: CandidateRepository,
        analysis_repo: AnalysisRepository,
        github_repo: GithubRepository
    ):
        self.candidate_repo = candidate_repo
        self.analysis_repo = analysis_repo
        self.github_repo = github_repo
        self.scoring_service = ScoringService()

    def get_complete_candidate_profile(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        profile = self.candidate_repo.find_by_user_id(candidate_id)
        if not profile:
            return None

        # Fetch associated entities
        skills = self.candidate_repo.get_candidate_skills(candidate_id)
        exp = self.candidate_repo.get_candidate_experience(candidate_id)
        edu = self.candidate_repo.get_candidate_education(candidate_id)
        projs = self.candidate_repo.get_candidate_projects(candidate_id)
        certs = self.candidate_repo.get_candidate_certifications(candidate_id)
        langs = self.candidate_repo.get_candidate_languages(candidate_id)
        github = self.github_repo.get_latest_github_profile(candidate_id)

        # Re-calculate or attach Candidate Profile Score
        profile_score = self.scoring_service.calculate_candidate_profile_score(profile, github)

        # Separate programming vs human languages
        prog_langs = profile.get("programming_languages") or [l.get("language") for l in langs if l.get("kind") == "programming"] or []
        human_langs = profile.get("human_languages") or [l for l in langs if l.get("kind") != "programming"] or []

        result = {
            **profile,
            "skills": skills,
            "experience": exp,
            "education": edu,
            "projects": projs,
            "certifications": certs,
            "programming_languages": prog_langs,
            "human_languages": human_langs,
            "github_profile": github,
            "candidate_profile_score": profile_score["overall_score"],
            "score_breakdown": profile_score["score_breakdown"],
        }
        return result

    def get_candidate_analysis_history(self, candidate_id: str) -> List[Dict[str, Any]]:
        return self.analysis_repo.get_candidate_analysis_history(candidate_id)
